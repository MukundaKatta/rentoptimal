"""Seasonal rental demand forecasting."""

from __future__ import annotations

import math
from datetime import date

import numpy as np


class DemandPredictor:
    """Forecast seasonal rental demand using a sinusoidal model.

    Rental markets typically peak in summer (May-Aug) and trough in
    winter (Nov-Feb).  This predictor captures that pattern and adds
    a linear trend component.
    """

    def __init__(
        self,
        peak_month: int = 6,
        amplitude: float = 0.15,
        annual_growth: float = 0.03,
    ) -> None:
        self.peak_month = peak_month
        self.amplitude = amplitude
        self.annual_growth = annual_growth

    def demand_index(self, target_date: date, base_date: date | None = None) -> float:
        """Return a demand index (1.0 = average, >1 = above average).

        Combines a seasonal sinusoidal component with a linear growth
        trend.
        """
        if base_date is None:
            base_date = date(target_date.year, 1, 1)

        # Seasonal component
        month_offset = target_date.month - self.peak_month
        seasonal = 1.0 + self.amplitude * math.cos(2 * math.pi * month_offset / 12)

        # Trend component
        years_elapsed = (target_date - base_date).days / 365.25
        trend = 1.0 + self.annual_growth * years_elapsed

        return round(seasonal * trend, 4)

    def forecast(
        self,
        start: date,
        months: int = 12,
    ) -> list[tuple[date, float]]:
        """Return monthly demand indices for the next *months* months."""
        results: list[tuple[date, float]] = []
        for i in range(months):
            m = start.month + i
            y = start.year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            d = date(y, m, 1)
            results.append((d, self.demand_index(d, base_date=start)))
        return results

    def best_listing_month(self, year: int) -> int:
        """Return the month number (1-12) with highest demand for *year*."""
        indices = []
        for m in range(1, 13):
            d = date(year, m, 1)
            indices.append(self.demand_index(d))
        return int(np.argmax(indices)) + 1
