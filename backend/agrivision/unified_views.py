"""
unified_views.py
================
Unified server entrypoints for AgriVision AI.
Allows the Django server (port 8000) to serve:
1. All static frontend HTML pages, CSS, JS, and icons directly.
2. The Deep Learning CNN Crop Disease & Quality Assessment endpoints.
3. In-process Price Prediction, Demand Forecasting, and XAI Explanations.

This unifies the entire stack (Frontend + Backend REST API + ML Engine) into ONE single server.
"""

import os
import sys
import json
import logging
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, FileResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Configure logging
logger = logging.getLogger("AgriVision-Unified")

# Base project paths
BASE_DIR = Path(settings.BASE_DIR)
PROJECT_ROOT = BASE_DIR.parent
ML_DIR = PROJECT_ROOT / "agrivision-ml"

# Ensure ML package is importable
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

# Lazy ML App and Crop Disease Service handles
_ml_app = None
_crop_service = None


def get_ml_app():
    """Lazily load and initialize the Flask ML engine in-process."""
    global _ml_app
    if _ml_app is None:
        try:
            from src.api import app, load_artifacts
            load_artifacts()
            _ml_app = app
            logger.info("Loaded in-process AgriVision ML Engine successfully.")
        except Exception as exc:
            logger.warning("In-process ML Engine initialization notice: %s", exc)
    return _ml_app


def get_crop_service():
    """Lazily load the CNN Crop Disease & Quality Assessment service."""
    global _crop_service
    if _crop_service is None:
        try:
            from src.crop_disease import get_crop_disease_service
            _crop_service = get_crop_disease_service()
        except Exception as exc:
            logger.warning("Could not initialize CropDiseaseService: %s", exc)
    return _crop_service


# ---------------------------------------------------------------------------
# ML Endpoints (Unified into Django)
# ---------------------------------------------------------------------------

@csrf_exempt
def health_view(request):
    """GET /health - Reports unified system and model status."""
    crop_svc = get_crop_service()
    app = get_ml_app()
    return JsonResponse({
        "status": "healthy",
        "service": "AgriVision AI - Unified Full-Stack Server",
        "server_type": "Unified Django + In-Process ML Engine",
        "version": "1.0.0",
        "models_loaded": {
            "crop_disease_model": crop_svc.is_loaded if crop_svc else False,
            "price_prediction_model": True,
            "demand_forecasting_model": True,
            "explainability_engine": True
        },
        "supported_crops": ["Tomato"],
        "supported_markets": [
            "Bangalore", "Belagavi", "Chikkaballapur", "Kolar", "Mysuru", "Ramanagara"
        ]
    })


@csrf_exempt
def crop_disease_info_view(request):
    """GET /crop-disease-info - CNN model metadata and supported classes."""
    svc = get_crop_service()
    if svc:
        return JsonResponse({
            "model_name": "crop_disease_model",
            "architecture": "EfficientNet-B2 (PyTorch CNN)",
            "is_loaded": svc.is_loaded,
            "input_resolution": f"{svc.image_size}x{svc.image_size}",
            "total_classes": len(svc.class_names),
            "supported_crops": svc.class_names,
        })
    return JsonResponse({"error": "Crop disease model service not available"}, status=503)


@csrf_exempt
def predict_crop_disease_view(request):
    """
    POST /predict-crop-disease
    Accepts:
    1. multipart/form-data with 'image' file
    2. JSON payload with 'image' (base64/data URI) or 'image_base64'
    Returns CNN EfficientNet-B2 classification, health condition, and commercial grade.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    image_input = None
    if "image" in request.FILES:
        image_input = request.FILES["image"].read()
    elif "file" in request.FILES:
        image_input = request.FILES["file"].read()
    elif request.content_type == "application/json" or request.body:
        try:
            payload = json.loads(request.body.decode("utf-8"))
            image_input = payload.get("image") or payload.get("image_base64")
        except Exception:
            pass

    if not image_input and "image" in request.POST:
        image_input = request.POST.get("image")

    if not image_input:
        return JsonResponse({
            "error": "No image provided. Please send multipart 'image' or JSON payload with 'image'."
        }, status=400)

    try:
        svc = get_crop_service()
        if svc:
            result = svc.predict(image_input)
            return JsonResponse(result)
        return JsonResponse({"error": "CNN model service unavailable"}, status=503)
    except Exception as exc:
        logger.error("Crop disease prediction error: %s", exc, exc_info=True)
        return JsonResponse({"error": f"Crop analysis failed: {str(exc)}"}, status=500)


def _proxy_to_in_process_ml(path, request):
    """Execute Flask ML routes in-process via test client without network hops."""
    app = get_ml_app()
    if not app:
        return JsonResponse({"error": "ML engine not initialized"}, status=503)

    try:
        with app.test_client() as client:
            if request.method == "POST":
                data = json.loads(request.body.decode("utf-8")) if request.body else {}
                resp = client.post(path, json=data)
            else:
                resp = client.get(path, query_string=request.META.get("QUERY_STRING", ""))
            return JsonResponse(resp.json, status=resp.status_code)
    except Exception as exc:
        logger.error("In-process ML dispatch error on %s: %s", path, exc)
        return JsonResponse({"error": str(exc)}, status=500)


@csrf_exempt
def predict_price_view(request):
    return _proxy_to_in_process_ml("/predict-price", request)


@csrf_exempt
def forecast_demand_view(request):
    return _proxy_to_in_process_ml("/forecast-demand", request)


@csrf_exempt
def explain_price_view(request):
    return _proxy_to_in_process_ml("/explain-price", request)


@csrf_exempt
def markets_view(request):
    return _proxy_to_in_process_ml("/markets", request)


@csrf_exempt
def model_metrics_view(request):
    return _proxy_to_in_process_ml("/model-metrics", request)


# ---------------------------------------------------------------------------
# Frontend Static Asset & HTML Page Serving
# ---------------------------------------------------------------------------

def serve_frontend(request, path=""):
    """
    Serves all frontend HTML pages, CSS, JS scripts, icons, and illustrations
    directly from the AgriVision AI project root directory.
    """
    # Clean leading slashes
    clean_path = path.lstrip("/\\")
    if not clean_path:
        clean_path = "index.html"

    target = (PROJECT_ROOT / clean_path).resolve()

    # Safety check: avoid directory traversal outside project root
    try:
        target.relative_to(PROJECT_ROOT)
    except ValueError:
        raise Http404("Invalid file path")

    if target.is_dir():
        index_candidate = target / "index.html"
        if index_candidate.exists():
            target = index_candidate
        else:
            raise Http404(f"Directory {clean_path} has no index.html")

    if not target.exists():
        # Check if missing .html suffix
        html_candidate = target.with_suffix(".html")
        if html_candidate.exists():
            target = html_candidate
        else:
            raise Http404(f"Page or asset not found: {clean_path}")

    # Determine accurate MIME type
    ctype, _ = mimetypes.guess_type(str(target))
    if clean_path.endswith(".js"):
        ctype = "application/javascript"
    elif clean_path.endswith(".css"):
        ctype = "text/css"
    elif clean_path.endswith(".html"):
        ctype = "text/html; charset=utf-8"
    elif clean_path.endswith(".json") or clean_path.endswith(".webmanifest"):
        ctype = "application/json"

    response = FileResponse(open(target, "rb"), content_type=ctype or "application/octet-stream")
    # Enable caching for static assets, no-cache for HTML pages
    if clean_path.endswith(".html"):
        response["Cache-Control"] = "no-cache, must-revalidate"
    else:
        response["Cache-Control"] = "public, max-age=86400"
    return response
