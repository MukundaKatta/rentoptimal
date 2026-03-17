"""Price-per-sqft benchmarks by city and neighborhood."""

from __future__ import annotations

import numpy as np

from rentoptimal.models import RentalListing


class MarketBenchmarks:
    """Compute and store price-per-sqft benchmarks.

    Benchmarks are organized as a two-level dict:
        city -> neighborhood -> stats dict
    """

    def __init__(self, listings: list[RentalListing]) -> None:
        self.listings = listings
        self._benchmarks: dict[str, dict[str, dict[str, float]]] = {}
        self._compute()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _compute(self) -> None:
        buckets: dict[str, dict[str, list[float]]] = {}
        for listing in self.listings:
            city = listing.property.city
            nbhd = listing.property.neighborhood or "_all"
            ppsf = listing.monthly_rent / listing.property.sqft
            buckets.setdefault(city, {}).setdefault(nbhd, []).append(ppsf)
            buckets[city].setdefault("_all", []).append(ppsf)

        for city, neighborhoods in buckets.items():
            self._benchmarks[city] = {}
            for nbhd, values in neighborhoods.items():
                arr = np.array(values)
                self._benchmarks[city][nbhd] = {
                    "median_ppsf": round(float(np.median(arr)), 2),
                    "mean_ppsf": round(float(np.mean(arr)), 2),
                    "p25_ppsf": round(float(np.percentile(arr, 25)), 2),
                    "p75_ppsf": round(float(np.percentile(arr, 75)), 2),
                    "min_ppsf": round(float(np.min(arr)), 2),
                    "max_ppsf": round(float(np.max(arr)), 2),
                    "count": len(values),
                }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_city_benchmark(self, city: str) -> dict[str, float]:
        """Return aggregate price-per-sqft stats for a city."""
        city_data = self._benchmarks.get(city, {})
        return city_data.get("_all", {})

    def get_neighborhood_benchmark(
        self, city: str, neighborhood: str
    ) -> dict[str, float]:
        """Return price-per-sqft stats for a specific neighborhood."""
        city_data = self._benchmarks.get(city, {})
        return city_data.get(neighborhood, {})

    def all_cities(self) -> list[str]:
        """Return list of cities with benchmark data."""
        return list(self._benchmarks.keys())

    def neighborhoods_for_city(self, city: str) -> list[str]:
        """Return neighborhoods (excluding _all) for a city."""
        city_data = self._benchmarks.get(city, {})
        return [k for k in city_data if k != "_all"]

    def rank_neighborhoods(
        self, city: str, metric: str = "median_ppsf"
    ) -> list[tuple[str, float]]:
        """Rank neighborhoods by a given metric (descending)."""
        city_data = self._benchmarks.get(city, {})
        ranked = []
        for nbhd, stats in city_data.items():
            if nbhd == "_all":
                continue
            if metric in stats:
                ranked.append((nbhd, stats[metric]))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
