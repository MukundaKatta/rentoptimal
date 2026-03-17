# RentOptimal

Rental Price Optimizer -- a data-driven tool for maximizing rental revenue.

RentOptimal combines gradient-boosting price prediction, comparable-listing
analysis, and occupancy-aware revenue optimization to recommend the best
asking rent for any residential property.

## Features

* **Price Prediction** -- GradientBoosting model trained on location, size,
  bedrooms, amenities, and condition features.
* **Comparable Analysis** -- finds similar rental listings and derives
  pricing insights from the local market.
* **Revenue Optimization** -- searches for the rent that maximizes
  `occupancy_rate * monthly_rent` (expected revenue).
* **Market Analytics** -- vacancy rates, rent trends, seasonal demand
  forecasting, and price-per-sqft benchmarks by city/neighborhood.
* **Synthetic Data** -- built-in simulator for generating realistic rental
  market datasets.
* **Rich Reports** -- beautiful terminal reports via Rich.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Generate sample market data and run pricing analysis
rentoptimal analyze --city "San Francisco" --bedrooms 2 --sqft 950

# Generate a full market report
rentoptimal report --city "San Francisco"
```

## Dependencies

numpy, scikit-learn, pydantic, click, rich

## Author

Mukunda Katta
