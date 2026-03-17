"""Comparable rental listing analysis."""

from __future__ import annotations

import numpy as np

from rentoptimal.models import Property, RentalListing


class CompAnalyzer:
    """Find and analyze comparable (comp) rental listings."""

    def __init__(self, listings: list[RentalListing]) -> None:
        self.listings = listings

    # ------------------------------------------------------------------
    # Similarity scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _similarity(target: Property, candidate: Property) -> float:
        """Return a similarity score in [0, 1] (higher is more similar)."""
        score = 0.0
        max_score = 0.0

        # Same city (required for meaningful comp)
        max_score += 3.0
        if target.city == candidate.city:
            score += 3.0

        # Same neighborhood
        max_score += 2.0
        if target.neighborhood and target.neighborhood == candidate.neighborhood:
            score += 2.0

        # Bedroom match
        max_score += 2.0
        bed_diff = abs(target.bedrooms - candidate.bedrooms)
        if bed_diff == 0:
            score += 2.0
        elif bed_diff == 1:
            score += 1.0

        # Sqft similarity
        max_score += 2.0
        sqft_ratio = min(target.sqft, candidate.sqft) / max(target.sqft, candidate.sqft)
        score += 2.0 * sqft_ratio

        # Condition similarity
        max_score += 1.0
        cond_order = {"poor": 0, "fair": 1, "good": 2, "excellent": 3}
        t_cond = cond_order.get(target.condition.value, 2)
        c_cond = cond_order.get(candidate.condition.value, 2)
        score += 1.0 * max(0, 1 - abs(t_cond - c_cond) / 3)

        return score / max_score if max_score > 0 else 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_comparables(
        self,
        target: Property,
        n: int = 10,
        min_similarity: float = 0.5,
    ) -> list[tuple[RentalListing, float]]:
        """Return up to *n* listings most similar to *target*.

        Returns list of (listing, similarity_score) sorted descending.
        """
        scored: list[tuple[RentalListing, float]] = []
        for listing in self.listings:
            sim = self._similarity(target, listing.property)
            if sim >= min_similarity:
                scored.append((listing, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:n]

    def comp_rent_stats(
        self,
        target: Property,
        n: int = 10,
    ) -> dict[str, float]:
        """Return summary statistics for comparable rents."""
        comps = self.find_comparables(target, n=n)
        if not comps:
            return {"count": 0}

        rents = [c[0].monthly_rent for c in comps]
        return {
            "count": len(rents),
            "min": float(np.min(rents)),
            "max": float(np.max(rents)),
            "mean": round(float(np.mean(rents)), 2),
            "median": round(float(np.median(rents)), 2),
            "std": round(float(np.std(rents)), 2),
        }
