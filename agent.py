from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Sequence 
from typing import Any

from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from config import Settings, get_settings
from morningstar_tools import (
    collect_morningstar_data,
    create_mcp_client,
    load_tools,
)
from schemas import (
    ChatTurnResponse,
    ETFComparisonResponse,
    ETFGraphState,
    RequestUnderstanding,
)

_TICKER = re.compile(r"\b[A-Z][A-Z0-9.-]{1,5}\b")
_COMMON_WORDS = {"ADD", "AND", "ETF", "ETFS", "HOW", "NOW", "THE", "WHAT", "WHICH"}

COMPARISON_PROMPT = """Build the requested ETFComparisonResponse using only the supplied
Morningstar data. Never invent values. Use 'Not available' when data is missing. Keep it
beginner-friendly and return structured data rather than Markdown.
"""

FOLLOW_UP_PROMPT = """Answer the user's follow-up using only the saved ETF comparison.
Answer naturally instead of repeating the full table. Follow requested formatting exactly;
for example, if the user asks for four lines, return exactly four short lines.
"""


def create_model(settings: Settings) -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_deployment=settings.azure_deployment,
        azure_endpoint=settings.azure_endpoint,
        api_key=settings.azure_key,
        api_version=settings.azure_api_version,
        timeout=120,
        max_retries=2,
    )


def _find_tickers(message: str) -> list[str]:
    """Fast path for familiar uppercase ticker symbols."""

    return list(
        dict.fromkeys(
            word for word in _TICKER.findall(message) if word not in _COMMON_WORDS
        )
    )


def _wants_research(message: str) -> bool:
    lowered = message.lower()
    return "research" in lowered or "analyst" in lowered


def _message_text(model_reply: Any) -> str:
    content = getattr(model_reply, "content", model_reply)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        ).strip()
    return str(content)


def friendly_error_message(error: BaseException) -> str:
    """Reveal useful causes hidden inside asyncio ExceptionGroup wrappers."""

    def leaf_messages(item: BaseException) -> list[str]:
        nested = getattr(item, "exceptions", None)
        if nested:
            return [message for child in nested for message in leaf_messages(child)]
        return [f"{type(item).__name__}: {item}"]

    messages = list(dict.fromkeys(leaf_messages(error)))
    combined = " | ".join(messages)
    lowered = combined.lower()
    if "401" in combined or "unauthorized" in lowered:
        return "Morningstar authentication failed. Refresh the access token in .env."
    if "rate limit" in lowered:
        return "Morningstar is temporarily rate limited. Wait a moment and try again."
    if "connecterror" in lowered or "connection attempts failed" in lowered:
        return "Could not connect to Morningstar MCP. Check your network and MCP URL, then try again."
    return combined


def build_graph(
    settings: Settings,
    tools: Sequence[BaseTool],
    *,
    model: Any | None = None,
    checkpointer: Any | None = None,
):
    """Build a small graph with comparison and conversational paths."""

    chat_model = model or create_model(settings)
    parse_request = chat_model.with_structured_output(RequestUnderstanding)
    build_comparison = chat_model.with_structured_output(ETFComparisonResponse)

    async def understand_request(state: ETFGraphState) -> dict[str, Any]:
        message = state.get("message", "").strip()
        previous_tickers = state.get("tickers", [])
        tickers = _find_tickers(message)
        include_research = bool(
            state.get("frontend_include_research") or _wants_research(message)
        )

        # No new tickers means this is a question about the saved comparison.
        if not tickers and previous_tickers:
            return {
                "tickers": previous_tickers,
                "include_research": include_research,
                "is_follow_up": not include_research,
                "error": "",
            }

        # Use the model only for natural fund names in a new conversation.
        if not 2 <= len(tickers) <= 3:
            parsed = await parse_request.ainvoke(
                [
                    ("system", "Extract two or three ETF tickers. Do not invent them."),
                    ("user", message),
                ]
            )
            tickers = [ticker.upper() for ticker in parsed.tickers]
            include_research = include_research or parsed.include_research

        error = "" if 2 <= len(tickers) <= 3 else "Please provide two or three ETF tickers."
        return {
            "tickers": tickers,
            "include_research": include_research,
            "is_follow_up": False,
            "error": error,
        }

    def choose_path(state: ETFGraphState) -> str:
        if state.get("error") or state.get("is_follow_up"):
            return "answer_follow_up"
        return "collect_data"

    async def collect_data(state: ETFGraphState) -> dict[str, Any]:
        try:
            data = await collect_morningstar_data(
                tools, state["tickers"], state.get("include_research", False)
            )
            return {"collected_data": data, "error": ""}
        except Exception as error:
            return {"error": friendly_error_message(error)}

    async def create_comparison(state: ETFGraphState) -> dict[str, Any]:
        if state.get("error"):
            response = ChatTurnResponse(
                response_type="message", message=state["error"]
            )
            return {"response": response.model_dump()}

        comparison = await build_comparison.ainvoke(
            [
                ("system", COMPARISON_PROMPT),
                (
                    "user",
                    json.dumps(
                        {
                            "question": state["message"],
                            **state["collected_data"],
                        },
                        default=str,
                    )[:60000],
                ),
            ]
        )
        response = ChatTurnResponse(
            response_type="comparison", comparison=comparison
        )
        return {
            "last_comparison": comparison.model_dump(),
            "response": response.model_dump(),
        }

    async def answer_follow_up(state: ETFGraphState) -> dict[str, Any]:
        if state.get("error"):
            text = state["error"]
        elif not state.get("last_comparison"):
            text = "Start by asking me to compare two or three ETFs."
        else:
            reply = await chat_model.ainvoke(
                [
                    ("system", FOLLOW_UP_PROMPT),
                    (
                        "user",
                        f"Saved comparison:\n{json.dumps(state['last_comparison'])}\n\n"
                        f"Follow-up question:\n{state['message']}",
                    ),
                ]
            )
            text = _message_text(reply)
        response = ChatTurnResponse(response_type="message", message=text)
        return {"response": response.model_dump()}

    workflow = StateGraph(ETFGraphState)
    workflow.add_node("understand_request", understand_request)
    workflow.add_node("collect_data", collect_data)
    workflow.add_node("create_comparison", create_comparison)
    workflow.add_node("answer_follow_up", answer_follow_up)
    workflow.add_edge(START, "understand_request")
    workflow.add_conditional_edges("understand_request", choose_path)
    workflow.add_edge("collect_data", "create_comparison")
    workflow.add_edge("create_comparison", END)
    workflow.add_edge("answer_follow_up", END)
    return workflow.compile(checkpointer=checkpointer or InMemorySaver())


_chat_graph: Any | None = None


async def initialize_chat_backend() -> Any:
    global _chat_graph
    if _chat_graph is None:
        settings = get_settings()
        for attempt in range(2):
            try:
                tools = await load_tools(create_mcp_client(settings))
                _chat_graph = build_graph(settings, tools)
                break
            except BaseException as error:
                if attempt == 1:
                    raise RuntimeError(friendly_error_message(error)) from error
                await asyncio.sleep(1)
    return _chat_graph


async def run_chat_turn(
    message: str,
    thread_id: str,
    include_research: bool = False,
) -> ChatTurnResponse:
    graph = await initialize_chat_backend()
    result = await graph.ainvoke(
        {"message": message, "frontend_include_research": include_research},
        config={"configurable": {"thread_id": thread_id}},
    )
    return ChatTurnResponse.model_validate(result["response"])