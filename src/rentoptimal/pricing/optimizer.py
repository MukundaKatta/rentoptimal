"""Revenue-maximizing price optimization."""

from __future__ import annotations

import numpy as np

from rentoptimal.models import Property, PricingRecommendation, MarketData, RentalListing
from rentoptimal.pricing.model import RentPredictor
from rentoptimal.pricing.comparables import CompAnalyzer


class PriceOptimizer:
    """Find the rent that maximizes expected revenue = occupancy * rent.

    The occupancy model assumes a logistic relationship: as rent increases
    above the market rate, the probability of occupancy decreases.
    """

    def __init__(
        self,
        predictor: RentPredictor,
        comp_analyzer: CompAnalyzer,
        base_vacancy: float = 0.06,
    ) -> None:
        self.predictor = predictor
        self.comp_analyzer = comp_analyzer
        self.base_vacancy = base_vacancy

    # ------------------------------------------------------------------
    # Occupancy model
    # ------------------------------------------------------------------

    def occupancy_rate(self, asking_rent: float, market_rent: float) -> float:
        """Estimate occupancy probability given an asking rent.

        Uses a sigmoid curve centred on market_rent.  Rents well below
        market approach 100 % occupancy; rents well above approach 0 %.
        """
        ratio = asking_rent / market_rent if market_rent > 0 else 1.0
        # Steepness controls how fast occupancy drops above market
        steepness = 8.0
        midpoint = 1.0  # at market rent, base occupancy
        occ = 1.0 / (1.0 + np.exp(steepness * (ratio - midpoint)))
        # Scale so that at market rent we get (1 - base_vacancy)
        base_occ = 1.0 / (1.0 + np.exp(0))  # 0.5
        scale = (1.0 - self.base_vacancy) / base_occ
        return float(min(occ * scale, 1.0))

    def expected_revenue(self, asking_rent: float, market_rent: float) -> float:
        """Return occupancy * asking_rent."""
        return self.occupancy_rate(asking_rent, market_rent) * asking_rent

    # ------------------------------------------------------------------
    # Optimization
    # ------------------------------------------------------------------

    def find_optimal_rent(
        self,
        market_rent: float,
        search_low: float | None = None,
        search_high: float | None = None,
        steps: int = 500,
    ) -> tuple[float, float, float]:
        """Grid-search for the rent maximizing expected monthly revenue.

        Returns (optimal_rent, expected_occupancy, expected_revenue).
        """
        low = search_low or market_rent * 0.6
        high = search_high or market_rent * 1.6
        candidates = np.linspace(low, high, steps)
        revenues = np.array(
            [self.expected_revenue(r, market_rent) for r in candidates]
        )
        best_idx = int(np.argmax(revenues))
        best_rent = float(candidates[best_idx])
        best_occ = self.occupancy_rate(best_rent, market_rent)
        best_rev = float(revenues[best_idx])
        return round(best_rent, 2), round(best_occ, 4), round(best_rev, 2)

    # ------------------------------------------------------------------
    # Full recommendation
    # ------------------------------------------------------------------

    def recommend(
        self,
        prop: Property,
        market_data: MarketData | None = None,
    ) -> PricingRecommendation:
        """Produce a full pricing recommendation for a property."""
        predicted_rent = self.predictor.predict(prop)

        comp_stats = self.comp_analyzer.comp_rent_stats(prop)
        comp_rents = [
            c[0].monthly_rent
            for c in self.comp_analyzer.find_comparables(prop)
        ]

        optimal_rent, occ, rev = self.find_optimal_rent(predicted_rent)

        # Confidence heuristic based on comparable count
        n_comps = comp_stats.get("count", 0)
        confidence = min(1.0, n_comps / 10.0) * 0.8 + 0.1

        reasoning_parts = [
            f"ML model predicts market rent of ${predicted_rent:,.0f}/mo.",
        ]
        if n_comps > 0:
            reasoning_parts.append(
                f"Based on {n_comps} comparable listings "
                f"(median ${comp_stats['median']:,.0f}/mo)."
            )
        reasoning_parts.append(
            f"Optimal asking rent of ${optimal_rent:,.0f}/mo yields "
            f"~{occ*100:.0f}% expected occupancy and "
            f"${rev:,.0f}/mo expected revenue."
        )

        return PricingRecommendation(
            property=prop,
            predicted_market_rent=round(predicted_rent, 2),
            optimal_rent=optimal_rent,
            expected_occupancy=occ,
            expected_monthly_revenue=rev,
            comparable_rents=comp_rents,
            market_data=market_data,
            confidence=round(confidence, 3),
            reasoning=" ".join(reasoning_parts),
        )
