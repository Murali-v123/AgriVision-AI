"""
demand_forecasting.py
---------------------
AgriVision AI - Agricultural Price Intelligence & Demand Forecasting
Forecasts short-term market demand pressure trends using arrival dynamics,
price elasticity proxies, and seasonal cycles. Explicitly documents
supply-proxy limitations.
"""

import os
import json
import logging
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEMAND_LIMITATION_NOTICE = (
    "Agricultural Market Proxy Notice: APMC mandi arrivals represent physical wholesale "
    "market supply volume, NOT final retail consumer demand. Genuine household consumption data "
    "is unavailable in government mandi records. This module computes a Market Absorption & Demand "
    "Pressure Index proxy based on arrival velocity, price elasticity, and seasonal clearance rates."
)


def compute_demand_pressure_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes a grounded 7-day forward demand-pressure trend label:
    - 'Increasing': Forward 7-day market absorption is expanding (prices holding or rising relative to arrivals).
    - 'Decreasing': Forward 7-day market absorption is softening (high supply glut or downward price-volume momentum).
    - 'Stable': Supply-demand equilibrium within ±3% volume-price threshold.
    """
    df = df.copy()
    grouped = df.groupby("market")
    
    # 7-day forward arrivals change
    fwd_arrivals_change = (grouped["arrivals_qtl"].shift(-7) - df["arrivals_qtl"]) / (df["arrivals_qtl"] + 1e-5)
    fwd_price_change = (grouped["modal_price"].shift(-7) - df["modal_price"]) / (df["modal_price"] + 1e-5)
    
    # Demand pressure proxy score
    # High demand pressure = price holding up (+), volume clearing (+)
    demand_proxy_score = fwd_price_change + 0.5 * fwd_arrivals_change
    
    conditions = [
        demand_proxy_score > 0.05,
        demand_proxy_score < -0.05
    ]
    choices = ["Increasing", "Decreasing"]
    df["demand_trend_target"] = np.select(conditions, choices, default="Stable")
    
    # Drop trailing rows where forward shift is NaN
    df = df.dropna(subset=["demand_trend_target"]).copy()
    return df


class DemandForecaster:
    """
    Demand Trend Forecaster using Random Forest Classifier on engineered features.
    """
    def __init__(self, model=None, label_encoder=None, feature_cols=None):
        self.model = model
        self.label_encoder = label_encoder
        self.feature_cols = feature_cols or []
        self.version = "1.0.0"
        self.limitation_notice = DEMAND_LIMITATION_NOTICE
        
    def forecast(self, X_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predicts demand trend and confidence for input feature records.
        """
        # Ensure required numeric feature columns exist
        X_eval = X_df.copy()
        for col in self.feature_cols:
            if col not in X_eval.columns:
                X_eval[col] = 0.0
                
        X_mat = X_eval[self.feature_cols]
        probs = self.model.predict_proba(X_mat)
        pred_indices = np.argmax(probs, axis=1)
        pred_labels = self.label_encoder.inverse_transform(pred_indices)
        confidences = np.max(probs, axis=1)
        
        results = []
        for i in range(len(pred_labels)):
            trend = pred_labels[i]
            conf = float(np.round(confidences[i], 3))
            
            # Grounded economic interpretation
            if trend == "Increasing":
                interpretation = (
                    "Market absorption capacity is projected to expand over the next 7 days. "
                    "Wholesale buyers and food processors are absorbing incoming stock rapidly."
                )
            elif trend == "Decreasing":
                interpretation = (
                    "Market demand absorption is softening or high arrivals are outpacing local clearing capacity. "
                    "Risk of mandi stock accumulation."
                )
            else:
                interpretation = (
                    "Supply and wholesale clearance are in relative equilibrium. "
                    "Normal seasonal consumption velocity expected."
                )
                
            results.append({
                "demand_trend": trend,
                "confidence_score": conf,
                "confidence_percentage": f"{int(conf * 100)}%",
                "economic_interpretation": interpretation,
                "proxy_disclaimer": self.limitation_notice
            })
        return results


def train_demand_forecasting_model(
    df: pd.DataFrame,
    models_dir: str = "models",
    graphs_dir: str = "outputs/graphs",
    random_state: int = 42
) -> Tuple[DemandForecaster, Dict[str, Any]]:
    """
    Prepares demand proxy target, trains classifier, evaluates, saves artifacts and plots.
    """
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(graphs_dir, exist_ok=True)
    
    df_labeled = compute_demand_pressure_target(df)
    
    # Chronological train/test split on unique dates
    unique_dates = np.sort(df_labeled["date"].unique())
    split_idx = int(len(unique_dates) * 0.80)
    train_dates = unique_dates[:split_idx]
    test_dates = unique_dates[split_idx:]
    
    train_df = df_labeled[df_labeled["date"].isin(train_dates)].copy()
    test_df = df_labeled[df_labeled["date"].isin(test_dates)].copy()
    
    feature_cols = [
        "month", "week", "day_of_week",
        "modal_price_lag_1", "modal_price_lag_7",
        "arrivals_lag_1", "arrivals_lag_7",
        "price_rolling_mean_7", "arrivals_rolling_mean_7",
        "price_momentum_7d", "price_ratio_to_7d_mean", "arrival_ratio_to_7d_mean"
    ]
    
    le = LabelEncoder()
    y_train = le.fit_transform(train_df["demand_trend_target"])
    y_test = le.transform(test_df["demand_trend_target"])
    
    X_train = train_df[feature_cols].fillna(0)
    X_test = test_df[feature_cols].fillna(0)
    
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=6,
        random_state=random_state,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    
    test_preds = clf.predict(X_test)
    acc = float(accuracy_score(y_test, test_preds))
    report = classification_report(y_test, test_preds, target_names=le.classes_, output_dict=True)
    
    logger.info("Demand Model Test Accuracy: %.2f%%", acc * 100.0)
    
    forecaster = DemandForecaster(model=clf, label_encoder=le, feature_cols=feature_cols)
    
    # Save model artifacts
    model_path = os.path.join(models_dir, "demand_model.joblib")
    joblib.dump(forecaster, model_path)
    
    metrics = {
        "model_type": "Random Forest Classifier (7-Day Demand Pressure Trend)",
        "accuracy": round(acc, 4),
        "classes": list(le.classes_),
        "classification_report": report,
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "limitation_statement": DEMAND_LIMITATION_NOTICE
    }
    
    with open(os.path.join(models_dir, "demand_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    # Generate Demand Trend & Supply Proxy Graph
    mkt_name = "Kolar" if "Kolar" in df_labeled["market"].values else df_labeled["market"].iloc[0]
    sample_df = df_labeled[df_labeled["market"] == mkt_name].sort_values("date").tail(120)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color_price = "#c0392b"
    ax1.set_xlabel("Date", fontsize=11)
    ax1.set_ylabel("Modal Price (₹/Quintal)", color=color_price, fontsize=11)
    ax1.plot(sample_df["date"], sample_df["modal_price"], color=color_price, linewidth=2, label="Modal Price")
    ax1.tick_params(axis="y", labelcolor=color_price)
    ax1.grid(True, linestyle="--", alpha=0.5)
    
    ax2 = ax1.twinx()
    color_arrivals = "#2980b9"
    ax2.set_ylabel("Wholesale Arrivals (Quintals - Supply Proxy)", color=color_arrivals, fontsize=11)
    ax2.fill_between(sample_df["date"], sample_df["arrivals_qtl"], color=color_arrivals, alpha=0.25, label="Arrivals (Supply Proxy)")
    ax2.tick_params(axis="y", labelcolor=color_arrivals)
    
    plt.title(f"AgriVision AI: Demand Pressure & Supply Volume Dynamics ({mkt_name} APMC)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    
    graph_path = os.path.join(graphs_dir, "demand_trend.png")
    plt.savefig(graph_path, dpi=200)
    plt.close()
    
    logger.info("Demand model artifacts saved to %s and graph saved to %s", models_dir, graph_path)
    return forecaster, metrics


if __name__ == "__main__":
    from src.feature_engineering import engineer_dataset
    df_feat = engineer_dataset("../data/processed/clean_tomato_data.csv")
    forecaster, metrics = train_demand_forecasting_model(df_feat, models_dir="../models", graphs_dir="../outputs/graphs")
    print("Demand forecasting training complete. Accuracy:", metrics["accuracy"])
