"""
test_price_prediction.py
------------------------
Unit tests for evaluation metrics, chronological splits, and price model prediction intervals.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from src.price_prediction import (
    safe_mape,
    evaluate_predictions,
    chronological_train_val_test_split,
    PricePredictor
)
from src.feature_engineering import AgriFeaturePipeline, create_time_features, create_lag_and_rolling_features


def test_safe_mape_handles_zeros():
    y_true = np.array([100.0, 0.0, 200.0])
    y_pred = np.array([110.0, 50.0, 190.0])
    # Should safely compute MAPE only on nonzero actuals without crashing
    mape = safe_mape(y_true, y_pred)
    assert mape > 0
    assert not np.isnan(mape)


def test_chronological_split_no_overlap():
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "market": ["Kolar"] * 100,
        "district": ["Kolar"] * 100,
        "modal_price": np.random.uniform(1000, 2000, 100),
        "arrivals_qtl": np.random.uniform(1000, 5000, 100)
    })
    train_df, val_df, test_df = chronological_train_val_test_split(df, 0.70, 0.15)
    
    assert train_df["date"].max() < val_df["date"].min()
    assert val_df["date"].max() < test_df["date"].min()
    assert len(train_df) + len(val_df) + len(test_df) == 100


def test_price_predictor_interval_bounds():
    # Create synthetic dataset and preprocessor
    dates = pd.date_range("2025-01-01", periods=30, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "market": ["Kolar"] * 30,
        "district": ["Kolar"] * 30,
        "commodity": ["Tomato"] * 30,
        "modal_price": np.linspace(1400, 1800, 30),
        "arrivals_qtl": np.linspace(3000, 3500, 30)
    })
    df_feat = create_time_features(df)
    df_feat = create_lag_and_rolling_features(df_feat)
    
    preproc = AgriFeaturePipeline()
    preproc.fit(df_feat)
    X = preproc.transform(df_feat)
    y = df_feat["modal_price"].values
    
    rf = RandomForestRegressor(n_estimators=10, random_state=42)
    rf.fit(X, y)
    
    predictor = PricePredictor(model_name="RandomForest", model=rf, preprocessor=preproc)
    predictor.feature_names = preproc.all_feature_names
    
    preds = predictor.predict_with_interval(df_feat.tail(2), confidence_level=0.80)
    assert len(preds) == 2
    for p in preds:
        assert "predicted_modal_price" in p
        assert "prediction_interval" in p
        assert p["prediction_interval"]["lower_bound"] <= p["predicted_modal_price"]
        assert p["predicted_modal_price"] <= p["prediction_interval"]["upper_bound"]
        assert "uncertainty_disclaimer" in p
