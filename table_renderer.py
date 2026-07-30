from tabulate import tabulate

from schemas import ETFComparisonResponse


def render_comparison(result: ETFComparisonResponse) -> str:
    """Render structured backend output for CLI testing only."""

    headers = [
        "Ticker",
        "ETF Name",
        "Expense Ratio",
        "Fund Size",
        "Performance",
        "Top Holdings",
        "Concentration",
        "Main Risk",
        "Simple Explanation",
        "Analyst Summary",
    ]
    rows = [
        [
            row.ticker,
            row.name,
            row.expense_ratio,
            row.fund_size,
            row.performance,
            ", ".join(row.top_holdings) or "Not available",
            row.holdings_concentration,
            row.main_risk,
            row.simple_explanation,
            row.analyst_summary or "Not requested",
        ]
        for row in result.compared_etfs
    ]

    parts = [
        tabulate(rows, headers=headers, tablefmt="github") if rows else "No ETF rows available.",
        "",
        "### Similarities",
        *[f"- {item}" for item in result.similarities],
        "",
        "### Differences",
        *[f"- {item}" for item in result.differences],
        "",
        "### Beginner takeaway",
        result.beginner_takeaway,
        "",
        f"### Analyst research included: {'Yes' if result.research_included else 'No'}",
        "",
        "### Data notes",
        *[f"- {item}" for item in result.data_notes],
        "",
        "### Suggested follow-ups",
        *[f"- {item}" for item in result.follow_up_suggestions],
    ]
    return "\n".join(parts)