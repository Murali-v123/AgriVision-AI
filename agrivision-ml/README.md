# AgriVision AI – Agricultural Price Intelligence & Demand Forecasting
**Build Beyond'26 | BMS College of Engineering**  
**Role:** Member 2 – AI & Data Science  
**Target Crop:** Tomato (*Solanum lycopersicum*) – Karnataka APMC Mandis (Expandable architecture)

---

## 1. Project Overview & Context

AgriVision AI is an intelligent agricultural marketplace designed to protect smallholder farmers and agricultural traders in Karnataka from extreme market volatility, distress selling, and opaque commission-agent pricing.

As **Member 2 (AI & Data Science)**, this repository delivers:
1. **Agricultural Price Prediction:** Multi-model benchmarking (Historical Baseline, Random Forest Regressor, Gradient Boosting) using strictly chronological splits and empirical prediction intervals (80% confidence bands).
2. **Crop Demand Forecasting:** Mandi arrival velocity and price elasticity proxy modeling to classify 7-day forward market absorption pressure (`Increasing`, `Decreasing`, `Stable`).
3. **Explainable AI (XAI):** TreeSHAP and feature importance attribution synthesized into verifiable natural language explanations for farmers and traders.
4. **Performance Evaluation & Verification:** Rigorous MAE, RMSE, safe MAPE, and R² metrics documented in machine-readable JSON and human-readable Markdown reports.
5. **REST API Interface:** Production-ready Flask microservice for seamless integration with Member 3 & Member 4's Django REST Framework backend.

---

## 2. Architecture & Technology Stack

- **Python 3.11+ / 3.14**
- **Data Engineering:** `pandas`, `numpy`
- **Machine Learning:** `scikit-learn` (Random Forest, Gradient Boosting, OneHotEncoder)
- **Explainability:** `shap` (TreeSHAP) with fallback attribution synthesis
- **Model Persistence:** `joblib`
- **Visualization:** `matplotlib`, `seaborn`
- **API Server:** `Flask` with CORS headers
- **Testing:** `pytest`

---

## 3. Project Directory Structure

```text
agrivision-ml/
│
├── data/
│   ├── raw/                  # Raw APMC records & dataset provenance metadata
│   └── processed/            # Cleaned, validated, and normalized CSV datasets
│
├── models/                   # Serialized ML artifacts (.joblib) & metrics JSON
│   ├── price_model.joblib
│   ├── price_preprocessor.joblib
│   ├── demand_model.joblib
│   ├── price_model_metrics.json
│   └── demand_metrics.json
│
├── notebooks/                # Jupyter exploration notebook for hackathon demo
│   └── agrivision_exploration.ipynb
│
├── outputs/
│   ├── graphs/               # High-resolution publication plots
│   │   ├── price_trends.png
│   │   ├── actual_vs_predicted.png
│   │   ├── model_comparison.png
│   │   ├── feature_importance.png
│   │   ├── demand_trend.png
│   │   └── forecast_uncertainty.png
│   └── reports/              # Model verification & evaluation reports
│       ├── evaluation_report.md
│       └── evaluation_report.json
│
├── src/
│   ├── __init__.py
│   ├── data_collection.py     # data.gov.in API / Agmarknet / demo data acquisition
│   ├── data_preprocessing.py  # Deduplication, date parsing, price validity checks
│   ├── feature_engineering.py # Lags, rolling windows, and leakage-free pipelines
│   ├── price_prediction.py    # Chronological training, benchmarking, uncertainty intervals
│   ├── demand_forecasting.py  # Mandi supply proxy classification & trend forecast
│   ├── explainability.py      # TreeSHAP & factual natural language explanations
│   ├── evaluation.py          # Trend visualization & report generator
│   └── api.py                 # Production Flask REST API endpoints
│
├── tests/                    # Automated unit & integration tests
│   ├── test_data_preprocessing.py
│   ├── test_feature_engineering.py
│   ├── test_price_prediction.py
│   ├── test_demand_forecasting.py
│   └── test_api.py
│
├── requirements.txt          # Python dependencies
├── README.md                 # Complete documentation & setup instructions
├── main.py                   # End-to-end pipeline execution entrypoint
└── .gitignore
```

---

## 4. Setup & Execution Instructions (Windows PowerShell & CMD)

### Step 1: Open PowerShell / Terminal
```powershell
cd c:\Users\madhu\Downloads\ML_DATA\agrivision-ml
```

### Step 2: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Execute the Full Pipeline
Run `main.py` to acquire data, preprocess, engineer features, train models, generate graphs, and build evaluation reports:
```powershell
python main.py
```

### Step 4: Run Automated Tests
```powershell
python -m pytest tests/ -v
```

### Step 5: Start the Flask API Service
```powershell
python src/api.py
```
The API server will start at `http://127.0.0.1:5000`.

---

## 5. API Reference & Contract Specification

### 1. Health Check
- **Endpoint:** `GET /health`
- **Response:**
```json
{
  "service": "AgriVision AI - Machine Learning Engine",
  "status": "healthy",
  "version": "1.0.0",
  "supported_crops": ["Tomato"],
  "supported_markets": ["Bangalore", "Belagavi", "Chikkaballapur", "Kolar", "Mysuru", "Ramanagara"],
  "models_loaded": {
    "price_prediction_model": true,
    "demand_forecasting_model": true,
    "explainability_engine": true
  }
}
```

### 2. Predict Price (with Uncertainty Interval)
- **Endpoint:** `POST /predict-price`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "crop": "Tomato",
  "market": "Kolar",
  "district": "Kolar",
  "date": "2026-03-25",
  "confidence_level": 0.80
}
```
- **Response:**
```json
{
  "crop": "Tomato",
  "market": "Kolar",
  "district": "Kolar",
  "prediction_date": "2026-03-25",
  "predicted_modal_price": 2045.50,
  "unit": "INR/Quintal",
  "model_version": "1.0.0",
  "model_type": "RandomForestRegressor",
  "prediction_interval": {
    "confidence_level": "80%",
    "lower_bound": 1890.20,
    "upper_bound": 2210.40
  },
  "uncertainty_disclaimer": "Agricultural prices are subject to weather events, fuel costs, and supply surges. This interval represents model confidence based on historical APMC variance, not absolute certainty."
}
```

### 3. Forecast Demand Pressure Trend
- **Endpoint:** `POST /forecast-demand`
- **Request Body:**
```json
{
  "crop": "Tomato",
  "market": "Kolar",
  "district": "Kolar",
  "date": "2026-03-25"
}
```
- **Response:**
```json
{
  "crop": "Tomato",
  "market": "Kolar",
  "district": "Kolar",
  "forecast_date": "2026-03-25",
  "forecast_horizon": "7-day forward window",
  "demand_trend": "Increasing",
  "confidence_score": 0.84,
  "confidence_percentage": "84%",
  "economic_interpretation": "Market absorption capacity is projected to expand over the next 7 days. Wholesale buyers and food processors are absorbing incoming stock rapidly.",
  "proxy_disclaimer": "Agricultural Market Proxy Notice: APMC mandi arrivals represent physical wholesale market supply volume, NOT final retail consumer demand..."
}
```

### 4. Explain Price Prediction (Explainable AI)
- **Endpoint:** `POST /explain-price`
- **Request Body:**
```json
{
  "crop": "Tomato",
  "market": "Kolar",
  "district": "Kolar",
  "date": "2026-03-25"
}
```
- **Response:**
```json
{
  "predicted_modal_price": 2045.50,
  "unit": "INR/Quintal",
  "natural_language_explanation": "Recommended modal price of ₹2045.50/quintal for Kolar is driven by: 1) Recent 7-day price momentum shows an upward surge (+6.2%), indicating strong buying demand in Kolar. 2) Summer / Zaid season (March-June) typically causes localized crop heat stress and reduced field yields... 3) Kolar APMC functions as a primary terminal aggregation hub... 4) Arrival flow (3120 qtl) is tracking near the normal weekly baseline.",
  "top_influencing_features": [
    {"feature": "modal_price_lag_1", "shap_impact": 180.4, "direction": "upward"},
    {"feature": "price_rolling_mean_7", "shap_impact": 94.2, "direction": "upward"},
    {"feature": "season_Summer", "shap_impact": 42.1, "direction": "upward"}
  ]
}
```

### 5. Model Metrics
- **Endpoint:** `GET /model-metrics`

### 6. Supported Markets
- **Endpoint:** `GET /markets`

---

## 6. Integration Guide for Member 3 & Member 4 (Django Backend)

Member 3 & Member 4 can integrate directly using standard Python `requests` or Django REST Framework viewsets:

### Python / Django Example Integration:
```python
import requests

ML_SERVICE_URL = "http://127.0.0.1:5000"

def get_tomato_price_intelligence(market_name, query_date):
    """Fetches ML prediction and explanation from AgriVision ML microservice."""
    payload = {
        "crop": "Tomato",
        "market": market_name,
        "date": query_date,
        "confidence_level": 0.80
    }
    try:
        price_resp = requests.post(f"{ML_SERVICE_URL}/predict-price", json=payload, timeout=5)
        demand_resp = requests.post(f"{ML_SERVICE_URL}/forecast-demand", json=payload, timeout=5)
        explain_resp = requests.post(f"{ML_SERVICE_URL}/explain-price", json=payload, timeout=5)

        return {
            "price_data": price_resp.json() if price_resp.status_code == 200 else None,
            "demand_data": demand_resp.json() if demand_resp.status_code == 200 else None,
            "explanation": explain_resp.json().get("natural_language_explanation") if explain_resp.status_code == 200 else None
        }
    except requests.exceptions.RequestException as err:
        return {"error": f"ML Service unavailable: {str(err)}"}
```

---

## 7. Data Provenance & Real-World Limitations

1. **Synthetic Demo Data Disclosure:**  
   When live AGMARKNET or data.gov.in API keys are unavailable during development/hackathons, the pipeline generates a transparently flagged `SYNTHETIC DEMO DATA (Karnataka APMC Simulation)` dataset. It simulates realistic Karnataka tomato seasonality (summer price squeeze, winter bumper drop, Sunday mandi closures, and arrival elasticity).
2. **Wholesale Arrivals as Supply Proxy:**  
   Mandi records exclusively log wholesale truck dispatches. Household retail consumption is unobserved; therefore, demand trend is calculated as a market clearance and price absorption proxy.
3. **No False Future Certainty:**  
   Agricultural commodities are vulnerable to monsoon anomalies and logistics disruptions. The model returns empirical prediction intervals and explicit uncertainty notices rather than claiming absolute certainty.
