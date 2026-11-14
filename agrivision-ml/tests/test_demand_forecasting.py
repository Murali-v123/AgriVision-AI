"""
test_demand_forecasting.py
--------------------------
Unit tests for demand pressure targets, proxy limitations, and classification outputs.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from src.demand_forecasting import (
    compute_demand_pressure_target,
    DemandForecaster,
    DEMAND_LIMITATION_NOTICE
)


def test_compute_demand_pressure_target():
    dates = pd.date_range("2025-01-01", periods=20, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "market": ["Kolar"] * 20,
        "modal_price": [1000 + i * 20 for i in range(20)],
        "arrivals_qtl": [2000 + i * 50 for i in range(20)]
    })
    labeled_df = compute_demand_pressure_target(df)
    assert "demand_trend_target" in labeled_df.columns
    valid_classes = {"Increasing", "Decreasing", "Stable"}
    assert set(labeled_df["demand_trend_target"].unique()).issubset(valid_classes)


def test_demand_forecaster_predictions():
    feature_cols = ["month", "week", "modal_price_lag_1", "arrivals_lag_1"]
    X = np.random.uniform(10, 100, (30, len(feature_cols)))
    le = LabelEncoder()
    y_raw = ["Increasing", "Decreasing", "Stable"] * 10
    y = le.fit_transform(y_raw)
    
    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    clf.fit(X, y)
    
    forecaster = DemandForecaster(model=clf, label_encoder=le, feature_cols=feature_cols)
    
    test_df = pd.DataFrame({
        "month": [5],
        "week": [20],
        "modal_price_lag_1": [1600.0],
        "arrivals_lag_1": [3500.0]
    })
    
    res = forecaster.forecast(test_df)[0]
    assert res["demand_trend"] in ["Increasing", "Decreasing", "Stable"]
    assert 0.0 <= res["confidence_score"] <= 1.0
    assert "economic_interpretation" in res
    assert DEMAND_LIMITATION_NOTICE == res["proxy_disclaimer"]
