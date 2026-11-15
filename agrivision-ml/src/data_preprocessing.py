"""
data_preprocessing.py
---------------------
AgriVision AI - Agricultural Price Intelligence & Demand Forecasting
Performs data cleaning, validation, type conversions, outlier handling,
and produces a validated dataset ready for feature engineering.
"""

import os
import json
import logging
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Standard schema definition
REQUIRED_COLUMNS = ["date", "market", "district", "modal_price"]
RECOMMENDED_COLUMNS = ["min_price", "max_price", "arrivals_qtl", "commodity"]


def load_raw_data(raw_csv_path: str) -> pd.DataFrame:
    """Loads raw dataset from CSV with encoding fallbacks."""
    if not os.path.exists(raw_csv_path):
        raise FileNotFoundError(f"Raw data file not found at {raw_csv_path}")
        
    try:
        df = pd.read_csv(raw_csv_path)
    except UnicodeDecodeError:
        df = pd.read_csv(raw_csv_path, encoding="latin1")
        
    logger.info("Loaded %d rows from %s", len(df), raw_csv_path)
    return df


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes column names to lowercase snake_case."""
    df = df.copy()
    rename_map = {
        "Arrival_Date": "date",
        "Arrival_date": "date",
        "Date": "date",
        "Market": "market",
        "Market Name": "market",
        "District": "district",
        "District Name": "district",
        "Commodity": "commodity",
        "Crop": "commodity",
        "Variety": "variety",
        "Min_Price": "min_price",
        "Min Price": "min_price",
        "Max_Price": "max_price",
        "Max Price": "max_price",
        "Modal_Price": "modal_price",
        "Modal Price": "modal_price",
        "Modal_x0020_Price": "modal_price",
        "Arrivals": "arrivals_qtl",
        "Arrivals (Tonnes)": "arrivals_tonnes",
    }
    df = df.rename(columns=rename_map)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    
    # If arrivals are in tonnes, convert to quintals (1 Tonne = 10 Quintals)
    if "arrivals_tonnes" in df.columns and "arrivals_qtl" not in df.columns:
        df["arrivals_qtl"] = pd.to_numeric(df["arrivals_tonnes"], errors="coerce") * 10
        
    return df


def clean_and_validate_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw dataframe, handles nulls, removes duplicates, enforces price logic,
    and returns cleaned dataframe alongside preprocessing statistics.
    """
    initial_rows = len(df)
    stats: Dict[str, Any] = {
        "initial_rows": initial_rows,
        "duplicates_removed": 0,
        "nulls_handled": 0,
        "invalid_prices_removed": 0,
        "outliers_adjusted": 0,
    }
    
    df = standardize_column_names(df)
    
    # Validate required columns exist
    missing_req = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_req:
        raise ValueError(f"Missing mandatory columns: {missing_req}. Available: {list(df.columns)}")
        
    # 1. Deduplication
    dedup_cols = ["date", "market", "commodity"] if "commodity" in df.columns else ["date", "market"]
    duplicates = df.duplicated(subset=dedup_cols, keep="first").sum()
    df = df.drop_duplicates(subset=dedup_cols, keep="first")
    stats["duplicates_removed"] = int(duplicates)
    
    # 2. Date parsing
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    null_dates = df["date"].isna().sum()
    if null_dates > 0:
        logger.warning("Dropping %d rows with unparseable dates", null_dates)
        df = df.dropna(subset=["date"])
        
    # 3. Numeric conversion
    numeric_cols = ["modal_price", "min_price", "max_price", "arrivals_qtl"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    # Handle missing modal prices: drop as target cannot be missing
    null_modal = df["modal_price"].isna().sum()
    if null_modal > 0:
        df = df.dropna(subset=["modal_price"])
        stats["nulls_handled"] += int(null_modal)
        
    # Handle missing arrivals: impute with market median
    if "arrivals_qtl" in df.columns:
        df["arrivals_qtl"] = df.groupby("market")["arrivals_qtl"].transform(
            lambda s: s.fillna(s.median() if not s.median() != s.median() else 1000)
        )
        df["arrivals_qtl"] = df["arrivals_qtl"].fillna(1000).clip(lower=0)
    else:
        df["arrivals_qtl"] = 1000.0
        
    # Impute min_price and max_price if missing
    if "min_price" in df.columns:
        df["min_price"] = df["min_price"].fillna(df["modal_price"] * 0.90)
    else:
        df["min_price"] = df["modal_price"] * 0.90
        
    if "max_price" in df.columns:
        df["max_price"] = df["max_price"].fillna(df["modal_price"] * 1.10)
    else:
        df["max_price"] = df["modal_price"] * 1.10
        
    # 4. Enforce price validity logic:
    # modal_price > 0, min_price <= modal_price <= max_price
    # APMC realistic bound for Tomato: ₹200 to ₹12000 per quintal
    valid_mask = (df["modal_price"] >= 200.0) & (df["modal_price"] <= 12000.0)
    invalid_count = (~valid_mask).sum()
    df = df[valid_mask].copy()
    stats["invalid_prices_removed"] = int(invalid_count)
    
    # Correct swapped min/max prices
    swap_mask = df["min_price"] > df["modal_price"]
    df.loc[swap_mask, "min_price"] = df.loc[swap_mask, "modal_price"] * 0.90
    
    swap_max_mask = df["max_price"] < df["modal_price"]
    df.loc[swap_max_mask, "max_price"] = df.loc[swap_max_mask, "modal_price"] * 1.10
    
    # Standardize string fields
    df["market"] = df["market"].astype(str).str.strip().str.title()
    df["district"] = df["district"].astype(str).str.strip().str.title()
    if "commodity" in df.columns:
        df["commodity"] = df["commodity"].astype(str).str.strip().str.title()
    else:
        df["commodity"] = "Tomato"
        
    df["price_unit"] = "INR/Quintal"
    
    # 5. Sort chronologically by market and date
    df = df.sort_values(by=["market", "date"]).reset_index(drop=True)
    
    stats["final_rows"] = len(df)
    stats["markets_count"] = df["market"].nunique()
    stats["date_min"] = df["date"].min().strftime("%Y-%m-%d")
    stats["date_max"] = df["date"].max().strftime("%Y-%m-%d")
    stats["mean_modal_price"] = round(float(df["modal_price"].mean()), 2)
    stats["median_modal_price"] = round(float(df["modal_price"].median()), 2)
    
    logger.info("Preprocessing complete: %d -> %d rows across %d markets.",
                initial_rows, len(df), stats["markets_count"])
    return df, stats


def preprocess_dataset(
    raw_path: str = "data/raw/tomato_karnataka_raw.csv",
    processed_dir: str = "data/processed",
    crop: str = "Tomato"
) -> Tuple[str, Dict[str, Any]]:
    """
    Full pipeline to clean raw data and write processed dataset.
    """
    os.makedirs(processed_dir, exist_ok=True)
    processed_file = os.path.join(processed_dir, f"clean_{crop.lower()}_data.csv")
    stats_file = os.path.join(processed_dir, f"clean_{crop.lower()}_stats.json")
    
    raw_df = load_raw_data(raw_path)
    clean_df, stats = clean_and_validate_data(raw_df)
    
    clean_df.to_csv(processed_file, index=False)
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    logger.info("Processed dataset saved to %s", processed_file)
    return processed_file, stats


if __name__ == "__main__":
    path, stats = preprocess_dataset("../data/raw/tomato_karnataka_raw.csv", "../data/processed")
    print(f"Preprocessed data saved to: {path}")
    print("Summary Stats:", stats)
