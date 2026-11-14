"""
ml_client.py
============
Server-side utility that proxies calls from the Django backend to the
AgriVision ML Flask API (default: http://127.0.0.1:5000).

All functions return None gracefully when the Flask service is offline so
Django views can fall back to the demo formula without crashing.

Base URL is read from the ML_API_URL environment variable (or Django
settings.ML_API_URL), defaulting to http://127.0.0.1:5000.

UNIT CONVENTION:
  Flask API → prices in ₹/quintal (100 kg)
  Django / UI → prices in ₹/kg
  Conversion helper: _quintal_to_kg()
"""

import os
import logging
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


_TIMEOUT = 6  # seconds – tight enough not to block Django request cycle


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
        r = requests.get(f"{_base_url()}/health", timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("ML API /health unreachable: %s", exc)
        return None


def call_ml_predict_price(
    crop: str,
    market: str,
    district: str,
    prediction_date: str | None = None,
) -> dict | None:
    """
    POST /predict-price

    Returns a dict with keys (prices converted to ₹/kg):
        predicted_modal_price_per_kg, prediction_interval_per_kg,
        model_type, model_version, uncertainty_disclaimer, unit,
        raw_quintal_price  (original ₹/quintal for reference)
    Returns None on network/model error.
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
        r = requests.post(f"{_base_url()}/predict-price", json=payload, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()

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
            "model_type": data.get("model_type", "unknown"),
            "model_version": data.get("model_version", "1.0.0"),
            "uncertainty_disclaimer": data.get(
                "uncertainty_disclaimer",
                "Agricultural prices are inherently volatile. Treat prediction as a guide only.",
            ),
            "prediction_date": data.get("prediction_date", prediction_date),
            "crop": data.get("crop", crop),
            "market": data.get("market", market),
            "district": data.get("district", district),
        }
    except Exception as exc:
        logger.warning("ML API /predict-price failed: %s", exc)
        return None


def call_ml_forecast_demand(
    crop: str,
    market: str = "Kolar",
    district: str = "Kolar",
) -> dict | None:
    """
    POST /forecast-demand

    Returns a dict with keys:
        trend_label, trend_direction, confidence_pct, supply_proxy_note,
        methodology_note
    Returns None on error.
    """
    payload = {"crop": crop, "market": market, "district": district}
    try:
        r = requests.post(f"{_base_url()}/forecast-demand", json=payload, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("ML API /forecast-demand failed: %s", exc)
        return None


def call_ml_explain_price(
    crop: str,
    market: str,
    district: str,
    prediction_date: str | None = None,
) -> dict | None:
    """
    POST /explain-price

    Returns a dict with keys:
        narrative_explanation, feature_contributions (list),
        shap_available, model_type
    Returns None on error.
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
    except Exception as exc:
        logger.warning("ML API /explain-price failed: %s", exc)
        return None


def call_ml_metrics() -> dict | None:
    """
    GET /model-metrics

    Returns the full metrics dict from the Flask API.
    Returns None on error.
    """
    try:
        r = requests.get(f"{_base_url()}/model-metrics", timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("ML API /model-metrics failed: %s", exc)
        return None


def call_ml_markets() -> list | None:
    """
    GET /markets

    Returns list of supported markets.
    Returns None on error.
    """
    try:
        r = requests.get(f"{_base_url()}/markets", timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return data.get("markets", [])
    except Exception as exc:
        logger.warning("ML API /markets failed: %s", exc)
        return None
