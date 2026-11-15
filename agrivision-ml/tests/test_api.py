"""
test_api.py
-----------
Integration and contract tests for the Flask REST API endpoints,
validating schemas, uncertainty ranges, and error handling.
"""

import json
import pytest
from src.api import app, load_artifacts


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_root_index_endpoint(client):
    # HTML response by default
    res = client.get("/")
    assert res.status_code == 200
    assert b"AgriVision AI" in res.data

    # JSON response when Accept: application/json
    res_json = client.get("/", headers={"Accept": "application/json"})
    assert res_json.status_code == 200
    assert "endpoints" in res_json.get_json()


def test_favicon_endpoint(client):
    res = client.get("/favicon.ico")
    assert res.status_code == 204


def test_ui_routing(client):
    res = client.get("/ui")
    assert res.status_code in [302, 301]
    res_page = client.get("/ui/farmer/prices.html")
    assert res_page.status_code == 200
    assert b"Market Price Intelligence" in res_page.data


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code in [200, 503]
    data = res.get_json()
    assert "status" in data
    assert "version" in data
    assert data["service"] == "AgriVision AI - Machine Learning Engine"


def test_markets_endpoint(client):
    res = client.get("/markets")
    assert res.status_code == 200
    data = res.get_json()
    assert "supported_crops" in data
    assert "Tomato" in data["supported_crops"]
    assert "markets" in data


def test_predict_price_success(client):
    payload = {
        "crop": "Tomato",
        "market": "Kolar",
        "district": "Kolar",
        "date": "2026-03-25",
        "modal_price_lag_1": 1750.0,
        "arrivals_lag_1": 3500.0,
        "confidence_level": 0.80
    }
    res = client.post("/predict-price", json=payload)
    if res.status_code == 503:
        pytest.skip("Models not trained/loaded yet; skipping live prediction test.")
        
    assert res.status_code == 200
    data = res.get_json()
    assert data["crop"] == "Tomato"
    assert data["market"] == "Kolar"
    assert "predicted_modal_price" in data
    assert "prediction_interval" in data
    interval = data["prediction_interval"]
    assert interval["lower_bound"] <= data["predicted_modal_price"]
    assert data["predicted_modal_price"] <= interval["upper_bound"]
    assert "uncertainty_disclaimer" in data


def test_predict_price_missing_market(client):
    payload = {
        "crop": "Tomato",
        "date": "2026-03-25"
    }
    res = client.post("/predict-price", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
    assert "market" in data["error"]


def test_predict_price_missing_json(client):
    res = client.post("/predict-price", data="not json", content_type="text/plain")
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data


def test_forecast_demand_endpoint(client):
    payload = {
        "crop": "Tomato",
        "market": "Kolar",
        "district": "Kolar",
        "date": "2026-03-25"
    }
    res = client.post("/forecast-demand", json=payload)
    if res.status_code == 503:
        pytest.skip("Demand model not loaded yet; skipping.")
        
    assert res.status_code == 200
    data = res.get_json()
    assert data["demand_trend"] in ["Increasing", "Decreasing", "Stable"]
    assert "confidence_score" in data
    assert "proxy_disclaimer" in data


def test_explain_price_endpoint(client):
    payload = {
        "crop": "Tomato",
        "market": "Kolar",
        "district": "Kolar",
        "date": "2026-03-25",
        "modal_price_lag_1": 1800.0,
        "modal_price_lag_7": 1650.0
    }
    res = client.post("/explain-price", json=payload)
    if res.status_code == 503:
        pytest.skip("Models not loaded yet; skipping.")
        
    assert res.status_code == 200
    data = res.get_json()
    assert "natural_language_explanation" in data
    assert "top_influencing_features" in data
    assert "domain_context" in data
    assert "price_trend_analysis" in data["domain_context"]
