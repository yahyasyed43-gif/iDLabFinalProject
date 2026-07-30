import asyncio
import json
import unittest
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import ValidationError

from agent import build_graph, friendly_error_message
from table_renderer import comparison_table_rows
from schemas import (
    ChatTurnResponse,
    ETFComparisonResponse,
    ETFComparisonRow,
    RequestUnderstanding,
)


@dataclass
class DummySettings:
    azure_deployment: str = "test"
    azure_endpoint: str = "https://example.test"
    azure_key: str = "test"
    azure_api_version: str = "test"


class FakeStructuredRunner:
    def __init__(self, schema: type) -> None:
        self.schema = schema

    async def ainvoke(self, messages: Any):
        if self.schema is RequestUnderstanding:
            return RequestUnderstanding()
        payload = json.loads(messages[-1][1])
        research = payload["research_included"]
        return ETFComparisonResponse(
            compared_etfs=[
                ETFComparisonRow(
                    ticker=etf["ticker"],
                    name=etf["name"],
                    top_holdings=["Example Holding"],
                    simple_explanation="Mock row",
                    analyst_summary="Mock research" if research else None,
                )
                for etf in payload["etfs"]
            ],
            beginner_takeaway="Mock takeaway",
            research_included=research,
        )


class FakeModel:
    def with_structured_output(self, schema: type) -> FakeStructuredRunner:
        return FakeStructuredRunner(schema)

    async def ainvoke(self, messages: Any):
        return SimpleNamespace(content="Line 1\nLine 2\nLine 3\nLine 4")


def make_tools(*, invalid_ticker: str | None = None):
    calls = {"lookup": [], "data": [], "holdings": [], "research": [], "active": 0, "max_active": 0}

    async def lookup(investment_identifiers: list[str], datapoints: list[str]) -> dict:
        calls["lookup"].append(investment_identifiers)
        return {
            "investments": {
                ticker: [{
                    "ticker_symbol": ticker,
                    "investment_name": f"{ticker} Fund",
                    "morningstar_id": f"ID-{ticker}",
                    "investment_type": "ST" if ticker == invalid_ticker else "FE",
                }]
                for ticker in investment_identifiers
            },
            "datapoints": {
                "expense ratio": [{"morningstar_id": "OS05P"}],
                "total return": [{"morningstar_id": "PM00C"}],
                "fund size": [{"morningstar_id": "OF009"}],
            },
        }

    async def data(investment_ids: list[str], datapoint_ids: list[str]) -> dict:
        calls["data"].append(investment_ids)
        calls["active"] += 1
        calls["max_active"] = max(calls["max_active"], calls["active"])
        await asyncio.sleep(0.03)
        calls["active"] -= 1
        return {"values": "mock"}

    async def holdings(investment_ids: list[str], num_holdings: int) -> dict:
        calls["holdings"].append(investment_ids)
        calls["active"] += 1
        calls["max_active"] = max(calls["max_active"], calls["active"])
        await asyncio.sleep(0.03)
        calls["active"] -= 1
        return {"holdings": "mock"}

    async def research(investment_id: str) -> dict:
        calls["research"].append(investment_id)
        return {"summary": "mock"}

    tools = [
        StructuredTool.from_function(coroutine=lookup, name="morningstar-id-lookup-tool", description="lookup"),
        StructuredTool.from_function(coroutine=data, name="morningstar-data-tool", description="data"),
        StructuredTool.from_function(coroutine=holdings, name="morningstar-fund-holdings-tool", description="holdings"),
        StructuredTool.from_function(coroutine=research, name="morningstar-analyst-research-tool", description="research"),
    ]
    return tools, calls


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    def make_graph(self, **options):
        tools, calls = make_tools(**options)
        graph = build_graph(
            DummySettings(), tools, model=FakeModel(), checkpointer=InMemorySaver()
        )
        return graph, calls

    async def turn(self, graph, message: str, thread: str, research: bool = False):
        result = await graph.ainvoke(
            {"message": message, "frontend_include_research": research},
            config={"configurable": {"thread_id": thread}},
        )
        return ChatTurnResponse.model_validate(result["response"])

    async def test_new_comparison_returns_structured_response(self):
        graph, calls = self.make_graph()
        response = await self.turn(graph, "Compare VOO and QQQ", "one")
        self.assertEqual(response.response_type, "comparison")
        self.assertEqual([row.ticker for row in response.comparison.compared_etfs], ["VOO", "QQQ"])
        self.assertEqual(len(calls["lookup"]), 1)

    async def test_follow_up_returns_four_lines_without_new_tool_calls(self):
        graph, calls = self.make_graph()
        await self.turn(graph, "Compare VOO and QQQ", "same")
        response = await self.turn(graph, "Summarize it in 4 lines", "same")
        self.assertEqual(response.response_type, "message")
        self.assertEqual(len(response.message.splitlines()), 4)
        self.assertEqual(len(calls["lookup"]), 1)

    async def test_different_thread_has_no_context(self):
        graph, _ = self.make_graph()
        await self.turn(graph, "Compare VOO and QQQ", "first")
        response = await self.turn(graph, "Summarize it", "second")
        self.assertEqual(response.response_type, "message")
        self.assertIn("two or three", response.message)

    async def test_research_is_optional(self):
        graph, calls = self.make_graph()
        response = await self.turn(graph, "Compare VOO and QQQ", "no-research")
        self.assertFalse(response.comparison.research_included)
        self.assertEqual(calls["research"], [])

    async def test_toggle_enables_research(self):
        graph, calls = self.make_graph()
        response = await self.turn(graph, "Compare VOO and QQQ", "research", True)
        self.assertTrue(response.comparison.research_included)
        self.assertCountEqual(calls["research"], ["ID-VOO", "ID-QQQ"])

    async def test_follow_up_can_add_research(self):
        graph, calls = self.make_graph()
        await self.turn(graph, "Compare VOO and QQQ", "add-research")
        response = await self.turn(graph, "Now add analyst research", "add-research")
        self.assertEqual(response.response_type, "comparison")
        self.assertTrue(response.comparison.research_included)
        self.assertEqual(len(calls["research"]), 2)

    async def test_invalid_identifier_returns_message(self):
        graph, calls = self.make_graph(invalid_ticker="AAPL")
        response = await self.turn(graph, "Compare AAPL and QQQ", "invalid")
        self.assertEqual(response.response_type, "message")
        self.assertIn("could not find AAPL as an ETF", response.message)
        self.assertEqual(calls["data"], [])

    async def test_data_and_holdings_are_concurrent(self):
        graph, calls = self.make_graph()
        await self.turn(graph, "Compare VOO and QQQ", "concurrent")
        self.assertEqual(calls["max_active"], 2)

    def test_ui_table_has_one_row_per_etf(self):
        for ticker_count in (2, 3):
            comparison = ETFComparisonResponse(
                compared_etfs=[
                    ETFComparisonRow(ticker=f"ETF{index}")
                    for index in range(ticker_count)
                ],
                beginner_takeaway="Test",
            )
            rows = comparison_table_rows(comparison)
            self.assertEqual(len(rows), ticker_count)
            self.assertEqual(rows[0]["Ticker"], "ETF0")
            self.assertIn("Top-10 concentration", rows[0])
    def test_nested_taskgroup_error_shows_root_cause(self):
        error = ExceptionGroup(
            "unhandled errors in a TaskGroup",
            [ConnectionError("All connection attempts failed")],
        )
        message = friendly_error_message(error)
        self.assertNotIn("TaskGroup", message)
        self.assertIn("Could not connect to Morningstar MCP", message)
    def test_structured_response_validation(self):
        with self.assertRaises(ValidationError):
            ETFComparisonResponse(compared_etfs=[], beginner_takeaway=123)


if __name__ == "__main__":
    unittest.main()