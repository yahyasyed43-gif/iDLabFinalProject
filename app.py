from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import streamlit as st

from agent import friendly_error_message, run_chat_turn
from schemas import ChatTurnResponse, ETFComparisonResponse
from table_renderer import comparison_table_rows

APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "logo.png"


def render_bullets(title: str, items: list[str]) -> None:
    st.markdown(f"#### {title}")
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption("Not available")


def render_comparison(comparison: ETFComparisonResponse) -> None:
    """Render structured comparison data without turning it into Markdown."""

    st.markdown("### ETF comparison")
    rows = comparison_table_rows(comparison)
    if rows:
        st.dataframe(
            rows,
            hide_index=True,
            width="stretch",
            height=38 + (35 * len(rows)),
        )
    else:
        st.warning("No ETF rows were returned.")

    st.markdown("#### Holdings and explanations")
    for etf in comparison.compared_etfs:
        with st.expander(f"{etf.ticker} — {etf.name}"):
            st.markdown(f"**Simple explanation:** {etf.simple_explanation}")
            st.markdown("**Top holdings**")
            if etf.top_holdings:
                st.dataframe(
                    [{"Holding": holding} for holding in etf.top_holdings],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.caption("Not available")

            if comparison.research_included:
                st.markdown("**Morningstar analyst summary**")
                st.write(etf.analyst_summary or "Not available")

    left, right = st.columns(2)
    with left:
        render_bullets("Similarities", comparison.similarities)
    with right:
        render_bullets("Differences", comparison.differences)

    st.info(comparison.beginner_takeaway, icon="💡")
    render_bullets("Data notes", comparison.data_notes)
    render_bullets("Try asking", comparison.follow_up_suggestions)


def render_assistant_response(response: ChatTurnResponse) -> None:
    if response.response_type == "comparison" and response.comparison:
        render_comparison(response.comparison)
    else:
        st.markdown(response.message or "No response was returned.")


def ask_backend(prompt: str) -> ChatTurnResponse:
    return asyncio.run(
        run_chat_turn(
            message=prompt,
            thread_id=st.session_state.thread_id,
            include_research=st.session_state.include_research,
        )
    )


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid4())


st.set_page_config(page_title="ETF Engine", page_icon="🤖", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #ffffff; }
    section[data-testid="stSidebar"] { background: #1c866a; }
    section[data-testid="stSidebar"] * { color: white; }
    div[data-testid="stChatInput"] {
        border: 2px solid #50d6a3;
        border-radius: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())
if "include_research" not in st.session_state:
    st.session_state.include_research = False

title, logo = st.columns([0.85, 0.15])
with title:
    st.title("ETF Engine")
    st.caption("Compare two or three ETFs, then ask follow-up questions.")
with logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=100)

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=70)
    st.header("Financial Assistant")
    st.write("Morningstar-powered ETF comparisons with conversational follow-ups.")
    st.checkbox(
        "Include Morningstar analyst research",
        key="include_research",
        help="Research takes longer and is requested only when enabled.",
    )
    st.button(
        "Start a new conversation",
        on_click=reset_conversation,
        width="stretch",
    )
    st.caption(f"Thread: {st.session_state.thread_id[:8]}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        elif "response" in message:
            render_assistant_response(ChatTurnResponse.model_validate(message["response"]))
        else:
            st.write(message.get("content", ""))

st.markdown("#### Try an example")
example_columns = st.columns(3)
example_prompts = [
    "Compare VOO and QQQ",
    "Compare VOO, QQQ, and SCHD",
    "Summarize the comparison in 4 lines",
]
selected_prompt = None
for column, example in zip(example_columns, example_prompts, strict=True):
    with column:
        if st.button(example, width="stretch"):
            selected_prompt = example

typed_prompt = st.chat_input("Compare two or three ETFs...")
prompt = typed_prompt or selected_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Researching Morningstar data..."):
                response = ask_backend(prompt)
            render_assistant_response(response)
            st.session_state.messages.append(
                {"role": "assistant", "response": response.model_dump(mode="json")}
            )
        except Exception as error:
            error_message = f"Unable to complete the request: {friendly_error_message(error)}"
            st.error(error_message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "response": ChatTurnResponse(
                        response_type="message", message=error_message
                    ).model_dump(mode="json"),
                }
            )