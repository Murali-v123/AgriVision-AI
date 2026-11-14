"""
explainability.py
-----------------
AgriVision AI - Agricultural Price Intelligence & Demand Forecasting
Provides explainable AI recommendations using TreeSHAP / model feature importances,
synthesized with factual market trends, seasonal patterns, and arrival elasticity.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Try importing shap, with graceful fallback
try:
    import shap
    SHAP_AVAILABLE = True
except Exception:
    SHAP_AVAILABLE = False


class AgriExplainer:
    """
    Explainability engine for AgriVision AI price predictions.
    Computes global feature importances, local SHAP values (or feature contribution weights),
    and generates grounded, factual natural language explanations.
    """
    def __init__(self, model, preprocessor, feature_names: List[str]):
        self.model = model
        self.preprocessor = preprocessor
        self.feature_names = feature_names
        self.shap_explainer = None
        
        # Precompute global feature importances
        if hasattr(model, "feature_importances_"):
            self.global_importances = dict(zip(feature_names, model.feature_importances_))
        else:
            self.global_importances = {f: 1.0 / len(feature_names) for f in feature_names}
            
        # Initialize TreeExplainer if SHAP is available
        if SHAP_AVAILABLE and hasattr(model, "estimators_"):
            try:
                # Use a small background summary or direct tree explainer
                self.shap_explainer = shap.TreeExplainer(model)
                logger.info("Initialized SHAP TreeExplainer successfully.")
            except Exception as e:
                logger.warning("Could not initialize TreeExplainer: %s. Using feature importance fallback.", e)
                self.shap_explainer = None

    def get_top_global_features(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Returns top N most influential features across the entire model."""
        sorted_feats = sorted(self.global_importances.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [{"feature": k, "importance_score": round(float(v), 4)} for k, v in sorted_feats]

    def explain_prediction(
        self,
        input_data: Dict[str, Any],
        transformed_row: pd.DataFrame,
        predicted_price: float
    ) -> Dict[str, Any]:
        """
        Produces local feature attribution and human-readable natural language explanation
        grounded in actual model inputs.
        """
        # 1. Local attribution (SHAP or relative feature weighting)
        local_attributions = []
        if self.shap_explainer is not None:
            try:
                shap_vals = self.shap_explainer.shap_values(transformed_row.values)
                # For 1D or single output regression
                vals = shap_vals[0] if isinstance(shap_vals, np.ndarray) and shap_vals.ndim == 2 else shap_vals
                for feat, val in zip(self.feature_names, vals):
                    local_attributions.append({
                        "feature": feat,
                        "shap_impact": round(float(val), 2),
                        "direction": "upward" if val > 0 else "downward"
                    })
                # Sort by absolute SHAP impact
                local_attributions.sort(key=lambda x: abs(x["shap_impact"]), reverse=True)
            except Exception as err:
                logger.debug("SHAP explanation fallback triggered: %s", err)
                
        if not local_attributions:
            # Fallback to feature importance weighting
            for feat in self.feature_names:
                imp = self.global_importances.get(feat, 0.0)
                local_attributions.append({
                    "feature": feat,
                    "importance_weight": round(float(imp), 4),
                    "direction": "influential"
                })
            local_attributions.sort(key=lambda x: x["importance_weight"], reverse=True)

        top_factors = local_attributions[:5]

        # 2. Derive factual domain context from inputs
        market = input_data.get("market", "Karnataka APMC")
        district = input_data.get("district", "Karnataka")
        date_str = input_data.get("date", "Today")
        month = int(input_data.get("month", pd.to_datetime(date_str).month if date_str != "Today" else 6))
        
        # Historical price trend context
        lag1 = float(input_data.get("modal_price_lag_1", predicted_price))
        lag7 = float(input_data.get("modal_price_lag_7", lag1))
        rolling_mean_7 = float(input_data.get("price_rolling_mean_7", lag1))
        
        pct_change_7d = ((lag1 - lag7) / (lag7 + 1e-5)) * 100.0 if lag7 > 0 else 0.0
        if pct_change_7d > 5.0:
            price_trend_text = f"Recent 7-day price momentum shows an upward surge (+{pct_change_7d:.1f}%), indicating strong buying demand in {market}."
        elif pct_change_7d < -5.0:
            price_trend_text = f"Recent 7-day price momentum is softening ({pct_change_7d:.1f}%), reflecting increased wholesale availability."
        else:
            price_trend_text = f"Recent prices have remained range-bound around ₹{rolling_mean_7:.0f}/quintal in {market}."

        # Seasonal influence context
        if month in [3, 4, 5, 6]:
            seasonal_text = (
                "Summer / Zaid season (March-June) typically causes localized crop heat stress and reduced field yields, "
                "supporting firm prices across southern Karnataka mandis."
            )
        elif month in [7, 8, 9, 10]:
            seasonal_text = (
                "Kharif monsoon period (July-October) features variable arrivals driven by rain disruptions and transportation logistics."
            )
        else:
            seasonal_text = (
                "Rabi winter harvest (November-February) marks peak harvest arrivals across Kolar and Chikkaballapur belts, "
                "often moderating modal prices."
            )

        # Market-specific context
        if market.lower() in ["kolar", "chikkaballapur"]:
            market_text = (
                f"{market} APMC functions as a primary terminal aggregation hub with heavy interstate truck dispatches, "
                "leading to higher liquidity and sensitive price responsiveness."
            )
        elif market.lower() in ["bangalore", "bangalore urban"]:
            market_text = (
                "Bangalore urban market operates primarily on high daily retail and hospitality absorption, "
                "commanding a quality premium over regional farm-gate prices."
            )
        else:
            market_text = f"{market} APMC reflects local district consumption patterns and regional farm-gate supply."

        # Arrival trend context
        arr_lag1 = float(input_data.get("arrivals_lag_1", 2500))
        arr_mean7 = float(input_data.get("arrivals_rolling_mean_7", 2500))
        arr_diff_pct = ((arr_lag1 - arr_mean7) / (arr_mean7 + 1e-5)) * 100.0 if arr_mean7 > 0 else 0.0
        
        if arr_diff_pct > 15.0:
            arrival_text = f"Recent mandi arrivals ({arr_lag1:.0f} qtl) are {arr_diff_pct:.1f}% above the 7-day average, exerting moderate downward pressure on bids."
        elif arr_diff_pct < -15.0:
            arrival_text = f"Arrivals contracted by {abs(arr_diff_pct):.1f}% below recent averages, tightening market supply."
        else:
            arrival_text = f"Arrival flow ({arr_lag1:.0f} qtl) is tracking near the normal weekly baseline."

        # Synthesized, verifiable natural language narrative
        natural_explanation = (
            f"Recommended modal price of ₹{predicted_price:.2f}/quintal for {market} is driven by: "
            f"1) {price_trend_text} "
            f"2) {seasonal_text} "
            f"3) {market_text} "
            f"4) {arrival_text}"
        )

        return {
            "predicted_modal_price": predicted_price,
            "unit": "INR/Quintal",
            "top_influencing_features": top_factors,
            "domain_context": {
                "price_trend_analysis": price_trend_text,
                "seasonal_influence": seasonal_text,
                "market_specifics": market_text,
                "arrival_elasticity": arrival_text
            },
            "natural_language_explanation": natural_explanation,
            "interpretation_notice": (
                "Feature impacts reflect statistical associations learned from historical APMC records, "
                "not causal guarantees. External weather events and transport strikes can alter actual realized prices."
            )
        }


def generate_feature_importance_plot(
    feature_names: List[str],
    importances: np.ndarray,
    output_path: str = "outputs/graphs/feature_importance.png",
    top_n: int = 15
):
    """
    Renders and saves a clean, publication-grade feature importance bar chart.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Sort top features
    indices = np.argsort(importances)[::-1][:top_n]
    top_feats = [feature_names[i] for i in indices][::-1]
    top_vals = [importances[i] for i in indices][::-1]
    
    plt.figure(figsize=(10, 6))
    bars = plt.barh(top_feats, top_vals, color="#16a085", edgecolor="#0e6655")
    plt.xlabel("Relative Importance Score", fontsize=11)
    plt.title("AgriVision AI: Top Features Driving Price Predictions", fontsize=13, fontweight="bold")
    plt.grid(axis="x", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    logger.info("Feature importance plot saved to %s", output_path)
