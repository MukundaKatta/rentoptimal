"""Tests for domain models."""

import pytest
from datetime import date

from rentoptimal.models import (
    Property,
    PropertyCondition,
    RentalListing,
    MarketData,
    PricingRecommendation,
)


def make_property(**overrides) -> Property:
    defaults = dict(
        address="100 Oak St",
        city="Austin",
        state="TX",
        zip_code="78701",
        sqft=800.0,
        bedrooms=2,
        bathrooms=1.0,
        condition=PropertyCondition.GOOD,
    )
    defaults.update(overrides)
    return Property(**defaults)


class TestProperty:
    def test_basic_creation(self):
        p = make_property()
        assert p.city == "Austin"
        assert p.sqft == 800.0
        assert p.bedrooms == 2

    def test_sqft_must_be_positive(self):
        with pytest.raises(Exception):
            make_property(sqft=-10)

    def test_default_amenities(self):
        p = make_property()
        assert p.amenities == []

    def test_condition_enum(self):
        p = make_property(condition=PropertyCondition.EXCELLENT)
        assert p.condition.value == "excellent"


class TestRentalListing:
    def test_creation(self):
        listing = RentalListing(
            property=make_property(),
            monthly_rent=1500.0,
            listed_date=date(2025, 6, 1),
        )
        assert listing.monthly_rent == 1500.0
        assert listing.is_occupied is False

    def test_rent_must_be_positive(self):
        with pytest.raises(Exception):
            RentalListing(
                property=make_property(),
                monthly_rent=-100,
                listed_date=date(2025, 1, 1),
            )


class TestMarketData:
    def test_creation(self):
        md = MarketData(
            city="Austin",
            median_rent=1800.0,
            mean_rent=1900.0,
            median_price_per_sqft=2.25,
            vacancy_rate=0.07,
            total_listings=200,
            avg_days_on_market=30.5,
            rent_trend_pct=0.04,
            sample_period_start=date(2025, 1, 1),
            sample_period_end=date(2025, 6, 30),
        )
        assert md.vacancy_rate == 0.07

    def test_vacancy_rate_bounds(self):
        with pytest.raises(Exception):
            MarketData(
                city="X",
                median_rent=1000,
                mean_rent=1000,
                median_price_per_sqft=2.0,
                vacancy_rate=1.5,
                total_listings=10,
                avg_days_on_market=20,
                rent_trend_pct=0.0,
                sample_period_start=date(2025, 1, 1),
                sample_period_end=date(2025, 6, 1),
            )


class TestPricingRecommendation:
    def test_creation(self):
        rec = PricingRecommendation(
            property=make_property(),
            predicted_market_rent=1800.0,
            optimal_rent=1750.0,
            expected_occupancy=0.93,
            expected_monthly_revenue=1627.5,
            confidence=0.8,
        )
        assert rec.optimal_rent == 1750.0
        assert rec.reasoning == ""
