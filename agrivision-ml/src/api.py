"""
api.py
------
AgriVision AI - Agricultural Price Intelligence & Demand Forecasting
Production-ready Flask REST API serving price predictions, demand trend forecasts,
explainability attributions, and model metrics for Django backend integration.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify, send_from_directory, redirect
import pandas as pd
import numpy as np
import joblib

from src.feature_engineering import AgriFeaturePipeline, create_time_features
from src.price_prediction import PricePredictor
from src.demand_forecasting import DemandForecaster, DEMAND_LIMITATION_NOTICE
from src.explainability import AgriExplainer
from src.crop_disease import CropDiseasePredictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "clean_tomato_data.csv")
UI_DIR = os.path.dirname(BASE_DIR)

app = Flask(__name__)

# Global model state
price_predictor: Optional[PricePredictor] = None
demand_forecaster: Optional[DemandForecaster] = None
explainer: Optional[AgriExplainer] = None
crop_predictor: Optional[CropDiseasePredictor] = None
model_metrics: Dict[str, Any] = {}
recent_market_cache: Dict[str, Dict[str, Any]] = {}
supported_markets_list = []


def load_artifacts():
    """Loads trained models, preprocessors, and evaluation metrics at application boot."""
    global price_predictor, demand_forecaster, explainer, crop_predictor, model_metrics, recent_market_cache, supported_markets_list
    
    price_model_path = os.path.join(MODELS_DIR, "price_model.joblib")
    preproc_path = os.path.join(MODELS_DIR, "price_preprocessor.joblib")
    demand_model_path = os.path.join(MODELS_DIR, "demand_model.joblib")
    price_metrics_path = os.path.join(MODELS_DIR, "price_model_metrics.json")
    demand_metrics_path = os.path.join(MODELS_DIR, "demand_metrics.json")
    
    # Locate Crop Disease CNN model checkpoint
    candidate_paths = [
        os.path.join(MODELS_DIR, "crop_disease_model.pth"),
        os.path.join(MODELS_DIR, "crop_disease_model.pth.zip"),
        os.path.join(os.path.dirname(BASE_DIR), "crop_disease_model.pth"),
        os.path.join(os.path.dirname(BASE_DIR), "crop_disease_model.pth.zip"),
    ]
    crop_model_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if crop_model_path:
        try:
            crop_predictor = CropDiseasePredictor(crop_model_path)
            if crop_predictor.is_loaded():
                logger.info("Crop Disease / Quality CNN loaded successfully from %s", crop_model_path)
                model_metrics["crop_disease_cnn"] = {
                    "architecture": crop_predictor.architecture,
                    "classes_count": len(crop_predictor.class_names),
                    "input_size": [crop_predictor.image_size, crop_predictor.image_size],
                    "status": "active"
                }
            else:
                logger.warning("Crop CNN initialized in fallback mode.")
        except Exception as exc:
            logger.error("Failed to load Crop CNN model: %s", exc)
    else:
        logger.warning("Crop CNN model file not found in %s", MODELS_DIR)
    
    if os.path.exists(price_model_path) and os.path.exists(preproc_path):
        model = joblib.load(price_model_path)
        preproc = joblib.load(preproc_path)
        
        # Load residual std from metrics if available
        res_std = 120.0
        if os.path.exists(price_metrics_path):
            with open(price_metrics_path, "r", encoding="utf-8") as f:
                pm = json.load(f)
                res_std = pm.get("residual_std", 120.0)
                model_metrics["price_model"] = pm
                
        price_predictor = PricePredictor(
            model_name=type(model).__name__,
            model=model,
            preprocessor=preproc
        )
        price_predictor.residual_std = res_std
        price_predictor.feature_names = preproc.all_feature_names
        
        # Initialize Explainer
        explainer = AgriExplainer(model, preproc, preproc.all_feature_names)
        logger.info("Price prediction and explainability modules loaded successfully.")
    else:
        logger.warning("Price model artifacts not found at %s. Please run main.py first.", MODELS_DIR)
        
    if os.path.exists(demand_model_path):
        demand_forecaster = joblib.load(demand_model_path)
        logger.info("Demand forecasting model loaded successfully.")
    else:
        logger.warning("Demand model not found at %s", demand_model_path)
        
    if os.path.exists(demand_metrics_path):
        with open(demand_metrics_path, "r", encoding="utf-8") as f:
            model_metrics["demand_model"] = json.load(f)

    # Build market reference cache from clean data for easy inference defaults
    if os.path.exists(PROCESSED_DATA_PATH):
        try:
            df = pd.read_csv(PROCESSED_DATA_PATH)
            supported_markets_list = sorted(list(df["market"].unique()))
            for mkt in supported_markets_list:
                m_sub = df[df["market"] == mkt].sort_values("date")
                last_row = m_sub.iloc[-1]
                recent_market_cache[mkt] = {
                    "market": mkt,
                    "district": str(last_row.get("district", "Kolar")),
                    "last_modal_price": float(last_row.get("modal_price", 1600.0)),
                    "last_arrivals": float(last_row.get("arrivals_qtl", 3000.0)),
                    "rolling_mean_7": float(m_sub["modal_price"].tail(7).mean()),
                    "rolling_std_7": float(m_sub["modal_price"].tail(7).std() if len(m_sub) >= 7 else 100.0),
                    "rolling_arrivals_7": float(m_sub["arrivals_qtl"].tail(7).mean())
                }
            logger.info("Cached baseline context for %d Karnataka markets.", len(recent_market_cache))
        except Exception as e:
            logger.error("Failed to build market cache: %s", e)


# Enable CORS headers for Django integration
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/", methods=["GET"])
def index():
    """Root endpoint: Displays interactive API documentation dashboard or JSON spec."""
    if request.headers.get("Accept", "").startswith("application/json"):
        return jsonify({
            "service": "AgriVision AI - ML Microservice",
            "version": "1.0.0",
            "status": "online",
            "endpoints": {
                "GET /": "API Overview & Interactive Dashboard",
                "GET /health": "Health and loaded model status",
                "GET /markets": "List of supported APMC markets and districts",
                "GET /model-metrics": "Evaluation metrics (MAE, RMSE, MAPE, R²)",
                "POST /predict-price": "Predict crop modal price with uncertainty intervals",
                "POST /forecast-demand": "Forecast short-term demand pressure trend",
                "POST /explain-price": "Explain price predictions with TreeSHAP & domain insights",
                "POST /predict-disease": "EfficientNet-B2 CNN crop identity & quality assessment",
                "POST /assess-crop": "Alias for /predict-disease"
            }
        }), 200

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AgriVision AI - ML Service</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1e293b; padding: 30px; line-height: 1.6; }
    .container { max-width: 860px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    h1 { color: #166534; margin-top: 0; }
    .badge { background: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }
    .endpoint { margin: 15px 0; padding: 12px 16px; border-radius: 8px; background: #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
    .method { font-weight: bold; font-size: 0.85rem; padding: 2px 8px; border-radius: 4px; color: #fff; margin-right: 8px; }
    .get { background: #0284c7; }
    .post { background: #16a34a; }
    a { color: #0284c7; text-decoration: none; font-weight: 500; }
    a:hover { text-decoration: underline; }
    pre { background: #0f172a; color: #38bdf8; padding: 14px; border-radius: 8px; overflow-x: auto; font-size: 0.85rem; }
    button { background: #16a34a; color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 8px; }
    button:hover { background: #15803d; }
    #demo-result { background: #f8fafc; border: 1px solid #cbd5e1; padding: 12px; border-radius: 6px; margin-top: 10px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; display: none; }
  </style>
</head>
<body>
  <div class="container">
    <h1>AgriVision AI <span class="badge">ML API Online</span></h1>
    <p>Agricultural Price Intelligence & Demand Forecasting engine for Karnataka APMC mandis (Initial crop: <strong>Tomato</strong>).</p>

    <div style="background:#f0fdf4; border:1px solid #86efac; padding:16px; border-radius:8px; margin:20px 0;">
      <h3 style="margin-top:0; color:#15803d;">🚀 Member 4's Frontend UI Connected Live!</h3>
      <p style="margin-bottom:12px;">Member 4's agricultural marketplace UI is wired directly to our live ML microservice:</p>
      <a href="/ui/farmer/prices.html" target="_blank" style="background:#16a34a; color:white; padding:8px 16px; border-radius:6px; display:inline-block; font-weight:600; text-decoration:none;">🌾 Open Farmer Market Intelligence UI &rarr;</a>
      <a href="/ui/admin/ai-monitoring.html" target="_blank" style="background:#0284c7; color:white; padding:8px 16px; border-radius:6px; display:inline-block; font-weight:600; text-decoration:none; margin-left:8px;">📊 Open Admin AI Monitoring UI &rarr;</a>
    </div>

    <h3>Available Endpoints</h3>
    <div class="endpoint">
      <div><span class="method get">GET</span> <a href="/health">/health</a></div>
      <span>Health check & model status</span>
    </div>
    <div class="endpoint">
      <div><span class="method get">GET</span> <a href="/markets">/markets</a></div>
      <span>List Karnataka APMC markets & districts</span>
    </div>
    <div class="endpoint">
      <div><span class="method get">GET</span> <a href="/model-metrics">/model-metrics</a></div>
      <span>Model accuracy (MAE, RMSE, MAPE, R²)</span>
    </div>
    <div class="endpoint">
      <div><span class="method post">POST</span> <code>/predict-price</code></div>
      <span>Predict modal price with 80% interval</span>
    </div>
    <div class="endpoint">
      <div><span class="method post">POST</span> <code>/forecast-demand</code></div>
      <span>7-day demand absorption trend proxy</span>
    </div>
    <div class="endpoint">
      <div><span class="method post">POST</span> <code>/explain-price</code></div>
      <span>TreeSHAP attribution & domain context</span>
    </div>

    <h3>Interactive Test Console</h3>
    <p>Test the <code>/predict-price</code> endpoint live:</p>
    <button onclick="testPredict()">Send Test Prediction Request</button>
    <div id="demo-result"></div>

    <script>
      async function testPredict() {
        const resBox = document.getElementById('demo-result');
        resBox.style.display = 'block';
        resBox.innerText = 'Calling /predict-price for Kolar APMC...';
        try {
          const resp = await fetch('/predict-price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ crop: 'Tomato', market: 'Kolar', district: 'Kolar', date: '2026-03-25', confidence_level: 0.80 })
          });
          const data = await resp.json();
          resBox.innerText = JSON.stringify(data, null, 2);
        } catch (err) {
          resBox.innerText = 'Error: ' + err;
        }
      }
    </script>
  </div>
</body>
</html>"""
    return html, 200


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    """Prevents 404 noise for browser icon requests."""
    return "", 204


@app.route("/ui/", methods=["GET"])
@app.route("/ui", methods=["GET"])
def ui_root():
    """Redirects to Member 4's connected Farmer Market Intelligence page."""
    return redirect("/ui/farmer/prices.html")


@app.route("/ui/<path:filename>", methods=["GET"])
def serve_ui(filename):
    """Serves Member 4's frontend UI static assets directly."""
    if not os.path.exists(UI_DIR):
        return jsonify({"error": f"UI directory not found at {UI_DIR}"}), 404
    return send_from_directory(UI_DIR, filename)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint providing system status and version information."""
    is_ready = (price_predictor is not None and demand_forecaster is not None)
    return jsonify({
        "status": "healthy" if is_ready else "degraded",
        "service": "AgriVision AI - Machine Learning Engine",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": {
            "price_prediction_model": price_predictor is not None,
            "demand_forecasting_model": demand_forecaster is not None,
            "explainability_engine": explainer is not None,
            "crop_disease_cnn_model": (crop_predictor is not None and crop_predictor.is_loaded())
        },
        "cnn_species_count": len(crop_predictor.class_names) if crop_predictor else 0,
        "supported_crops": ["Tomato"] if not crop_predictor else crop_predictor.class_names[:10] + ["..."],
        "supported_markets": supported_markets_list
    }), (200 if is_ready else 503)


def build_inference_dataframe(payload: Dict[str, Any]) -> pd.DataFrame:
    """Constructs a fully featured single-row DataFrame from API payload."""
    market = str(payload.get("market", "Kolar")).strip().title()
    district = str(payload.get("district", "Kolar")).strip().title()
    crop = str(payload.get("crop", "Tomato")).strip().title()
    date_str = str(payload.get("date", datetime.now().strftime("%Y-%m-%d")))
    
    dt = pd.to_datetime(date_str)
    
    # Retrieve market context fallback
    cache = recent_market_cache.get(market, {})
    if not district and cache:
        district = cache.get("district", "Kolar")
        
    lag1 = float(payload.get("modal_price_lag_1", cache.get("last_modal_price", 1600.0)))
    lag3 = float(payload.get("modal_price_lag_3", lag1 * 0.99))
    lag7 = float(payload.get("modal_price_lag_7", cache.get("rolling_mean_7", lag1)))
    lag14 = float(payload.get("modal_price_lag_14", lag7 * 0.98))
    
    arr_lag1 = float(payload.get("arrivals_lag_1", cache.get("last_arrivals", 3000.0)))
    arr_lag3 = float(payload.get("arrivals_lag_3", arr_lag1))
    arr_lag7 = float(payload.get("arrivals_lag_7", cache.get("rolling_arrivals_7", arr_lag1)))
    
    roll_mean7 = float(payload.get("price_rolling_mean_7", cache.get("rolling_mean_7", lag1)))
    roll_std7 = float(payload.get("price_rolling_std_7", cache.get("rolling_std_7", 120.0)))
    roll_mean14 = float(payload.get("price_rolling_mean_14", roll_mean7))
    roll_std14 = float(payload.get("price_rolling_std_14", roll_std7))
    roll_arr7 = float(payload.get("arrivals_rolling_mean_7", cache.get("rolling_arrivals_7", arr_lag1)))
    
    row = {
        "date": dt,
        "market": market,
        "district": district,
        "commodity": crop,
        "modal_price": lag1, # placeholder target for transforms
        "arrivals_qtl": arr_lag1,
        "month": dt.month,
        "week": dt.isocalendar().week,
        "day_of_week": dt.dayofweek,
        "day_of_year": dt.dayofyear,
        "is_weekend": 1 if dt.dayofweek in [5, 6] else 0,
        "sin_day_of_year": np.sin(2 * np.pi * dt.dayofyear / 365.25),
        "cos_day_of_year": np.cos(2 * np.pi * dt.dayofyear / 365.25),
        "sin_month": np.sin(2 * np.pi * dt.month / 12.0),
        "cos_month": np.cos(2 * np.pi * dt.month / 12.0),
        "modal_price_lag_1": lag1,
        "modal_price_lag_3": lag3,
        "modal_price_lag_7": lag7,
        "modal_price_lag_14": lag14,
        "arrivals_lag_1": arr_lag1,
        "arrivals_lag_3": arr_lag3,
        "arrivals_lag_7": arr_lag7,
        "price_rolling_mean_7": roll_mean7,
        "price_rolling_std_7": roll_std7,
        "price_rolling_mean_14": roll_mean14,
        "price_rolling_std_14": roll_std14,
        "arrivals_rolling_mean_7": roll_arr7,
        "price_momentum_7d": lag1 - lag7,
        "price_ratio_to_7d_mean": lag1 / (roll_mean7 + 1e-5),
        "arrival_ratio_to_7d_mean": arr_lag1 / (roll_arr7 + 1e-5)
    }
    return pd.DataFrame([row])


@app.route("/predict-price", methods=["POST"])
def predict_price():
    """
    POST /predict-price
    Body:
    {
        "crop": "Tomato",
        "market": "Kolar",
        "district": "Kolar",
        "date": "2026-03-25",
        "modal_price_lag_1": 1750.0  (optional)
    }
    """
    if price_predictor is None:
        return jsonify({"error": "Price prediction model not loaded on server"}), 503
        
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400
        
    market = payload.get("market")
    if not market:
        return jsonify({"error": "Field 'market' is required (e.g. 'Kolar', 'Bangalore')"}), 400
        
    try:
        conf_level = float(payload.get("confidence_level", 0.80))
        input_df = build_inference_dataframe(payload)
        pred_res = price_predictor.predict_with_interval(input_df, confidence_level=conf_level)[0]
        
        response = {
            "crop": payload.get("crop", "Tomato"),
            "market": input_df["market"].iloc[0],
            "district": input_df["district"].iloc[0],
            "prediction_date": input_df["date"].iloc[0].strftime("%Y-%m-%d"),
            "model_version": price_predictor.version,
            "model_type": price_predictor.model_name,
            **pred_res
        }
        return jsonify(response), 200
    except Exception as exc:
        logger.error("Error during price prediction: %s", exc, exc_info=True)
        return jsonify({"error": f"Prediction failed: {str(exc)}"}), 500


@app.route("/forecast-demand", methods=["POST"])
def forecast_demand():
    """
    POST /forecast-demand
    Body:
    {
        "crop": "Tomato",
        "market": "Kolar",
        "district": "Kolar",
        "date": "2026-03-25"
    }
    """
    if demand_forecaster is None:
        return jsonify({"error": "Demand forecasting model not loaded on server"}), 503
        
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400
        
    market = payload.get("market")
    if not market:
        return jsonify({"error": "Field 'market' is required"}), 400
        
    try:
        input_df = build_inference_dataframe(payload)
        forecast_res = demand_forecaster.forecast(input_df)[0]
        
        response = {
            "crop": payload.get("crop", "Tomato"),
            "market": input_df["market"].iloc[0],
            "district": input_df["district"].iloc[0],
            "forecast_date": input_df["date"].iloc[0].strftime("%Y-%m-%d"),
            "forecast_horizon": "7-day forward window",
            "model_version": demand_forecaster.version,
            **forecast_res
        }
        return jsonify(response), 200
    except Exception as exc:
        logger.error("Error during demand forecasting: %s", exc, exc_info=True)
        return jsonify({"error": f"Demand forecast failed: {str(exc)}"}), 500


@app.route("/explain-price", methods=["POST"])
def explain_price():
    """
    POST /explain-price
    Returns local attribution and synthesized domain explanations.
    """
    if explainer is None or price_predictor is None:
        return jsonify({"error": "Explainability engine not loaded"}), 503
        
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400
        
    market = payload.get("market")
    if not market:
        return jsonify({"error": "Field 'market' is required"}), 400
        
    try:
        input_df = build_inference_dataframe(payload)
        transformed_row = price_predictor.preprocessor.transform(input_df)
        pred_val = float(price_predictor.model.predict(transformed_row)[0])
        
        explanation = explainer.explain_prediction(
            input_data=input_df.iloc[0].to_dict(),
            transformed_row=transformed_row,
            predicted_price=round(pred_val, 2)
        )
        
        response = {
            "crop": payload.get("crop", "Tomato"),
            "market": input_df["market"].iloc[0],
            "district": input_df["district"].iloc[0],
            "date": input_df["date"].iloc[0].strftime("%Y-%m-%d"),
            **explanation
        }
        return jsonify(response), 200
    except Exception as exc:
        logger.error("Error during explanation generation: %s", exc, exc_info=True)
        return jsonify({"error": f"Explanation failed: {str(exc)}"}), 500


@app.route("/model-metrics", methods=["GET"])
def get_model_metrics():
    """GET /model-metrics returns performance statistics of trained models."""
    if not model_metrics:
        return jsonify({"message": "Metrics not yet compiled. Run main.py to train models."}), 404
    return jsonify(model_metrics), 200


@app.route("/markets", methods=["GET"])
def get_markets():
    """GET /markets returns supported crops, districts, and Karnataka mandis."""
    return jsonify({
        "supported_crops": ["Tomato"],
        "state": "Karnataka",
        "markets": recent_market_cache or [
            {"market": "Kolar", "district": "Kolar"},
            {"market": "Bangalore", "district": "Bangalore Urban"},
            {"market": "Ramanagara", "district": "Ramanagara"},
            {"market": "Belagavi", "district": "Belagavi"},
            {"market": "Mysuru", "district": "Mysuru"},
            {"market": "Chikkaballapur", "district": "Chikkaballapur"}
        ]
    }), 200


@app.route("/predict-disease", methods=["POST"])
@app.route("/assess-crop", methods=["POST"])
def predict_crop_disease():
    """
    POST /predict-disease or POST /assess-crop
    Deep Learning CNN inference for crop identity and quality verification.
    
    Accepts:
      - Multipart Form: 'file' or 'image' (binary image upload), 'crop' (claimed crop string)
      - JSON Body: { 'image': '<base64 data-url or raw string>', 'crop': 'Tomato' }
    """
    global crop_predictor
    if crop_predictor is None:
        return jsonify({
            "error": "Crop CNN model is not initialized on server",
            "method": "efficientnet_b2_cnn"
        }), 503

    claimed_crop = None
    image_input = None

    # 1. Handle multipart file upload
    if request.files:
        file_obj = request.files.get("file") or request.files.get("image")
        if file_obj:
            image_input = file_obj.read()
        claimed_crop = request.form.get("crop") or request.form.get("claimed_crop")

    # 2. Handle JSON payload (base64 image)
    if not image_input and request.is_json:
        payload = request.get_json(silent=True) or {}
        image_input = payload.get("image") or payload.get("photo") or payload.get("file")
        claimed_crop = payload.get("crop") or payload.get("claimed_crop")

    # 3. Check for raw data in body
    if not image_input and request.data:
        image_input = request.data

    if not image_input:
        return jsonify({
            "error": "No image provided. Send a multipart file ('file'/'image') or JSON {'image': '<base64>'}"
        }), 400

    try:
        result = crop_predictor.predict(image_input, claimed_crop=claimed_crop)
        status_code = 200 if result.get("success", True) else 400
        return jsonify(result), status_code
    except Exception as exc:
        logger.error("Error in crop disease prediction endpoint: %s", exc, exc_info=True)
        return jsonify({"error": f"Prediction failed: {str(exc)}"}), 500


# Self-boot helper
load_artifacts()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting AgriVision AI ML API on port %d...", port)
    app.run(host="0.0.0.0", port=port, debug=False)
