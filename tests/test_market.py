"""Tests for market analysis sub-package."""

import pytest
from datetime import date

from rentoptimal.simulator import generate_listings
from rentoptimal.market.analyzer import MarketAnalyzer
from rentoptimal.market.demand import DemandPredictor
from rentoptimal.market.benchmarks import MarketBenchmarks


@pytest.fixture(scope="module")
def listings():
    return generate_listings(n=300, seed=10)


class TestMarketAnalyzer:
    def test_vacancy_rate_in_range(self, listings):
        ma = MarketAnalyzer(listings)
        rate = ma.vacancy_rate("Austin")
        assert 0 <= rate <= 1

    def test_compute_market_data(self, listings):
        ma = MarketAnalyzer(listings)
        md = ma.compute_market_data("Austin")
        assert md.city == "Austin"
        assert md.median_rent > 0
        assert md.total_listings > 0

    def test_missing_city_raises(self, listings):
        ma = MarketAnalyzer(listings)
        with pytest.raises(ValueError):
            ma.compute_market_data("Atlantis")


class TestDemandPredictor:
    def test_demand_index_around_one(self):
        dp = DemandPredictor()
        idx = dp.demand_index(date(2026, 1, 15))
        assert 0.5 < idx < 2.0

    def test_summer_higher_than_winter(self):
        dp = DemandPredictor(peak_month=6)
        summer = dp.demand_index(date(2026, 6, 1))
        winter = dp.demand_index(date(2026, 12, 1))
        assert summer > winter

    def test_forecast_length(self):
        dp = DemandPredictor()
        fc = dp.forecast(date(2026, 1, 1), months=6)
        assert len(fc) == 6

    def test_best_listing_month(self):
        dp = DemandPredictor(peak_month=6)
        best = dp.best_listing_month(2026)
        assert 1 <= best <= 12


class TestMarketBenchmarks:
    def test_city_benchmark(self, listings):
        mb = MarketBenchmarks(listings)
        bench = mb.get_city_benchmark("San Francisco")
        assert "median_ppsf" in bench
        assert bench["median_ppsf"] > 0

    def test_neighborhood_ranking(self, listings):
        mb = MarketBenchmarks(listings)
        ranked = mb.rank_neighborhoods("Austin")
        assert len(ranked) > 0
        # Should be descending
        values = [v for _, v in ranked]
        assert values == sorted(values, reverse=True)

    def test_all_cities(self, listings):
        mb = MarketBenchmarks(listings)
        cities = mb.all_cities()
        assert "Austin" in cities
        assert "San Francisco" in cities
