"""Market-level analytics -- vacancy rates and rent trends."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from rentoptimal.models import MarketData, RentalListing


class MarketAnalyzer:
    """Compute area-level vacancy rates and rent trends."""

    def __init__(self, listings: list[RentalListing]) -> None:
        self.listings = listings

    # ------------------------------------------------------------------
    # Vacancy
    # ------------------------------------------------------------------

    def vacancy_rate(self, city: str, neighborhood: str | None = None) -> float:
        """Fraction of listings that are unoccupied."""
        subset = [l for l in self.listings if l.property.city == city]
        if neighborhood:
            subset = [l for l in subset if l.property.neighborhood == neighborhood]
        if not subset:
            return 0.0
        vacant = sum(1 for l in subset if not l.is_occupied)
        return round(vacant / len(subset), 4)

    # ------------------------------------------------------------------
    # Rent trends
    # ------------------------------------------------------------------

    def rent_trend(
        self,
        city: str,
        window_days: int = 90,
    ) -> float:
        """Estimate annualized rent trend from recent vs. older listings.

        Compares median rent of listings from the last *window_days* to
        those from the prior period.  Returns a decimal (0.05 = +5%/yr).
        """
        today = date.today()
        recent_cutoff = today - timedelta(days=window_days)
        old_cutoff = recent_cutoff - timedelta(days=window_days)

        city_listings = [l for l in self.listings if l.property.city == city]
        recent = [l for l in city_listings if l.listed_date >= recent_cutoff]
        older = [l for l in city_listings if old_cutoff <= l.listed_date < recent_cutoff]

        if not recent or not older:
            return 0.0

        med_recent = float(np.median([l.monthly_rent for l in recent]))
        med_older = float(np.median([l.monthly_rent for l in older]))

        if med_older == 0:
            return 0.0

        period_change = (med_recent - med_older) / med_older
        annualized = period_change * (365 / window_days)
        return round(annualized, 4)

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------

    def compute_market_data(self, city: str) -> MarketData:
        """Build a full MarketData snapshot for a city."""
        city_listings = [l for l in self.listings if l.property.city == city]
        if not city_listings:
            raise ValueError(f"No listings found for city: {city}")

        rents = [l.monthly_rent for l in city_listings]
        ppsf = [l.monthly_rent / l.property.sqft for l in city_listings]
        doms = [l.days_on_market for l in city_listings]
        today = date.today()

        return MarketData(
            city=city,
            median_rent=round(float(np.median(rents)), 2),
            mean_rent=round(float(np.mean(rents)), 2),
            median_price_per_sqft=round(float(np.median(ppsf)), 2),
            vacancy_rate=self.vacancy_rate(city),
            total_listings=len(city_listings),
            avg_days_on_market=round(float(np.mean(doms)), 1),
            rent_trend_pct=self.rent_trend(city),
            sample_period_start=today - timedelta(days=180),
            sample_period_end=today,
        )
