"""Tests for pricing sub-package."""

import pytest

from rentoptimal.models import Property, PropertyCondition
from rentoptimal.simulator import generate_listings
from rentoptimal.pricing.model import RentPredictor
from rentoptimal.pricing.comparables import CompAnalyzer
from rentoptimal.pricing.optimizer import PriceOptimizer


def _prop(**kw) -> Property:
    defaults = dict(
        address="1 Main St", city="Austin", state="TX", zip_code="78701",
        sqft=900.0, bedrooms=2, bathrooms=1.0, condition=PropertyCondition.GOOD,
    )
    defaults.update(kw)
    return Property(**defaults)


@pytest.fixture(scope="module")
def listings():
    return generate_listings(n=200, seed=42)


@pytest.fixture(scope="module")
def fitted_predictor(listings):
    predictor = RentPredictor(n_estimators=50, max_depth=3)
    predictor.fit(listings)
    return predictor


class TestRentPredictor:
    def test_predict_returns_positive(self, fitted_predictor):
        pred = fitted_predictor.predict(_prop())
        assert pred > 0

    def test_larger_units_cost_more(self, fitted_predictor):
        small = fitted_predictor.predict(_prop(sqft=500.0, bedrooms=1))
        large = fitted_predictor.predict(_prop(sqft=1500.0, bedrooms=3))
        assert large > small

    def test_feature_importances(self, fitted_predictor):
        imp = fitted_predictor.feature_importances
        assert imp is not None
        assert "sqft" in imp
        assert all(v >= 0 for v in imp.values())

    def test_unfitted_raises(self):
        p = RentPredictor()
        with pytest.raises(RuntimeError):
            p.predict(_prop())


class TestCompAnalyzer:
    def test_find_comps(self, listings):
        analyzer = CompAnalyzer(listings)
        comps = analyzer.find_comparables(_prop(), n=5)
        assert 0 < len(comps) <= 5
        # All comps should be from the same city
        assert all(c[0].property.city == "Austin" for c in comps)

    def test_comp_stats(self, listings):
        analyzer = CompAnalyzer(listings)
        stats = analyzer.comp_rent_stats(_prop())
        assert stats["count"] > 0
        assert stats["median"] > 0

    def test_no_comps_different_city(self, listings):
        analyzer = CompAnalyzer(listings)
        prop = _prop(city="Nowhere", state="XX")
        comps = analyzer.find_comparables(prop, min_similarity=0.8)
        # Should find very few or none since city doesn't match
        assert len(comps) == 0


class TestPriceOptimizer:
    def test_optimal_rent_positive(self, fitted_predictor, listings):
        comp = CompAnalyzer(listings)
        opt = PriceOptimizer(fitted_predictor, comp)
        rent, occ, rev = opt.find_optimal_rent(market_rent=2000.0)
        assert rent > 0
        assert 0 <= occ <= 1
        assert rev > 0

    def test_revenue_curve_concave(self, fitted_predictor, listings):
        comp = CompAnalyzer(listings)
        opt = PriceOptimizer(fitted_predictor, comp)
        market = 2000.0
        # Revenue at market should exceed revenue far above market
        rev_at_market = opt.expected_revenue(market, market)
        rev_high = opt.expected_revenue(market * 2.0, market)
        assert rev_at_market > rev_high

    def test_recommend(self, fitted_predictor, listings):
        comp = CompAnalyzer(listings)
        opt = PriceOptimizer(fitted_predictor, comp)
        rec = opt.recommend(_prop())
        assert rec.optimal_rent > 0
        assert rec.confidence > 0
        assert len(rec.reasoning) > 0
