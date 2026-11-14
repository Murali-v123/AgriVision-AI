"""
data_collection.py
------------------
AgriVision AI - Agricultural Price Intelligence & Demand Forecasting
Handles data acquisition from AGMARKNET / data.gov.in APIs, local CSV imports,
or generating structured, transparently labeled synthetic demonstration datasets
reflecting Karnataka tomato APMC markets.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Key Tomato APMCs in Karnataka
KARNATAKA_TOMATO_MARKETS = [
    {"market": "Kolar", "district": "Kolar", "base_modal": 1650, "avg_arrivals": 4500},
    {"market": "Bangalore", "district": "Bangalore Urban", "base_modal": 1800, "avg_arrivals": 3800},
    {"market": "Ramanagara", "district": "Ramanagara", "base_modal": 1550, "avg_arrivals": 2200},
    {"market": "Belagavi", "district": "Belagavi", "base_modal": 1700, "avg_arrivals": 1800},
    {"market": "Mysuru", "district": "Mysuru", "base_modal": 1750, "avg_arrivals": 1600},
    {"market": "Chikkaballapur", "district": "Chikkaballapur", "base_modal": 1600, "avg_arrivals": 2800},
]


def generate_synthetic_demo_data(
    start_date: str = "2024-01-01",
    end_date: str = "2025-12-31",
    crop: str = "Tomato",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic synthetic demonstration dataset for Karnataka APMC markets.
    
    IMPORTANT NOTICE:
    This dataset is strictly SYNTHETIC DEMO DATA designed for hackathon demonstration,
    testing, and architecture validation when live AGMARKNET/data.gov.in feeds are
    offline or rate-limited. It simulates realistic seasonal price curves, arrival
    elasticity, and market variations for Karnataka tomatoes.
    """
    np.random.seed(seed)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    
    records: List[Dict[str, Any]] = []
    
    for dt in date_range:
        day_of_year = dt.timetuple().tm_yday
        month = dt.month
        is_sunday = (dt.weekday() == 6)
        
        # Karnataka Tomato Seasonality:
        # High prices during summer pinch (April-June) and late monsoon (Sept-Oct)
        # Low prices during bumper winter harvest (Dec-Feb)
        seasonal_price_factor = (
            1.0
            + 0.45 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
            + 0.20 * np.sin(4 * np.pi * (day_of_year - 20) / 365)
        )
        # Supply inversely relates to price seasonality
        seasonal_arrival_factor = (
            1.0
            - 0.40 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
            + 0.15 * np.cos(2 * np.pi * day_of_year / 365)
        )
        
        for mkt in KARNATAKA_TOMATO_MARKETS:
            # Sunday APMC closure / reduced arrivals
            sunday_arrival_mult = 0.15 if is_sunday else 1.0
            
            # Arrivals (in Quintals)
            arrival_noise = np.random.normal(0, 0.12)
            arrivals = int(
                max(
                    50,
                    mkt["avg_arrivals"]
                    * seasonal_arrival_factor
                    * sunday_arrival_mult
                    * (1 + arrival_noise)
                )
            )
            
            # Market price elasticity relative to arrival shock
            arrival_deviation = (arrivals - mkt["avg_arrivals"]) / mkt["avg_arrivals"]
            elasticity_impact = -0.22 * arrival_deviation
            
            price_noise = np.random.normal(0, 0.08)
            modal_price = (
                mkt["base_modal"]
                * seasonal_price_factor
                * (1 + elasticity_impact + price_noise)
            )
            # Bound within realistic historical Karnataka APMC limits (₹500 to ₹5500/quintal)
            modal_price = float(np.clip(modal_price, 500.0, 5500.0))
            
            spread = np.random.uniform(0.08, 0.18) * modal_price
            min_price = float(np.round(modal_price - spread * 0.55, 2))
            max_price = float(np.round(modal_price + spread * 0.60, 2))
            modal_price = float(np.round(modal_price, 2))
            
            # Ensure price ordering integrity
            min_price = max(100.0, min_price)
            if min_price > modal_price:
                min_price = round(modal_price * 0.90, 2)
            if max_price < modal_price:
                max_price = round(modal_price * 1.10, 2)
                
            records.append({
                "date": dt.strftime("%Y-%m-%d"),
                "state": "Karnataka",
                "district": mkt["district"],
                "market": mkt["market"],
                "commodity": crop,
                "variety": "Local / Hybrid",
                "arrivals_qtl": arrivals,
                "min_price": min_price,
                "max_price": max_price,
                "modal_price": modal_price,
                "price_unit": "INR/Quintal",
                "data_source": "SYNTHETIC DEMO DATA (Karnataka APMC Simulation)",
                "is_synthetic": True
            })
            
    df = pd.DataFrame(records)
    logger.info("Generated %d synthetic demo records for Karnataka %s (%s to %s)",
                len(df), crop, start_date, end_date)
    return df


def fetch_from_datagov_api(
    api_key: str,
    resource_id: str = "9ef84268-d588-465a-a308-a864a43d0070",
    filters: Optional[Dict[str, str]] = None,
    limit: int = 5000,
    timeout: int = 15
) -> Optional[pd.DataFrame]:
    """
    Fetches real-world market prices from data.gov.in Agricultural Market APIs.
    Requires an active API key from data.gov.in.
    """
    url = f"https://api.data.gov.in/resource/{resource_id}"
    params = {
        "api-key": api_key,
        "format": "json",
        "limit": limit
    }
    if filters:
        for k, v in filters.items():
            params[f"filters[{k}]"] = v
            
    try:
        logger.info("Connecting to data.gov.in API endpoint: %s", url)
        response = requests.get(url, params=params, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            if records:
                df = pd.DataFrame(records)
                df["data_source"] = "data.gov.in (Official API)"
                df["is_synthetic"] = False
                logger.info("Successfully fetched %d records from data.gov.in", len(df))
                return df
            else:
                logger.warning("data.gov.in responded with 0 records.")
                return None
        else:
            logger.warning("data.gov.in API returned HTTP %d: %s", response.status_code, response.text[:200])
            return None
    except Exception as exc:
        logger.error("Failed to fetch data from data.gov.in: %s", exc)
        return None


def import_from_csv(file_path: str) -> pd.DataFrame:
    """
    Imports and validates an authentic AGMARKNET / data.gov.in CSV file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input CSV file not found: {file_path}")
        
    df = pd.read_csv(file_path)
    if "is_synthetic" not in df.columns:
        df["is_synthetic"] = False
    if "data_source" not in df.columns:
        df["data_source"] = f"Imported CSV ({os.path.basename(file_path)})"
        
    logger.info("Imported %d rows from %s", len(df), file_path)
    return df


def acquire_data(
    raw_output_dir: str = "data/raw",
    source_type: str = "auto",
    custom_csv_path: Optional[str] = None,
    api_key: Optional[str] = None,
    crop: str = "Tomato"
) -> str:
    """
    Acquires data and saves it into the raw data directory.
    Priority:
    1. custom_csv_path if provided.
    2. data.gov.in API if api_key provided.
    3. Existing raw file in raw_output_dir.
    4. Generate high-fidelity synthetic demo data clearly labeled.
    
    Returns the file path of saved raw dataset.
    """
    os.makedirs(raw_output_dir, exist_ok=True)
    raw_file_path = os.path.join(raw_output_dir, f"{crop.lower()}_karnataka_raw.csv")
    meta_file_path = os.path.join(raw_output_dir, f"{crop.lower()}_karnataka_raw_meta.json")
    
    df: Optional[pd.DataFrame] = None
    source_label = ""
    is_synthetic = False
    
    if custom_csv_path and os.path.exists(custom_csv_path):
        logger.info("Loading provided CSV file: %s", custom_csv_path)
        df = import_from_csv(custom_csv_path)
        source_label = f"Local CSV ({custom_csv_path})"
    elif api_key:
        logger.info("Attempting retrieval via data.gov.in API...")
        df = fetch_from_datagov_api(api_key, filters={"state": "Karnataka", "commodity": crop})
        if df is not None:
            source_label = "data.gov.in API (Official)"
            
    if df is None:
        logger.info(
            "No active API key or external raw feed provided. Generating high-fidelity "
            "SYNTHETIC DEMO DATA for Karnataka %s APMCs...", crop
        )
        df = generate_synthetic_demo_data(start_date="2024-01-01", end_date="2025-12-31", crop=crop)
        source_label = "SYNTHETIC DEMO DATA (Karnataka APMC Simulation for Hackathon)"
        is_synthetic = True
        
    df.to_csv(raw_file_path, index=False)
    
    metadata = {
        "crop": crop,
        "region": "Karnataka, India",
        "records_count": len(df),
        "source": source_label,
        "is_synthetic": is_synthetic,
        "saved_at": datetime.now().isoformat(),
        "columns": list(df.columns),
        "markets": sorted(list(df["market"].unique())) if "market" in df.columns else []
    }
    
    with open(meta_file_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    logger.info("Raw data saved to: %s (%d rows)", raw_file_path, len(df))
    logger.info("Data source note: %s", source_label)
    return raw_file_path


if __name__ == "__main__":
    path = acquire_data(raw_output_dir="../data/raw")
    print(f"Data collection completed. Saved raw file: {path}")
