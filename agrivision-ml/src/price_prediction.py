"""
price_prediction.py
-------------------
AgriVision AI - Agricultural Price Intelligence & Demand Forecasting
Trains, validates, compares, and packages supervised regression models
(Baseline, Random Forest, Gradient Boosting) using chronological data splits.
Computes empirical prediction intervals and exports production artifacts.
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

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.feature_engineering import AgriFeaturePipeline, create_time_features, create_lag_and_rolling_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Computes Mean Absolute Percentage Error (MAPE) safely,
    avoiding division by zero or infinite distortions.
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = (y_true != 0) & (~np.isnan(y_true))
    if np.sum(mask) == 0:
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes MAE, RMSE, MAPE, and R2."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = safe_mape(y_true, y_pred)
    r2 = float(r2_score(y_true, y_pred))
    return {
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE_pct": round(mape, 2),
        "R2": round(r2, 4)
    }


class BaselinePriceModel:
    """
    Historical price baseline: Predicts the recent 7-day rolling mean
    (or lag-1 price if rolling mean is unavailable).
    """
    def __init__(self):
        self.name = "Historical 7-Day Rolling Baseline"
        
    def fit(self, X: pd.DataFrame, y=None):
        return self
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if "price_rolling_mean_7" in X.columns:
            preds = X["price_rolling_mean_7"].values.copy()
        elif "modal_price_lag_1" in X.columns:
            preds = X["modal_price_lag_1"].values.copy()
        else:
            preds = np.zeros(len(X))
        # Fallback if any NaNs remain
        nan_mask = np.isnan(preds)
        if np.any(nan_mask):
            preds[nan_mask] = 1500.0
        return preds


def chronological_train_val_test_split(
    df: pd.DataFrame,
    train_pct: float = 0.70,
    val_pct: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits time-series data chronologically by date across all markets
    to strictly prevent future information leakage into training.
    """
    unique_dates = np.sort(df["date"].unique())
    n_dates = len(unique_dates)
    
    train_end_idx = int(n_dates * train_pct)
    val_end_idx = int(n_dates * (train_pct + val_pct))
    
    train_dates = unique_dates[:train_end_idx]
    val_dates = unique_dates[train_end_idx:val_end_idx]
    test_dates = unique_dates[val_end_idx:]
    
    train_df = df[df["date"].isin(train_dates)].copy()
    val_df = df[df["date"].isin(val_dates)].copy()
    test_df = df[df["date"].isin(test_dates)].copy()
    
    logger.info("Chronological Split Summary:")
    logger.info("  Train: %s to %s (%d rows)",
                pd.to_datetime(train_dates[0]).strftime("%Y-%m-%d"),
                pd.to_datetime(train_dates[-1]).strftime("%Y-%m-%d"), len(train_df))
    logger.info("  Val:   %s to %s (%d rows)",
                pd.to_datetime(val_dates[0]).strftime("%Y-%m-%d"),
                pd.to_datetime(val_dates[-1]).strftime("%Y-%m-%d"), len(val_df))
    logger.info("  Test:  %s to %s (%d rows)",
                pd.to_datetime(test_dates[0]).strftime("%Y-%m-%d"),
                pd.to_datetime(test_dates[-1]).strftime("%Y-%m-%d"), len(test_df))
                
    return train_df, val_df, test_df


class PricePredictor:
    """
    Unified Price Predictor encapsulating preprocessor, best model,
    empirical prediction intervals, and metadata.
    """
    def __init__(self, model_name: str = "RandomForest", model=None, preprocessor=None):
        self.model_name = model_name
        self.model = model
        self.preprocessor = preprocessor
        self.residual_std: float = 120.0
        self.version: str = "1.0.0"
        self.feature_names: List[str] = []
        
    def predict_with_interval(
        self,
        X_df: pd.DataFrame,
        confidence_level: float = 0.80
    ) -> List[Dict[str, Any]]:
        """
        Produces price prediction with uncertainty bounds.
        If Random Forest: utilizes tree-ensemble variance.
        If Gradient Boosting: utilizes empirical residual quantiles.
        """
        X_proc = self.preprocessor.transform(X_df)
        preds = self.model.predict(X_proc)
        
        results = []
        if isinstance(self.model, RandomForestRegressor):
            # Compute tree-wise predictions for true empirical ensemble variance
            tree_preds = np.array([tree.predict(X_proc.values) for tree in self.model.estimators_])
            lower_pct = (1.0 - confidence_level) / 2.0 * 100.0
            upper_pct = (1.0 + confidence_level) / 2.0 * 100.0
            lower_bounds = np.percentile(tree_preds, lower_pct, axis=0)
            upper_bounds = np.percentile(tree_preds, upper_pct, axis=0)
        else:
            # Gaussian interval using residual standard error
            z_score = 1.28 if confidence_level == 0.80 else 1.96
            margin = z_score * self.residual_std
            lower_bounds = np.maximum(100.0, preds - margin)
            upper_bounds = preds + margin
            
        for i in range(len(preds)):
            pred_val = float(np.round(preds[i], 2))
            low_val = float(np.round(max(100.0, lower_bounds[i]), 2))
            up_val = float(np.round(max(pred_val, upper_bounds[i]), 2))
            results.append({
                "predicted_modal_price": pred_val,
                "unit": "INR/Quintal",
                "prediction_interval": {
                    "confidence_level": f"{int(confidence_level * 100)}%",
                    "lower_bound": low_val,
                    "upper_bound": up_val
                },
                "uncertainty_disclaimer": (
                    "Agricultural prices are subject to weather events, fuel costs, and supply surges. "
                    "This interval represents model confidence based on historical APMC variance, not absolute certainty."
                )
            })
        return results


def train_and_evaluate_price_models(
    df: pd.DataFrame,
    models_dir: str = "models",
    graphs_dir: str = "outputs/graphs",
    random_state: int = 42
) -> Tuple[PricePredictor, Dict[str, Any]]:
    """
    Trains Baseline, Random Forest, and Gradient Boosting models on chronological splits,
    selects the champion model on the validation set, and reports test metrics honestly.
    """
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(graphs_dir, exist_ok=True)
    
    train_df, val_df, test_df = chronological_train_val_test_split(df)
    
    # Fit preprocessor strictly on training data
    preprocessor = AgriFeaturePipeline()
    preprocessor.fit(train_df)
    
    X_train = preprocessor.transform(train_df)
    y_train = train_df["modal_price"].values
    
    X_val = preprocessor.transform(val_df)
    y_val = val_df["modal_price"].values
    
    X_test = preprocessor.transform(test_df)
    y_test = test_df["modal_price"].values
    
    # 1. Baseline Model
    baseline = BaselinePriceModel()
    baseline.fit(train_df)
    baseline_val_preds = baseline.predict(val_df)
    baseline_test_preds = baseline.predict(test_df)
    baseline_val_metrics = evaluate_predictions(y_val, baseline_val_preds)
    baseline_test_metrics = evaluate_predictions(y_test, baseline_test_preds)
    
    # 2. Random Forest Regressor
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_val_preds = rf.predict(X_val)
    rf_test_preds = rf.predict(X_test)
    rf_val_metrics = evaluate_predictions(y_val, rf_val_preds)
    rf_test_metrics = evaluate_predictions(y_test, rf_test_preds)
    
    # 3. Gradient Boosting Regressor
    gbr = GradientBoostingRegressor(
        n_estimators=120,
        learning_rate=0.08,
        max_depth=5,
        random_state=random_state
    )
    gbr.fit(X_train, y_train)
    gbr_val_preds = gbr.predict(X_val)
    gbr_test_preds = gbr.predict(X_test)
    gbr_val_metrics = evaluate_predictions(y_val, gbr_val_preds)
    gbr_test_metrics = evaluate_predictions(y_test, gbr_test_preds)
    
    model_comparison = {
        "Baseline": {"val": baseline_val_metrics, "test": baseline_test_metrics},
        "RandomForest": {"val": rf_val_metrics, "test": rf_test_metrics},
        "GradientBoosting": {"val": gbr_val_metrics, "test": gbr_test_metrics}
    }
    
    logger.info("Validation Comparison: Baseline MAE=%.2f | RF MAE=%.2f | GBR MAE=%.2f",
                baseline_val_metrics["MAE"], rf_val_metrics["MAE"], gbr_val_metrics["MAE"])
                
    # Model Selection: select best model based on validation MAE
    candidates = [
        ("RandomForest", rf, rf_val_metrics, rf_test_metrics, rf_test_preds),
        ("GradientBoosting", gbr, gbr_val_metrics, gbr_test_metrics, gbr_test_preds)
    ]
    candidates.sort(key=lambda c: c[2]["MAE"])
    best_name, best_model, best_val_m, best_test_m, best_test_preds = candidates[0]
    
    logger.info("Best model selected: %s (Validation MAE: %.2f, Test MAE: %.2f)",
                best_name, best_val_m["MAE"], best_test_m["MAE"])
                
    # Calculate residual standard deviation on validation set for intervals
    val_residuals = y_val - (rf_val_preds if best_name == "RandomForest" else gbr_val_preds)
    residual_std = float(np.std(val_residuals))
    
    # Build package predictor
    predictor = PricePredictor(model_name=best_name, model=best_model, preprocessor=preprocessor)
    predictor.residual_std = residual_std
    predictor.feature_names = preprocessor.all_feature_names
    
    # Save artifacts
    model_path = os.path.join(models_dir, "price_model.joblib")
    preproc_path = os.path.join(models_dir, "price_preprocessor.joblib")
    metrics_path = os.path.join(models_dir, "price_model_metrics.json")
    
    joblib.dump(best_model, model_path)
    joblib.dump(preprocessor, preproc_path)
    
    metrics_summary = {
        "best_model": best_name,
        "validation_metrics": best_val_m,
        "test_metrics": best_test_m,
        "residual_std": round(residual_std, 2),
        "all_models": model_comparison,
        "feature_count": len(preprocessor.all_feature_names),
        "split_sizes": {
            "train": len(train_df),
            "validation": len(val_df),
            "test": len(test_df)
        }
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
        
    # Generate Plots
    # 1. Model comparison plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    models = ["Baseline", "RandomForest", "GradientBoosting"]
    val_maes = [model_comparison[m]["val"]["MAE"] for m in models]
    test_maes = [model_comparison[m]["test"]["MAE"] for m in models]
    
    x = np.arange(len(models))
    width = 0.35
    axes[0].bar(x - width/2, val_maes, width, label="Val MAE (₹)", color="#3498db")
    axes[0].bar(x + width/2, test_maes, width, label="Test MAE (₹)", color="#2ecc71")
    axes[0].set_ylabel("MAE (₹/Quintal)")
    axes[0].set_title("Model Comparison - Mean Absolute Error")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(models)
    axes[0].legend()
    axes[0].grid(axis="y", linestyle="--", alpha=0.7)
    
    test_r2s = [model_comparison[m]["test"]["R2"] for m in models]
    axes[1].bar(models, test_r2s, color=["#95a5a6", "#9b59b6", "#e67e22"], width=0.5)
    axes[1].set_ylabel("Test R² Score")
    axes[1].set_title("Test R² Performance")
    axes[1].set_ylim([max(0, min(test_r2s) - 0.1), 1.0])
    axes[1].grid(axis="y", linestyle="--", alpha=0.7)
    
    plt.tight_layout()
    comparison_graph = os.path.join(graphs_dir, "model_comparison.png")
    plt.savefig(comparison_graph, dpi=200)
    plt.close()
    
    # 2. Actual vs Predicted on Test Set (for dominant market like Kolar)
    test_df_eval = test_df.copy()
    test_df_eval["predicted_price"] = best_test_preds
    
    # Select Kolar or first available market for clear chronological visual
    sample_mkt = "Kolar" if "Kolar" in test_df_eval["market"].values else test_df_eval["market"].iloc[0]
    mkt_sub = test_df_eval[test_df_eval["market"] == sample_mkt].sort_values("date")
    
    plt.figure(figsize=(12, 6))
    plt.plot(mkt_sub["date"], mkt_sub["modal_price"], label="Actual Modal Price", color="#e74c3c", linewidth=2)
    plt.plot(mkt_sub["date"], mkt_sub["predicted_price"], label=f"Predicted ({best_name})", color="#2980b9", linestyle="--", linewidth=2)
    
    # Prediction interval band
    margin = 1.28 * residual_std
    plt.fill_between(
        mkt_sub["date"],
        mkt_sub["predicted_price"] - margin,
        mkt_sub["predicted_price"] + margin,
        color="#3498db",
        alpha=0.2,
        label="80% Prediction Interval Band"
    )
    plt.title(f"AgriVision AI: Actual vs Predicted Tomato Modal Price ({sample_mkt} APMC)", fontsize=14, fontweight="bold")
    plt.xlabel("Date", fontsize=11)
    plt.ylabel("Modal Price (₹/Quintal)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    actual_vs_pred_graph = os.path.join(graphs_dir, "actual_vs_predicted.png")
    plt.savefig(actual_vs_pred_graph, dpi=200)
    plt.close()
    
    logger.info("Saved prediction artifacts to %s and graphs to %s", models_dir, graphs_dir)
    return predictor, metrics_summary


if __name__ == "__main__":
    from src.feature_engineering import engineer_dataset
    df_feat = engineer_dataset("../data/processed/clean_tomato_data.csv")
    predictor, metrics = train_and_evaluate_price_models(df_feat, models_dir="../models", graphs_dir="../outputs/graphs")
    print("Price model training completed.")
    print("Metrics:", json.dumps(metrics, indent=2))
