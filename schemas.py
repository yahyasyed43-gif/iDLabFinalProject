from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class RequestUnderstanding(BaseModel):
    """Used only when a first message does not contain obvious tickers."""

    tickers: list[str] = Field(default_factory=list)
    include_research: bool = False


class ETFComparisonRow(BaseModel):
    ticker: str
    name: str = "Not available"
    expense_ratio: str = "Not available"
    fund_size: str = "Not available"
    performance: str = "Not available"
    top_holdings: list[str] = Field(default_factory=list)
    holdings_concentration: str = "Not available"
    main_risk: str = "Not available"
    simple_explanation: str = "Not available"
    analyst_summary: str | None = None


class ETFComparisonResponse(BaseModel):
    compared_etfs: list[ETFComparisonRow]
    similarities: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    beginner_takeaway: str
    research_included: bool = False
    data_notes: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)


class ChatTurnResponse(BaseModel):
    """A turn is either a full comparison or a natural chat reply."""

    response_type: Literal["comparison", "message"]
    comparison: ETFComparisonResponse | None = None
    message: str | None = None


class ETFGraphState(TypedDict, total=False):
    message: str
    frontend_include_research: bool
    tickers: list[str]
    include_research: bool
    is_follow_up: bool
    collected_data: dict[str, Any]
    last_comparison: dict[str, Any]
    response: dict[str, Any]
    error: str