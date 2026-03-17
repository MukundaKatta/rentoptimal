"""Command-line interface for RentOptimal."""

from __future__ import annotations

import click
from rich.console import Console

from rentoptimal.models import Property, PropertyCondition
from rentoptimal.simulator import generate_listings, generate_market_data, CITIES
from rentoptimal.pricing.model import RentPredictor
from rentoptimal.pricing.comparables import CompAnalyzer
from rentoptimal.pricing.optimizer import PriceOptimizer
from rentoptimal.market.analyzer import MarketAnalyzer
from rentoptimal.market.benchmarks import MarketBenchmarks
from rentoptimal.market.demand import DemandPredictor
from rentoptimal.report import (
    render_pricing_recommendation,
    render_market_report,
    render_benchmarks_table,
)

console = Console()


@click.group()
def main() -> None:
    """RentOptimal -- Rental Price Optimizer."""


@main.command()
@click.option("--city", required=True, help="City for pricing analysis")
@click.option("--bedrooms", type=int, default=2, help="Number of bedrooms")
@click.option("--sqft", type=float, default=900, help="Square footage")
@click.option("--condition", type=click.Choice(["excellent", "good", "fair", "poor"]), default="good")
@click.option("--n-listings", type=int, default=300, help="Simulated listings for training")
def analyze(city: str, bedrooms: int, sqft: float, condition: str, n_listings: int) -> None:
    """Analyze optimal rent for a property."""
    if city not in CITIES:
        console.print(f"[red]Unknown city: {city}. Available: {', '.join(CITIES)}[/red]")
        return

    console.print("[dim]Generating market data...[/dim]")
    listings = generate_listings(n=n_listings)

    console.print("[dim]Training pricing model...[/dim]")
    predictor = RentPredictor()
    predictor.fit(listings)

    comp_analyzer = CompAnalyzer(listings)
    optimizer = PriceOptimizer(predictor, comp_analyzer)

    info = CITIES[city]
    prop = Property(
        address="123 Main St",
        city=city,
        state=info["state"],
        zip_code="00000",
        sqft=sqft,
        bedrooms=bedrooms,
        bathrooms=max(1.0, bedrooms * 0.5 + 0.5),
        condition=PropertyCondition(condition),
    )

    market_data = generate_market_data(city, listings)
    rec = optimizer.recommend(prop, market_data=market_data)
    render_pricing_recommendation(rec, console)


@main.command()
@click.option("--city", required=True, help="City for market report")
@click.option("--n-listings", type=int, default=300)
def report(city: str, n_listings: int) -> None:
    """Generate a market report for a city."""
    if city not in CITIES:
        console.print(f"[red]Unknown city: {city}. Available: {', '.join(CITIES)}[/red]")
        return

    listings = generate_listings(n=n_listings)
    analyzer = MarketAnalyzer(listings)
    market = analyzer.compute_market_data(city)
    render_market_report(market, console)

    benchmarks = MarketBenchmarks(listings)
    ranked = benchmarks.rank_neighborhoods(city)
    if ranked:
        render_benchmarks_table(ranked, city, console)

    demand = DemandPredictor()
    best_month = demand.best_listing_month(2026)
    console.print(f"\n[bold]Best month to list:[/bold] Month {best_month}")


if __name__ == "__main__":
    main()
