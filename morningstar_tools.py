from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp.shared.exceptions import McpError

from config import Settings

CORE_DATAPOINTS = ["expense ratio", "total return", "fund size"]
ALLOWED_TOOLS = {
    "morningstar-id-lookup-tool",
    "morningstar-data-tool",
    "morningstar-fund-holdings-tool",
    "morningstar-analyst-research-tool",
}


def create_mcp_client(settings: Settings) -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "morningstar": {
                "transport": "http",
                "url": settings.morningstar_url,
                "headers": {"Authorization": f"Bearer {settings.morningstar_token}"},
            }
        }
    )


async def load_tools(client: MultiServerMCPClient) -> list[BaseTool]:
    tools = [
        tool for tool in await client.get_tools() if tool.name in ALLOWED_TOOLS
    ]
    missing = ALLOWED_TOOLS - {tool.name for tool in tools}
    if missing:
        raise RuntimeError(f"Missing Morningstar tools: {', '.join(sorted(missing))}")
    return tools


def get_tool(tools: Sequence[BaseTool], name: str) -> BaseTool:
    return next((tool for tool in tools if tool.name == name), None) or _missing_tool(name)


def _missing_tool(name: str):
    raise RuntimeError(f"Morningstar tool is unavailable: {name}")


def _plain(value: Any) -> Any:
    """Turn MCP content blocks and JSON strings into ordinary Python data."""

    if isinstance(value, str):
        try:
            return _plain(json.loads(value))
        except json.JSONDecodeError:
            return value
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_plain(item) for item in value]
    if hasattr(value, "model_dump"):
        return _plain(value.model_dump())
    if hasattr(value, "content"):
        return _plain(value.content)
    return value


def _container(value: Any, wanted_name: str) -> Any | None:
    """Find a named section such as investments or datapoints."""

    if isinstance(value, dict):
        for name, child in value.items():
            if name.lower() == wanted_name:
                return child
        for child in value.values():
            found = _container(child, wanted_name)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _container(child, wanted_name)
            if found is not None:
                return found
    return None


def _pick_etfs(lookup_result: Any, tickers: list[str]) -> list[dict[str, str]]:
    investments = _container(_plain(lookup_result), "investments")
    if not isinstance(investments, dict):
        raise ValueError("Morningstar returned an unexpected investment lookup response.")

    selected_etfs = []
    for ticker in tickers:
        matches = next(
            (value for key, value in investments.items() if key.upper() == ticker.upper()),
            [],
        )
        exact_etfs = [
            item
            for item in matches
            if item.get("ticker_symbol", "").upper() == ticker.upper()
            and item.get("investment_type") == "FE"
        ]
        if not exact_etfs:
            raise ValueError(f"Morningstar could not find {ticker} as an ETF.")
        match = exact_etfs[0]
        selected_etfs.append(
            {
                "ticker": ticker.upper(),
                "name": match.get("investment_name", "Not available"),
                "investment_id": match["morningstar_id"],
            }
        )
    return selected_etfs


def _pick_datapoint_ids(lookup_result: Any) -> list[str]:
    datapoints = _container(_plain(lookup_result), "datapoints")
    if not isinstance(datapoints, dict):
        raise ValueError("Morningstar did not return datapoint IDs.")

    ids = []
    for name in CORE_DATAPOINTS:
        choices = datapoints.get(name, [])
        if not choices or not choices[0].get("morningstar_id"):
            raise ValueError(f"Morningstar did not find the '{name}' datapoint.")
        ids.append(choices[0]["morningstar_id"])
    return ids


async def _call(tool: BaseTool, arguments: dict[str, Any]) -> Any:
    """Retry only the temporary rate-limit failure seen from Morningstar."""

    for attempt in range(4):
        try:
            return _plain(await tool.ainvoke(arguments))
        except McpError as error:
            if "rate limit" not in str(error).lower() or attempt == 3:
                raise
            await asyncio.sleep(1.1 * (2**attempt))


async def collect_morningstar_data(
    tools: Sequence[BaseTool],
    tickers: list[str],
    include_research: bool,
) -> dict[str, Any]:
    """Run the small fixed Morningstar workflow used by the graph."""

    lookup = await _call(
        get_tool(tools, "morningstar-id-lookup-tool"),
        {"investment_identifiers": tickers, "datapoints": CORE_DATAPOINTS},
    )
    etfs = _pick_etfs(lookup, tickers)
    investment_ids = [etf["investment_id"] for etf in etfs]
    datapoint_ids = _pick_datapoint_ids(lookup)

    data, holdings = await asyncio.gather(
        _call(
            get_tool(tools, "morningstar-data-tool"),
            {"investment_ids": investment_ids, "datapoint_ids": datapoint_ids},
        ),
        _call(
            get_tool(tools, "morningstar-fund-holdings-tool"),
            {"investment_ids": investment_ids, "num_holdings": 10},
        ),
    )

    research = {}
    if include_research:
        results = await asyncio.gather(
            *[
                _call(
                    get_tool(tools, "morningstar-analyst-research-tool"),
                    {"investment_id": etf["investment_id"]},
                )
                for etf in etfs
            ]
        )
        research = {
            etf["ticker"]: result
            for etf, result in zip(etfs, results, strict=True)
        }

    return {
        "etfs": etfs,
        "data": data,
        "holdings": holdings,
        "research": research,
        "research_included": include_research,
    }