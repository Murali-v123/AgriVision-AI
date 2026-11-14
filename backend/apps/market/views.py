"""
apps/market/views.py
====================
Market API views for AgriVision AI.

ML Integration (Member 2 → Member 3 integration):
  - PriceRecommendationView  : proxies to Flask /predict-price + /explain-price
  - MarketDemandView         : proxies to Flask /forecast-demand
  - MarketMLIntelligenceView : combined single-shot endpoint for the UI

If the Flask ML API (port 5000) is offline, all three views fall back to the
original demo formula so the Django backend keeps running independently.

Unit convention:
  Flask API → ₹/quintal | Django views → ₹/kg  (ml_client handles conversion)
"""

import math
import logging
from datetime import date

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import MarketPrice, ContactMessage
from .serializers import MarketPriceSerializer, ContactMessageSerializer
from .ml_client import (
    call_ml_predict_price,
    call_ml_forecast_demand,
    call_ml_explain_price,
    call_ml_markets,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Demo / fallback constants (kept intact so the API never crashes)
# ---------------------------------------------------------------------------
CROP_BASE = {'Tomato': 28.0, 'Onion': 21.0, 'Potato': 18.0}
DEMAND_IDX = {
    'Tomato': {'value': 82, 'label': 'High'},
    'Onion': {'value': 58, 'label': 'Medium'},
    'Potato': {'value': 41, 'label': 'Low'},
}
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Default market for ML calls when only crop+district is supplied
_DEFAULT_MARKET_MAP = {
    'Kolar': 'Kolar',
    'Bengaluru': 'Bengaluru (Binny Mill)',
    'Mysuru': 'Mysuru',
    'Tumkur': 'Tumkur',
    'Hassan': 'Hassan',
    'Chitradurga': 'Chitradurga',
}


# ---------------------------------------------------------------------------
# Demo formula helpers (fallback, unchanged from original implementation)
# ---------------------------------------------------------------------------

def calculate_current_price(crop, district):
    base = CROP_BASE.get(crop, 20.0)
    f = 0.97 + ((len(district or '')) % 8) * 0.01
    return round(base * f, 1)


def generate_series(crop, district, months=12):
    base = CROP_BASE.get(crop, 20.0)
    s = len(district or '') * 0.37 + len(crop)
    raw = []
    for i in range(months):
        k = months - 1 - i
        m = (10 - k + 120) % 12
        val = base * (1 + 0.14 * math.sin(i / 2.1 + s) + 0.03 * math.cos(i * 1.7))
        raw.append({'label': MON[m], 'v': val})

    now = calculate_current_price(crop, district)
    last = raw[-1]['v']
    return [{'label': p['label'], 'value': round(p['v'] * now / last, 1)} for p in raw]


def calculate_recommended_price(crop, district):
    hist = generate_series(crop, district, 12)[-3:]
    avg_3m = sum(p['value'] for p in hist) / 3.0
    return round(avg_3m * 1.04, 1)


# ---------------------------------------------------------------------------
# Market price list (unchanged — returns DB / demo records)
# ---------------------------------------------------------------------------

class MarketPriceListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = MarketPrice.objects.all()
        crop = request.query_params.get('crop')
        state = request.query_params.get('state')
        district = request.query_params.get('district')
        market_name = request.query_params.get('market')

        if crop:
            queryset = queryset.filter(crop__iexact=crop)
        if state:
            queryset = queryset.filter(state__iexact=state)
        if district:
            queryset = queryset.filter(district__iexact=district)
        if market_name:
            queryset = queryset.filter(market_name__icontains=market_name)

        serializer = MarketPriceSerializer(queryset[:100], many=True)
        return Response({
            'count': queryset.count(),
            'is_demo_data': True,
            'data_source': 'Simulated demonstration mandi series (labeled demo data)',
            'results': serializer.data,
        })


# ---------------------------------------------------------------------------
# Price Recommendation — now ML-powered with demo fallback
# ---------------------------------------------------------------------------

class PriceRecommendationView(APIView):
    """
    GET /api/market/recommendations/

    Query params:
        crop     (default: Tomato)
        district (default: Kolar)
        market   (optional, inferred from district if omitted)
        state    (default: Karnataka)
        months   (default: 12, for historical series)
        date     (default: today, ISO format YYYY-MM-DD)

    Response includes:
        is_live_ml          — True when Flask ML API was reachable
        ml_prediction       — ML model output (₹/kg)
        prediction_interval — 80 % confidence band (₹/kg)
        demand_trend        — supply/demand proxy from demand model
        explanation         — XAI narrative text + feature contributions
        [fallback fields]   — current_price_per_kg, recommended_price_per_kg,
                              demand_indicator, series (always present)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        crop = request.query_params.get('crop', 'Tomato')
        district = request.query_params.get('district', 'Kolar')
        state = request.query_params.get('state', 'Karnataka')
        months = int(request.query_params.get('months', 12))
        prediction_date = request.query_params.get('date', date.today().isoformat())

        # Infer market name from district (best-effort mapping)
        market = request.query_params.get(
            'market',
            _DEFAULT_MARKET_MAP.get(district, district)
        )

        # Always compute demo values (used as fallback + historical series)
        cur = calculate_current_price(crop, district)
        rec = calculate_recommended_price(crop, district)
        hist_series = generate_series(crop, district, months)
        demo_demand = DEMAND_IDX.get(crop, {'value': 50, 'label': 'Medium'})

        # Base response (always present regardless of ML status)
        response = {
            'crop': crop,
            'district': district,
            'market': market,
            'state': state,
            'prediction_date': prediction_date,
            # Demo / fallback fields (kept for backward compatibility)
            'current_price_per_kg': cur,
            'recommended_price_per_kg': rec,
            'demand_indicator': demo_demand,
            'series': hist_series,
        }

        # ----------------------------------------------------------------
        # Attempt ML API calls (server-to-server, no CORS)
        # ----------------------------------------------------------------
        ml_price = call_ml_predict_price(crop, market, district, prediction_date)
        ml_demand = call_ml_forecast_demand(crop, market, district)
        ml_explain = call_ml_explain_price(crop, market, district, prediction_date)

        is_live_ml = ml_price is not None

        if is_live_ml:
            # Overwrite recommended price with ML prediction
            response['recommended_price_per_kg'] = ml_price['predicted_modal_price_per_kg']
            response['ml_prediction'] = {
                'predicted_modal_price_per_kg': ml_price['predicted_modal_price_per_kg'],
                'raw_quintal_price': ml_price['raw_quintal_price'],
                'model_type': ml_price['model_type'],
                'model_version': ml_price['model_version'],
                'prediction_date': ml_price['prediction_date'],
                'uncertainty_disclaimer': ml_price['uncertainty_disclaimer'],
            }
            response['prediction_interval'] = ml_price.get('prediction_interval_per_kg', {})
        else:
            logger.info(
                "ML API offline for /recommendations — using demo formula fallback "
                "(crop=%s district=%s)", crop, district
            )
            response['ml_prediction'] = None

        if ml_demand is not None:
            response['demand_trend'] = {
                'trend_label': ml_demand.get('demand_trend') or ml_demand.get('trend_label', 'Stable'),
                'trend_direction': (ml_demand.get('demand_trend') or ml_demand.get('trend_direction', 'stable')).lower(),
                'confidence_pct': ml_demand.get('confidence_percentage') or ml_demand.get('confidence_pct', '50%'),
                'economic_interpretation': ml_demand.get('economic_interpretation', ''),
                'supply_proxy_note': ml_demand.get('proxy_disclaimer') or ml_demand.get(
                    'supply_proxy_note',
                    'Based on historical market arrivals — not a direct measurement of consumer demand.',
                ),
                'methodology_note': ml_demand.get('methodology_note', ''),
            }
        else:
            response['demand_trend'] = None

        if ml_explain is not None:
            response['explanation'] = {
                'narrative': ml_explain.get('natural_language_explanation') or ml_explain.get('narrative_explanation', ''),
                'top_influencing_features': ml_explain.get('top_influencing_features') or ml_explain.get('feature_contributions', []),
                'domain_context': ml_explain.get('domain_context', {}),
                'interpretation_notice': ml_explain.get('interpretation_notice', ''),
                'shap_available': bool(ml_explain.get('top_influencing_features')),
            }
        else:
            response['explanation'] = {
                'narrative': (
                    'Recommended price is based on the recent market price trend, '
                    'seasonal patterns, and historical market conditions. '
                    '(ML API offline — using demo formula)'
                ),
                'top_influencing_features': [],
                'domain_context': {},
                'shap_available': False,
            }

        response['is_live_ml'] = is_live_ml
        response['data_source'] = (
            'AgriVision ML Engine v1.0 (GradientBoostingRegressor, Karnataka APMC synthetic demo data)'
            if is_live_ml
            else 'AgriVision Market Intelligence Demo Rule (ML API offline fallback)'
        )

        return Response(response)


# ---------------------------------------------------------------------------
# Market Demand — now ML-powered with demo fallback
# ---------------------------------------------------------------------------

class MarketDemandView(APIView):
    """
    GET /api/market/demand/

    Query params:
        crop     (optional — returns all crops if omitted)
        market   (optional, default: Kolar)
        district (optional, default: Kolar)

    If crop is supplied, proxies to Flask /forecast-demand.
    Falls back to DEMAND_IDX if ML API is offline.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        crop = request.query_params.get('crop')
        market = request.query_params.get('market', 'Kolar')
        district = request.query_params.get('district', 'Kolar')

        if crop:
            # Attempt live ML forecast
            ml_demand = call_ml_forecast_demand(crop, market, district)

            if ml_demand is not None:
                return Response({
                    'crop': crop,
                    'market': market,
                    'district': district,
                    'demand': {
                        'trend_label': ml_demand.get('trend_label', 'Stable'),
                        'trend_direction': ml_demand.get('trend_direction', 'stable'),
                        'confidence_pct': ml_demand.get('confidence_pct', 0),
                        'supply_proxy_note': ml_demand.get(
                            'supply_proxy_note',
                            'Arrivals-based proxy. Not a direct consumer demand measurement.',
                        ),
                    },
                    'is_live_ml': True,
                    'is_demo_data': False,
                })
            else:
                # Fallback to static index
                demand = DEMAND_IDX.get(crop, {'value': 50, 'label': 'Medium'})
                return Response({
                    'crop': crop,
                    'demand': demand,
                    'is_live_ml': False,
                    'is_demo_data': True,
                })

        # No crop specified — return all static demand indices
        return Response({
            'demands': DEMAND_IDX,
            'is_live_ml': False,
            'is_demo_data': True,
        })


# ---------------------------------------------------------------------------
# Combined ML Intelligence View (new endpoint for the UI)
# ---------------------------------------------------------------------------

class MarketMLIntelligenceView(APIView):
    """
    POST /api/market/ml-intelligence/

    Single-shot endpoint that returns price prediction + demand forecast +
    XAI explanation in one response.  Designed for Member 4's frontend to
    call Django instead of the Flask API directly.

    Request body (JSON):
    {
        "crop":     "Tomato",
        "market":   "Kolar",
        "district": "Kolar",
        "date":     "2026-03-25"   (optional, defaults to today)
    }

    Response:
    {
        "price_prediction":  { ... },
        "demand_forecast":   { ... },
        "explanation":       { ... },
        "is_live_ml":        true,
        "data_source":       "..."
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        crop = data.get('crop', 'Tomato')
        district = data.get('district', 'Kolar')
        market = data.get(
            'market',
            _DEFAULT_MARKET_MAP.get(district, district)
        )
        prediction_date = data.get('date', date.today().isoformat())

        # Validation
        if not crop or not isinstance(crop, str):
            return Response(
                {'error': 'crop must be a non-empty string.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ml_price = call_ml_predict_price(crop, market, district, prediction_date)
        ml_demand = call_ml_forecast_demand(crop, market, district)
        ml_explain = call_ml_explain_price(crop, market, district, prediction_date)

        is_live_ml = ml_price is not None

        # Build response blocks
        if is_live_ml:
            price_block = {
                'predicted_modal_price_per_kg': ml_price['predicted_modal_price_per_kg'],
                'raw_quintal_price': ml_price['raw_quintal_price'],
                'prediction_interval': ml_price.get('prediction_interval_per_kg', {}),
                'model_type': ml_price['model_type'],
                'model_version': ml_price['model_version'],
                'uncertainty_disclaimer': ml_price['uncertainty_disclaimer'],
                'prediction_date': ml_price['prediction_date'],
            }
        else:
            rec = calculate_recommended_price(crop, district)
            price_block = {
                'predicted_modal_price_per_kg': rec,
                'raw_quintal_price': rec * 100,
                'prediction_interval': {
                    'lower_bound': round(rec * 0.75, 2),
                    'upper_bound': round(rec * 1.25, 2),
                    'confidence_level': 'N/A (demo fallback)',
                },
                'model_type': 'DemoFormula',
                'model_version': 'fallback',
                'uncertainty_disclaimer': (
                    'ML API is offline. Price shown is a demo formula estimate only. '
                    'Do not use for real trading decisions.'
                ),
                'prediction_date': prediction_date,
            }

        demand_block = None
        if ml_demand is not None:
            demand_block = {
                'trend_label': ml_demand.get('demand_trend') or ml_demand.get('trend_label', 'Stable'),
                'trend_direction': (ml_demand.get('demand_trend') or ml_demand.get('trend_direction', 'stable')).lower(),
                'confidence_pct': ml_demand.get('confidence_percentage') or ml_demand.get('confidence_pct', '50%'),
                'economic_interpretation': ml_demand.get('economic_interpretation', ''),
                'supply_proxy_note': ml_demand.get('proxy_disclaimer') or ml_demand.get(
                    'supply_proxy_note',
                    'Arrivals proxy — not a direct consumer demand measurement.',
                ),
            }

        explain_block = None
        if ml_explain is not None:
            explain_block = {
                'narrative': ml_explain.get('natural_language_explanation') or ml_explain.get('narrative_explanation', ''),
                'top_influencing_features': ml_explain.get('top_influencing_features') or ml_explain.get('feature_contributions', []),
                'domain_context': ml_explain.get('domain_context', {}),
                'interpretation_notice': ml_explain.get('interpretation_notice', ''),
                'shap_available': bool(ml_explain.get('top_influencing_features')),
            }

        return Response({
            'crop': crop,
            'market': market,
            'district': district,
            'price_prediction': price_block,
            'demand_forecast': demand_block,
            'explanation': explain_block,
            'is_live_ml': is_live_ml,
            'data_source': (
                'AgriVision ML Engine v1.0 (GradientBoostingRegressor, Karnataka APMC synthetic demo data)'
                if is_live_ml
                else 'AgriVision Demo Formula (ML API offline — fallback mode)'
            ),
        })


# ---------------------------------------------------------------------------
# Contact message (unchanged)
# ---------------------------------------------------------------------------

class ContactMessageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Message received. Platform team has recorded your contact request.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
