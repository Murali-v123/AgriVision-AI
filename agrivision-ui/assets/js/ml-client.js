/**
 * ml-client.js
 * ------------
 * AgriVision AI - Client-Side Bridge between Member 4's Frontend and Member 2's ML Engine
 * Connects directly to Flask REST API at http://127.0.0.1:5000
 */

const ML_API_BASE = 'http://127.0.0.1:5000';

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
    window.ML_CACHE.isOnline = false;
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
  } catch (err) {
    console.warn('AgriVision ML API offline or unreachable:', err);
    window.ML_CACHE.isOnline = false;
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
    console.warn('Could not fetch ML metrics:', err);
  }
  return null;
}

// Initial async probe
checkMLHealth();
