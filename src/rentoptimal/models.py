"""Domain models for RentOptimal."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PropertyCondition(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class Property(BaseModel):
    """A rental property."""

    address: str
    city: str
    state: str
    zip_code: str
    neighborhood: Optional[str] = None
    latitude: float = 0.0
    longitude: float = 0.0
    sqft: float = Field(gt=0, description="Living area in square feet")
    bedrooms: int = Field(ge=0)
    bathrooms: float = Field(ge=0)
    year_built: Optional[int] = None
    condition: PropertyCondition = PropertyCondition.GOOD
    amenities: list[str] = Field(default_factory=list)
    has_parking: bool = False
    has_laundry: bool = False
    pet_friendly: bool = False


class RentalListing(BaseModel):
    """A rental listing with pricing information."""

    property: Property
    monthly_rent: float = Field(gt=0)
    listed_date: date
    is_occupied: bool = False
    days_on_market: int = 0
    lease_term_months: int = 12


class MarketData(BaseModel):
    """Aggregated market data for an area."""

    city: str
    neighborhood: Optional[str] = None
    median_rent: float
    mean_rent: float
    median_price_per_sqft: float
    vacancy_rate: float = Field(ge=0, le=1)
    total_listings: int
    avg_days_on_market: float
    rent_trend_pct: float = Field(
        description="Year-over-year rent change as a decimal (0.05 = +5%)"
    )
    sample_period_start: date
    sample_period_end: date


class PricingRecommendation(BaseModel):
    """Output of the pricing optimization pipeline."""

    property: Property
    predicted_market_rent: float = Field(
        description="ML-predicted fair-market rent"
    )
    optimal_rent: float = Field(
        description="Rent maximizing expected revenue (occupancy * rent)"
    )
    expected_occupancy: float = Field(
        ge=0, le=1, description="Predicted occupancy rate at optimal rent"
    )
    expected_monthly_revenue: float = Field(
        description="optimal_rent * expected_occupancy"
    )
    comparable_rents: list[float] = Field(
        default_factory=list,
        description="Monthly rents of comparable properties",
    )
    market_data: Optional[MarketData] = None
    confidence: float = Field(
        ge=0, le=1, description="Model confidence in the recommendation"
    )
    reasoning: str = ""
