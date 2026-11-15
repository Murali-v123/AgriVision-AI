"""
ml_client.py
============
Server-side utility that proxies calls from the Django backend to the
AgriVision ML engine. Supports both HTTP requests (if microservice is running
separately) AND seamless in-process fallback (if running in Unified Single-Server mode).

All functions return None gracefully when the ML service is completely unavailable,
so Django views can fall back to the demo formula without crashing.

UNIT CONVENTION:
  Flask API → prices in ₹/quintal (100 kg)
  Django / UI → prices in ₹/kg
  Conversion helper: _quintal_to_kg()
"""

import os
import sys
import logging
from pathlib import Path
from datetime import date as _date

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Base URL resolution
# ---------------------------------------------------------------------------
_DEFAULT_ML_URL = "http://127.0.0.1:5000"


def _base_url() -> str:
    """Return the ML API base URL from settings or environment."""
    return getattr(settings, "ML_API_URL", os.environ.get("ML_API_URL", _DEFAULT_ML_URL)).rstrip("/")


_TIMEOUT = 2  # Tight timeout to quickly fall back to in-process execution

# ---------------------------------------------------------------------------
# In-Process ML Fallback (Unified Single-Server Mode)
# ---------------------------------------------------------------------------
_in_process_ml_app = None


def _get_in_process_ml_app():
    global _in_process_ml_app
    if _in_process_ml_app is None:
        try:
            ml_dir = str(Path(settings.BASE_DIR).parent / "agrivision-ml")
            if ml_dir not in sys.path:
                sys.path.insert(0, ml_dir)
            from src.api import app, load_artifacts
            load_artifacts()
            _in_process_ml_app = app
        except Exception as exc:
            logger.warning("Could not initialize in-process ML app: %s", exc)
    return _in_process_ml_app


def _call_in_process(endpoint: str, method: str = "POST", payload: dict | None = None) -> dict | None:
    app = _get_in_process_ml_app()
    if not app:
        return None
    try:
        with app.test_client() as client:
            if method == "POST":
                resp = client.post(endpoint, json=payload or {})
            else:
                resp = client.get(endpoint)
            if resp.status_code == 200:
                return resp.json
    except Exception as exc:
        logger.warning("In-process ML call %s failed: %s", endpoint, exc)
    return None


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def _quintal_to_kg(price_per_quintal: float) -> float:
    """Convert ₹/quintal → ₹/kg (1 quintal = 100 kg)."""
    return round(price_per_quintal / 100.0, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_ml_health() -> dict | None:
    """GET /health — ping the ML service."""
    try:
        r = requests.get(f"{_base_url()}/health", timeout=1)
        r.raise_for_status()
        return r.json()
    except Exception:
        return _call_in_process("/health", "GET")


def call_ml_predict_price(
    crop: str,
    market: str,
    district: str,
    prediction_date: str | None = None,
) -> dict | None:
    """
    POST /predict-price
    Returns a dict with prices converted to ₹/kg.
    """
    if prediction_date is None:
        prediction_date = _date.today().isoformat()

    payload = {
        "crop": crop,
        "market": market,
        "district": district,
        "date": prediction_date,
    }
    data = None
    try:
        r = requests.post(f"{_base_url()}/predict-price", json=payload, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception:
        data = _call_in_process("/predict-price", "POST", payload)

    if not data:
        return None

    raw_q = data.get("predicted_modal_price", 0)
    interval_q = data.get("prediction_interval", {})

    return {
        "raw_quintal_price": raw_q,
        "predicted_modal_price_per_kg": _quintal_to_kg(raw_q),
        "prediction_interval_per_kg": {
            "lower_bound": _quintal_to_kg(interval_q.get("lower_bound", raw_q * 0.75)),
            "upper_bound": _quintal_to_kg(interval_q.get("upper_bound", raw_q * 1.25)),
            "confidence_level": interval_q.get("confidence_level", "80%"),
        },
        "model_type": data.get("model_type", "GradientBoostingRegressor"),
        "model_version": data.get("model_version", "1.0.0"),
        "uncertainty_disclaimer": data.get(
            "uncertainty_disclaimer",
            "Agricultural prices vary by weather, fuel costs, and arrivals.",
        ),
        "unit": "INR/kg",
        "market": market,
        "district": district,
        "crop": crop,
        "prediction_date": prediction_date,
    }


def call_ml_forecast_demand(
    crop: str,
    market: str,
    district: str,
    forecast_date: str | None = None,
) -> dict | None:
    """
    POST /forecast-demand
    """
    if forecast_date is None:
        forecast_date = _date.today().isoformat()

    payload = {
        "crop": crop,
        "market": market,
        "district": district,
        "date": forecast_date,
    }
    data = None
    try:
        r = requests.post(f"{_base_url()}/forecast-demand", json=payload, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception:
        data = _call_in_process("/forecast-demand", "POST", payload)

    if not data:
        return None

    probs = data.get("probabilities", {})
    return {
        "trend_label": data.get("demand_trend", "Stable"),
        "trend_direction": data.get("demand_trend", "Stable").lower(),
        "confidence_pct": round(data.get("confidence", 0.5) * 100),
        "probabilities": {k: round(v * 100, 1) for k, v in probs.items()},
        "economic_interpretation": data.get("economic_interpretation", ""),
        "supply_proxy_note": data.get(
            "proxy_disclaimer",
            "Arrivals-based proxy. Not a direct consumer demand measurement.",
        ),
        "methodology_note": data.get("methodology_note", ""),
        "model_type": data.get("model_type", "RandomForestClassifier"),
        "market": market,
        "district": district,
        "crop": crop,
        "forecast_date": forecast_date,
    }


def call_ml_explain_price(
    crop: str,
    market: str,
    district: str,
    prediction_date: str | None = None,
) -> dict | None:
    """
    POST /explain-price
    """
    if prediction_date is None:
        prediction_date = _date.today().isoformat()

    payload = {
        "crop": crop,
        "market": market,
        "district": district,
        "date": prediction_date,
    }
    try:
        r = requests.post(f"{_base_url()}/explain-price", json=payload, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return _call_in_process("/explain-price", "POST", payload)


def call_ml_metrics() -> dict | None:
    """
    GET /model-metrics
    """
    try:
        r = requests.get(f"{_base_url()}/model-metrics", timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return _call_in_process("/model-metrics", "GET")


def call_ml_markets() -> list | None:
    """
    GET /markets
    """
    try:
        r = requests.get(f"{_base_url()}/markets", timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return data.get("markets", [])
    except Exception:
        data = _call_in_process("/markets", "GET")
        return data.get("markets", []) if data else None
