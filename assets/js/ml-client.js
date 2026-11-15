/**
 * ml-client.js
 * ------------
 * AgriVision AI - Client-Side Bridge connecting Frontend Views to the Machine Learning Engine.
 * Supports direct connection to Flask ML microservice (http://127.0.0.1:5000)
 * with automatic fallback to Django proxy (http://127.0.0.1:8000/api/market/ml-intelligence/).
 */

const ML_API_BASE = window.ML_API_BASE_OVERRIDE || 'http://127.0.0.1:5000';
const DJANGO_ML_API_BASE = window.API_BASE_OVERRIDE || (
  (typeof window !== 'undefined' && window.location && window.location.protocol.startsWith('http') && window.location.port !== '5500' && window.location.port !== '3000')
    ? `${window.location.origin}/api`
    : 'http://127.0.0.1:8000/api'
);

window.ML_CACHE = {
  isOnline: false,
  lastQuery: null,
  priceData: null,
  demandData: null,
  explainData: null,
  metricsData: null,
  loading: false
};

// Check if ML Microservice is running
async function checkMLHealth() {
  try {
    const res = await fetch(`${ML_API_BASE}/health`, { method: 'GET', mode: 'cors' });
    if (res.ok) {
      const data = await res.json();
      window.ML_CACHE.isOnline = true;
      return data;
    }
  } catch (err) {
    // Check if Django backend is available as proxy
    try {
      const dRes = await fetch(`${DJANGO_ML_API_BASE}/market/prices/`, { method: 'GET', mode: 'cors' });
      if (dRes.ok) {
        window.ML_CACHE.isOnline = false; // Flask offline, Django online
      }
    } catch (e) {
      window.ML_CACHE.isOnline = false;
    }
  }
  return null;
}

// Fetch Price, Demand, and XAI Explanation for a given crop/mandi
async function fetchMLIntelligence(crop, market, district) {
  const cacheKey = `${crop}-${market}-${district}`;
  if (window.ML_CACHE.lastQuery === cacheKey && window.ML_CACHE.priceData) {
    return window.ML_CACHE;
  }

  window.ML_CACHE.loading = true;
  const today = new Date().toISOString().split('T')[0];
  const payload = {
    crop: crop || 'Tomato',
    market: market || 'Kolar',
    district: district || 'Kolar',
    date: today,
    confidence_level: 0.80
  };

  // 1. Try direct Flask ML microservice on port 5000
  try {
    const [priceRes, demandRes, explainRes] = await Promise.all([
      fetch(`${ML_API_BASE}/predict-price`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }),
      fetch(`${ML_API_BASE}/forecast-demand`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }),
      fetch(`${ML_API_BASE}/explain-price`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    ]);

    if (priceRes.ok) {
      window.ML_CACHE.priceData = await priceRes.json();
      window.ML_CACHE.isOnline = true;
    }
    if (demandRes.ok) {
      window.ML_CACHE.demandData = await demandRes.json();
    }
    if (explainRes.ok) {
      window.ML_CACHE.explainData = await explainRes.json();
    }
    window.ML_CACHE.lastQuery = cacheKey;
    return window.ML_CACHE;
  } catch (err) {
    // Flask offline — try Django single-shot proxy endpoint
    try {
      const djangoRes = await fetch(`${DJANGO_ML_API_BASE}/market/ml-intelligence/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (djangoRes.ok) {
        const dData = await djangoRes.json();
        if (dData.price_prediction) {
          window.ML_CACHE.priceData = {
            predicted_modal_price: dData.price_prediction.raw_quintal_price,
            predicted_modal_price_per_kg: dData.price_prediction.predicted_modal_price_per_kg,
            prediction_interval: {
              lower_bound: (dData.price_prediction.prediction_interval.lower_bound || 0) * 100,
              upper_bound: (dData.price_prediction.prediction_interval.upper_bound || 0) * 100,
              confidence_level: '80%'
            },
            model_type: dData.price_prediction.model_type,
            model_version: dData.price_prediction.model_version,
            is_live_ml: dData.is_live_ml
          };
          window.ML_CACHE.isOnline = !!dData.is_live_ml;
        }
        if (dData.demand_forecast) {
          window.ML_CACHE.demandData = {
            demand_trend: dData.demand_forecast.trend_label || dData.demand_forecast.demand_trend,
            confidence_percentage: dData.demand_forecast.confidence_pct || 'N/A',
            economic_interpretation: dData.demand_forecast.supply_proxy_note || ''
          };
        }
        if (dData.explanation) {
          window.ML_CACHE.explainData = {
            natural_language_explanation: dData.explanation.narrative_explanation || dData.explanation.natural_language_explanation
          };
        }
        window.ML_CACHE.lastQuery = cacheKey;
        return window.ML_CACHE;
      }
    } catch (e2) {
      // Both offline
      window.ML_CACHE.isOnline = false;
    }
  } finally {
    window.ML_CACHE.loading = false;
  }

  return window.ML_CACHE;
}

// Fetch Model Performance Metrics
async function fetchMLMetrics() {
  if (window.ML_CACHE.metricsData) return window.ML_CACHE.metricsData;
  try {
    const res = await fetch(`${ML_API_BASE}/model-metrics`, { method: 'GET', mode: 'cors' });
    if (res.ok) {
      window.ML_CACHE.metricsData = await res.json();
      return window.ML_CACHE.metricsData;
    }
  } catch (err) {
    // Try fallback to Django admin model metrics
    try {
      const dRes = await fetch(`${DJANGO_ML_API_BASE}/admin/models/`, { method: 'GET', mode: 'cors' });
      if (dRes.ok) {
        const d = await dRes.json();
        if (d.price_prediction_model) {
          window.ML_CACHE.metricsData = {
            price_model: d.price_prediction_model,
            demand_model: d.demand_model
          };
          return window.ML_CACHE.metricsData;
        }
      }
    } catch (e2) {}
  }
  return null;
}

// Initial async probe
checkMLHealth();
