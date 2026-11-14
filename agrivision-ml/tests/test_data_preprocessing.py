"""
test_data_preprocessing.py
--------------------------
Unit tests for data cleaning, deduplication, price ordering, and schema validation.
"""

import pytest
import pandas as pd
import numpy as np
from src.data_preprocessing import (
    standardize_column_names,
    clean_and_validate_data,
    REQUIRED_COLUMNS
)


def test_standardize_column_names():
    raw_df = pd.DataFrame({
        "Arrival_Date": ["2025-01-01"],
        "Market Name": ["Kolar"],
        "District Name": ["Kolar"],
        "Modal_Price": [1500],
        "Arrivals (Tonnes)": [100]
    })
    standardized = standardize_column_names(raw_df)
    assert "date" in standardized.columns
    assert "market" in standardized.columns
    assert "district" in standardized.columns
    assert "modal_price" in standardized.columns
    assert "arrivals_qtl" in standardized.columns
    assert standardized["arrivals_qtl"].iloc[0] == 1000 # 100 tonnes * 10


def test_clean_and_validate_duplicates_and_invalid_prices():
    test_data = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"],
        "market": ["Kolar", "Kolar", "Kolar", "Kolar", "Kolar"],
        "district": ["Kolar", "Kolar", "Kolar", "Kolar", "Kolar"],
        "commodity": ["Tomato", "Tomato", "Tomato", "Tomato", "Tomato"],
        "min_price": [1200, 1200, 2500, 1000, 50],       # row 2 has min > modal, row 4 has astronomical/low
        "max_price": [1800, 1800, 1800, 2200, 60],
        "modal_price": [1500, 1500, 1600, 1700, 50],     # row 4 is < 200 invalid price
        "arrivals_qtl": [2000, 2000, 1500, 1800, 100]
    })
    
    clean_df, stats = clean_and_validate_data(test_data)
    
    # 1 duplicate removed, 1 invalid price dropped (50 < 200)
    assert stats["duplicates_removed"] == 1
    assert stats["invalid_prices_removed"] == 1
    assert len(clean_df) == 3
    
    # Ensure min <= modal <= max
    for _, row in clean_df.iterrows():
        assert row["min_price"] <= row["modal_price"]
        assert row["modal_price"] <= row["max_price"]
        assert row["modal_price"] >= 200.0


def test_missing_mandatory_columns():
    invalid_df = pd.DataFrame({"market": ["Kolar"], "date": ["2025-01-01"]})
    with pytest.raises(ValueError) as excinfo:
        clean_and_validate_data(invalid_df)
    assert "Missing mandatory columns" in str(excinfo.value)
