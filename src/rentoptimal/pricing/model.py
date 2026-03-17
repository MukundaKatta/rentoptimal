"""GradientBoosting rent prediction model."""

from __future__ import annotations

from typing import Optional

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder

from rentoptimal.models import Property, PropertyCondition, RentalListing


class RentPredictor:
    """Predict monthly rent using GradientBoosting on property features.

    Features used:
        - location (city encoded)
        - sqft
        - bedrooms
        - bathrooms
        - amenity_count (number of amenities)
        - condition (ordinal-encoded)
        - has_parking, has_laundry, pet_friendly (binary)
    """

    CONDITION_ORD = {
        PropertyCondition.POOR: 0,
        PropertyCondition.FAIR: 1,
        PropertyCondition.GOOD: 2,
        PropertyCondition.EXCELLENT: 3,
    }

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 5,
        learning_rate: float = 0.1,
    ) -> None:
        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42,
        )
        self._city_encoder = LabelEncoder()
        self._is_fitted = False

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def _property_features(self, prop: Property) -> list[float]:
        condition_val = self.CONDITION_ORD.get(prop.condition, 2)
        return [
            prop.sqft,
            float(prop.bedrooms),
            float(prop.bathrooms),
            float(len(prop.amenities)),
            float(condition_val),
            float(prop.has_parking),
            float(prop.has_laundry),
            float(prop.pet_friendly),
        ]

    def _build_X(self, listings: list[RentalListing], fit_encoder: bool = False) -> np.ndarray:
        cities = [l.property.city for l in listings]
        if fit_encoder:
            city_encoded = self._city_encoder.fit_transform(cities)
        else:
            city_encoded = self._city_encoder.transform(cities)

        rows: list[list[float]] = []
        for idx, listing in enumerate(listings):
            row = [float(city_encoded[idx])] + self._property_features(listing.property)
            rows.append(row)
        return np.array(rows)

    # ------------------------------------------------------------------
    # Train / Predict
    # ------------------------------------------------------------------

    def fit(self, listings: list[RentalListing]) -> "RentPredictor":
        """Train the model on historical rental listings."""
        X = self._build_X(listings, fit_encoder=True)
        y = np.array([l.monthly_rent for l in listings])
        self.model.fit(X, y)
        self._is_fitted = True
        return self

    def predict(self, property: Property) -> float:
        """Return predicted monthly rent for a single property."""
        if not self._is_fitted:
            raise RuntimeError("Model has not been fitted. Call fit() first.")
        city_enc = self._city_encoder.transform([property.city])
        row = [float(city_enc[0])] + self._property_features(property)
        X = np.array([row])
        return float(self.model.predict(X)[0])

    def predict_batch(self, properties: list[Property]) -> list[float]:
        """Return predicted rents for multiple properties."""
        return [self.predict(p) for p in properties]

    @property
    def feature_importances(self) -> Optional[dict[str, float]]:
        """Return feature importance dict if model is fitted."""
        if not self._is_fitted:
            return None
        names = [
            "city", "sqft", "bedrooms", "bathrooms",
            "amenity_count", "condition", "has_parking",
            "has_laundry", "pet_friendly",
        ]
        return dict(zip(names, self.model.feature_importances_))
