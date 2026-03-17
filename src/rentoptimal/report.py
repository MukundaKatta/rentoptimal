"""Rich terminal reports for RentOptimal."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from rentoptimal.models import MarketData, PricingRecommendation


def render_pricing_recommendation(
    rec: PricingRecommendation, console: Console | None = None
) -> None:
    """Print a rich pricing recommendation to the terminal."""
    console = console or Console()
    prop = rec.property

    # Header
    console.print(
        Panel(
            f"[bold]{prop.address}[/bold]\n"
            f"{prop.city}, {prop.state} {prop.zip_code}\n"
            f"{prop.bedrooms} bed / {prop.bathrooms} bath | "
            f"{prop.sqft:,.0f} sqft | {prop.condition.value}",
            title="Property Summary",
            border_style="blue",
        )
    )

    # Pricing table
    table = Table(title="Pricing Analysis", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Predicted Market Rent", f"${rec.predicted_market_rent:,.2f}/mo")
    table.add_row(
        "Optimal Asking Rent",
        Text(f"${rec.optimal_rent:,.2f}/mo", style="bold green"),
    )
    table.add_row("Expected Occupancy", f"{rec.expected_occupancy * 100:.1f}%")
    table.add_row(
        "Expected Monthly Revenue",
        Text(f"${rec.expected_monthly_revenue:,.2f}", style="bold yellow"),
    )
    table.add_row("Confidence", f"{rec.confidence * 100:.0f}%")

    if rec.comparable_rents:
        comp_range = f"${min(rec.comparable_rents):,.0f} - ${max(rec.comparable_rents):,.0f}"
        table.add_row("Comparable Rent Range", comp_range)
        table.add_row("Comparables Found", str(len(rec.comparable_rents)))

    console.print(table)

    # Reasoning
    if rec.reasoning:
        console.print(Panel(rec.reasoning, title="Reasoning", border_style="dim"))


def render_market_report(
    market: MarketData, console: Console | None = None
) -> None:
    """Print a rich market report to the terminal."""
    console = console or Console()

    table = Table(
        title=f"Market Report: {market.city}",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Median Rent", f"${market.median_rent:,.2f}/mo")
    table.add_row("Mean Rent", f"${market.mean_rent:,.2f}/mo")
    table.add_row("Median $/sqft", f"${market.median_price_per_sqft:,.2f}")
    table.add_row("Vacancy Rate", f"{market.vacancy_rate * 100:.1f}%")
    table.add_row("Total Listings", str(market.total_listings))
    table.add_row("Avg Days on Market", f"{market.avg_days_on_market:.0f}")

    trend_style = "green" if market.rent_trend_pct >= 0 else "red"
    trend_text = Text(
        f"{market.rent_trend_pct * 100:+.1f}% YoY", style=trend_style
    )
    table.add_row("Rent Trend", trend_text)

    table.add_row(
        "Sample Period",
        f"{market.sample_period_start} to {market.sample_period_end}",
    )

    console.print(table)


def render_benchmarks_table(
    ranked: list[tuple[str, float]],
    city: str,
    console: Console | None = None,
) -> None:
    """Print neighborhood benchmark rankings."""
    console = console or Console()
    table = Table(
        title=f"Neighborhood Benchmarks: {city}",
        show_header=True,
        header_style="bold green",
    )
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Neighborhood", style="bold")
    table.add_column("Median $/sqft", justify="right")

    for i, (nbhd, ppsf) in enumerate(ranked, 1):
        table.add_row(str(i), nbhd, f"${ppsf:.2f}")

    console.print(table)
