"""Tests for the rental market simulator."""

from rentoptimal.simulator import generate_listings, generate_market_data


class TestGenerateListings:
    def test_default_returns_listings(self):
        listings = generate_listings(n=50, seed=1)
        assert len(listings) > 0

    def test_single_city(self):
        listings = generate_listings(city="Austin", n=30, seed=2)
        assert all(l.property.city == "Austin" for l in listings)

    def test_deterministic_with_seed(self):
        a = generate_listings(n=20, seed=99)
        b = generate_listings(n=20, seed=99)
        assert [l.monthly_rent for l in a] == [l.monthly_rent for l in b]

    def test_positive_rents(self):
        listings = generate_listings(n=100, seed=3)
        assert all(l.monthly_rent > 0 for l in listings)

    def test_valid_sqft(self):
        listings = generate_listings(n=100, seed=4)
        assert all(l.property.sqft >= 300 for l in listings)


class TestGenerateMarketData:
    def test_returns_market_data(self):
        md = generate_market_data("San Francisco")
        assert md.city == "San Francisco"
        assert md.median_rent > 0
        assert 0 <= md.vacancy_rate <= 1

    def test_with_provided_listings(self):
        listings = generate_listings(city="Chicago", n=50)
        md = generate_market_data("Chicago", listings)
        assert md.total_listings == 50
