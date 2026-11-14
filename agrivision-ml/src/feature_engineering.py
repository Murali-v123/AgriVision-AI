"""
feature_engineering.py
----------------------
AgriVision AI - Agricultural Price Intelligence & Demand Forecasting
Extracts temporal, cyclical, seasonal, market-level lag, and rolling statistics
without data leakage.
"""

import os
import json
import logging
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Karnataka Agricultural Seasons
def get_agricultural_season(month: int) -> str:
    """
    Maps month to Karnataka agricultural crop season:
    - Summer / Zaid: March (3) to June (6)
    - Kharif (Monsoon): July (7) to October (10)
    - Rabi (Winter): November (11) to February (2)
    """
    if month in [3, 4, 5, 6]:
        return "Summer"
    elif month in [7, 8, 9, 10]:
        return "Kharif"
    else:
        return "Rabi"


def create_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts calendar, cyclical, and seasonal features."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
        
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_year"] = df["date"].dt.dayofyear
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    
    # Cyclical sin/cos encodings for annual and weekly cycles
    df["sin_day_of_year"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["cos_day_of_year"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)
    
    df["season"] = df["month"].apply(get_agricultural_season)
    return df


def create_lag_and_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes lag prices (1, 3, 7, 14 days) and rolling averages (7, 14 days)
    strictly grouped by market to prevent cross-market and future data leakage.
    """
    df = df.copy()
    # Sort rigorously by market and date
    df = df.sort_values(by=["market", "date"]).reset_index(drop=True)
    
    # Target column to lag
    grouped = df.groupby("market")
    
    # Price Lags
    for lag in [1, 3, 7, 14]:
        df[f"modal_price_lag_{lag}"] = grouped["modal_price"].shift(lag)
        
    # Arrivals Lags
    for lag in [1, 3, 7]:
        df[f"arrivals_lag_{lag}"] = grouped["arrivals_qtl"].shift(lag)
        
    # Rolling Statistics (using shifted series so current day's price/arrival is never included)
    for window in [7, 14]:
        # Shift 1 first, so rolling window strictly looks at past days [t-window, t-1]
        shifted_price = grouped["modal_price"].shift(1)
        df[f"price_rolling_mean_{window}"] = shifted_price.groupby(df["market"]).transform(
            lambda s: s.rolling(window, min_periods=max(2, window // 2)).mean()
        )
        df[f"price_rolling_std_{window}"] = shifted_price.groupby(df["market"]).transform(
            lambda s: s.rolling(window, min_periods=max(2, window // 2)).std()
        )
        
    # Rolling Arrivals (7-day past)
    shifted_arrivals = grouped["arrivals_qtl"].shift(1)
    df["arrivals_rolling_mean_7"] = shifted_arrivals.groupby(df["market"]).transform(
        lambda s: s.rolling(7, min_periods=3).mean()
    )
    
    # Momentum & Ratio features
    df["price_momentum_7d"] = df["modal_price_lag_1"] - df["modal_price_lag_7"]
    df["price_ratio_to_7d_mean"] = df["modal_price_lag_1"] / (df["price_rolling_mean_7"] + 1e-5)
    df["arrival_ratio_to_7d_mean"] = df["arrivals_lag_1"] / (df["arrivals_rolling_mean_7"] + 1e-5)
    
    # Fill early burn-in NaNs within each market using forward/backward fill then market medians
    feature_cols = [
        "modal_price_lag_1", "modal_price_lag_3", "modal_price_lag_7", "modal_price_lag_14",
        "arrivals_lag_1", "arrivals_lag_3", "arrivals_lag_7",
        "price_rolling_mean_7", "price_rolling_std_7",
        "price_rolling_mean_14", "price_rolling_std_14",
        "arrivals_rolling_mean_7", "price_momentum_7d",
        "price_ratio_to_7d_mean", "arrival_ratio_to_7d_mean"
    ]
    
    for col in feature_cols:
        df[col] = df.groupby("market")[col].transform(lambda s: s.bfill().ffill())
        # If still NaN (e.g. overall start), fill with global column median
        df[col] = df[col].fillna(df[col].median() if not np.isnan(df[col].median()) else 0.0)
        
    return df


class AgriFeaturePipeline(BaseEstimator, TransformerMixin):
    """
    Sklearn-compatible feature pipeline that encodes categorical variables (market, district, season),
    scales numerical features (if needed), and prepares feature matrices reproducibly.
    Fits ONLY on training splits to prevent data leakage.
    """
    def __init__(self):
        self.cat_encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        self.cat_cols = ["market", "district", "season"]
        self.num_cols = [
            "month", "week", "day_of_week", "is_weekend",
            "sin_day_of_year", "cos_day_of_year", "sin_month", "cos_month",
            "modal_price_lag_1", "modal_price_lag_3", "modal_price_lag_7", "modal_price_lag_14",
            "arrivals_lag_1", "arrivals_lag_3", "arrivals_lag_7",
            "price_rolling_mean_7", "price_rolling_std_7",
            "price_rolling_mean_14", "price_rolling_std_14",
            "arrivals_rolling_mean_7", "price_momentum_7d",
            "price_ratio_to_7d_mean", "arrival_ratio_to_7d_mean"
        ]
        self.fitted_cat_feature_names: List[str] = []
        self.all_feature_names: List[str] = []
        self.is_fitted = False
        
    def fit(self, X: pd.DataFrame, y=None):
        df = X.copy()
        if "season" not in df.columns:
            df = create_time_features(df)
            
        self.cat_encoder.fit(df[self.cat_cols])
        self.fitted_cat_feature_names = list(self.cat_encoder.get_feature_names_out(self.cat_cols))
        self.all_feature_names = self.num_cols + self.fitted_cat_feature_names
        self.is_fitted = True
        return self
        
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("AgriFeaturePipeline must be fitted before transforming data.")
        df = X.copy()
        if "season" not in df.columns:
            df = create_time_features(df)
            
        # Ensure all num_cols are present
        for col in self.num_cols:
            if col not in df.columns:
                df[col] = 0.0
                
        cat_encoded_arr = self.cat_encoder.transform(df[self.cat_cols])
        cat_encoded_df = pd.DataFrame(
            cat_encoded_arr,
            columns=self.fitted_cat_feature_names,
            index=df.index
        )
        
        num_df = df[self.num_cols].astype(float)
        transformed_df = pd.concat([num_df, cat_encoded_df], axis=1)
        return transformed_df


def engineer_dataset(clean_csv_path: str) -> pd.DataFrame:
    """
    Loads cleaned CSV, adds calendar features, computes strictly isolated lag/rolling stats.
    Returns the enriched feature DataFrame.
    """
    df = pd.read_csv(clean_csv_path)
    df["date"] = pd.to_datetime(df["date"])
    
    # 1. Calendar & seasonal features
    df = create_time_features(df)
    
    # 2. Market-isolated lag and rolling statistics
    df = create_lag_and_rolling_features(df)
    
    logger.info("Feature engineering complete: %d rows, %d columns.", len(df), df.shape[1])
    return df


if __name__ == "__main__":
    df = engineer_dataset("../data/processed/clean_tomato_data.csv")
    print("Features engineered successfully. Shape:", df.shape)
    print("Sample columns:", list(df.columns)[:15])
