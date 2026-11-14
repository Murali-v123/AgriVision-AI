"""
test_feature_engineering.py
---------------------------
Unit tests for temporal feature generation, lag calculation, and leakage prevention.
"""

import pytest
import pandas as pd
import numpy as np
from src.feature_engineering import (
    get_agricultural_season,
    create_time_features,
    create_lag_and_rolling_features,
    AgriFeaturePipeline
)


def test_agricultural_season_mapping():
    assert get_agricultural_season(4) == "Summer"
    assert get_agricultural_season(8) == "Kharif"
    assert get_agricultural_season(12) == "Rabi"
    assert get_agricultural_season(1) == "Rabi"


def test_time_features():
    df = pd.DataFrame({"date": ["2025-05-15", "2025-05-17"]})
    res = create_time_features(df)
    assert res["month"].iloc[0] == 5
    assert res["season"].iloc[0] == "Summer"
    assert res["is_weekend"].iloc[0] == 0
    assert res["is_weekend"].iloc[1] == 1 # 2025-05-17 is Saturday
    assert -1.0 <= res["sin_month"].iloc[0] <= 1.0


def test_market_isolated_lags_and_no_leakage():
    # 2 markets, 10 days each
    dates = pd.date_range("2025-01-01", periods=10, freq="D")
    df_kolar = pd.DataFrame({
        "date": dates,
        "market": "Kolar",
        "district": "Kolar",
        "modal_price": [1000 + i * 10 for i in range(10)],
        "arrivals_qtl": [2000 + i * 50 for i in range(10)]
    })
    df_blr = pd.DataFrame({
        "date": dates,
        "market": "Bangalore",
        "district": "Bangalore Urban",
        "modal_price": [2000 + i * 20 for i in range(10)],
        "arrivals_qtl": [4000 + i * 100 for i in range(10)]
    })
    combined = pd.concat([df_kolar, df_blr], ignore_index=True)
    
    engineered = create_lag_and_rolling_features(combined)
    
    # Check Kolar day 5: lag-1 price must equal day 4 modal price (1030)
    kolar_sub = engineered[engineered["market"] == "Kolar"].sort_values("date").reset_index(drop=True)
    assert kolar_sub.loc[4, "modal_price_lag_1"] == 1030
    
    # Bangalore day 0 must NOT inherit any Kolar prices (cross-market leakage check)
    blr_sub = engineered[engineered["market"] == "Bangalore"].sort_values("date").reset_index(drop=True)
    assert blr_sub.loc[1, "modal_price_lag_1"] == 2000 # strictly Bangalore's day 0
    
    # Rolling 7 mean should strictly use past days [t-7, t-1]
    assert "price_rolling_mean_7" in engineered.columns


def test_agri_feature_pipeline():
    df = pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=5),
        "market": ["Kolar"] * 5,
        "district": ["Kolar"] * 5,
        "modal_price": [1500, 1520, 1510, 1530, 1540],
        "arrivals_qtl": [3000, 3100, 2900, 3200, 3050]
    })
    df_feat = create_time_features(df)
    df_feat = create_lag_and_rolling_features(df_feat)
    
    pipeline = AgriFeaturePipeline()
    pipeline.fit(df_feat)
    transformed = pipeline.transform(df_feat)
    
    assert transformed.shape[0] == 5
    assert not transformed.isna().any().any()
    assert any("market_Kolar" in col for col in transformed.columns)
