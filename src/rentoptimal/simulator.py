"""Generate synthetic rental market data for testing and demos."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Optional

import numpy as np

from rentoptimal.models import (
    MarketData,
    Property,
    PropertyCondition,
    RentalListing,
)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

CITIES: dict[str, dict] = {
    "San Francisco": {
        "state": "CA",
        "base_rent_per_sqft": 4.50,
        "vacancy": 0.06,
        "trend": 0.03,
        "neighborhoods": ["Mission", "SOMA", "Marina", "Sunset", "Richmond"],
    },
    "New York": {
        "state": "NY",
        "base_rent_per_sqft": 5.00,
        "vacancy": 0.04,
        "trend": 0.04,
        "neighborhoods": ["Harlem", "Chelsea", "Williamsburg", "Astoria", "UWS"],
    },
    "Austin": {
        "state": "TX",
        "base_rent_per_sqft": 2.20,
        "vacancy": 0.08,
        "trend": 0.05,
        "neighborhoods": ["Downtown", "East Austin", "South Lamar", "Mueller", "Hyde Park"],
    },
    "Chicago": {
        "state": "IL",
        "base_rent_per_sqft": 2.00,
        "vacancy": 0.07,
        "trend": 0.02,
        "neighborhoods": ["Lincoln Park", "Wicker Park", "Logan Square", "Loop", "Lakeview"],
    },
    "Denver": {
        "state": "CO",
        "base_rent_per_sqft": 2.40,
        "vacancy": 0.06,
        "trend": 0.04,
        "neighborhoods": ["LoDo", "Capitol Hill", "RiNo", "Highlands", "Cherry Creek"],
    },
}

AMENITIES_POOL = [
    "dishwasher", "central_ac", "hardwood_floors", "balcony",
    "gym", "pool", "doorman", "rooftop", "storage", "elevator",
]

CONDITIONS = list(PropertyCondition)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))


def _rent_for_property(
    base_per_sqft: float,
    sqft: float,
    bedrooms: int,
    condition: PropertyCondition,
    amenity_count: int,
) -> float:
    """Compute a noisy but realistic monthly rent."""
    condition_mult = {
        PropertyCondition.EXCELLENT: 1.15,
        PropertyCondition.GOOD: 1.00,
        PropertyCondition.FAIR: 0.88,
        PropertyCondition.POOR: 0.75,
    }
    base = base_per_sqft * sqft
    base *= condition_mult[condition]
    base += amenity_count * 30  # each amenity adds ~$30/mo
    base += bedrooms * 50
    noise = np.random.normal(1.0, 0.07)
    return round(max(base * noise, 500), 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_listings(
    city: Optional[str] = None,
    n: int = 200,
    seed: int = 42,
) -> list[RentalListing]:
    """Return *n* synthetic rental listings for *city* (or all cities)."""
    rng = random.Random(seed)
    np.random.seed(seed)

    cities = [city] if city and city in CITIES else list(CITIES.keys())
    per_city = max(n // len(cities), 1)

    listings: list[RentalListing] = []
    today = date.today()

    for c in cities:
        info = CITIES[c]
        for _ in range(per_city):
            bedrooms = rng.choice([0, 1, 1, 2, 2, 2, 3, 3, 4])
            sqft = int(rng.gauss(450 + bedrooms * 350, 120))
            sqft = max(sqft, 300)
            condition = rng.choice(CONDITIONS)
            n_amenities = rng.randint(0, 6)
            amenities = rng.sample(AMENITIES_POOL, n_amenities)
            neighborhood = rng.choice(info["neighborhoods"])

            prop = Property(
                address=f"{rng.randint(100, 9999)} {rng.choice(['Oak', 'Main', 'Pine', 'Elm', 'Market'])} St",
                city=c,
                state=info["state"],
                zip_code=f"{rng.randint(10000, 99999)}",
                neighborhood=neighborhood,
                latitude=round(rng.uniform(37.0, 42.0), 6),
                longitude=round(rng.uniform(-122.5, -73.5), 6),
                sqft=float(sqft),
                bedrooms=bedrooms,
                bathrooms=max(1.0, bedrooms * 0.5 + rng.choice([0, 0.5, 0.5, 1.0])),
                year_built=rng.randint(1920, 2024),
                condition=condition,
                amenities=amenities,
                has_parking=rng.random() < 0.4,
                has_laundry=rng.random() < 0.6,
                pet_friendly=rng.random() < 0.5,
            )

            rent = _rent_for_property(
                info["base_rent_per_sqft"], prop.sqft, bedrooms, condition, n_amenities
            )
            listed = _random_date(today - timedelta(days=180), today)
            dom = (today - listed).days
            occupied = rng.random() > info["vacancy"]

            listings.append(
                RentalListing(
                    property=prop,
                    monthly_rent=rent,
                    listed_date=listed,
                    is_occupied=occupied,
                    days_on_market=dom,
                    lease_term_months=rng.choice([6, 12, 12, 12, 24]),
                )
            )

    return listings


def generate_market_data(city: str, listings: list[RentalListing] | None = None) -> MarketData:
    """Compute aggregate market data from listings (generates if needed)."""
    if listings is None:
        listings = generate_listings(city=city)

    city_listings = [l for l in listings if l.property.city == city]
    if not city_listings:
        city_listings = generate_listings(city=city)

    rents = [l.monthly_rent for l in city_listings]
    sqfts = [l.property.sqft for l in city_listings]
    ppsf = [r / s for r, s in zip(rents, sqfts)]
    occupied = [l.is_occupied for l in city_listings]
    doms = [l.days_on_market for l in city_listings]

    info = CITIES.get(city, {"vacancy": 0.07, "trend": 0.03})
    today = date.today()

    return MarketData(
        city=city,
        median_rent=round(float(np.median(rents)), 2),
        mean_rent=round(float(np.mean(rents)), 2),
        median_price_per_sqft=round(float(np.median(ppsf)), 2),
        vacancy_rate=round(1 - sum(occupied) / len(occupied), 4),
        total_listings=len(city_listings),
        avg_days_on_market=round(float(np.mean(doms)), 1),
        rent_trend_pct=info.get("trend", 0.03),
        sample_period_start=today - timedelta(days=180),
        sample_period_end=today,
    )
