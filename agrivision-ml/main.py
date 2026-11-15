"""
main.py
-------
AgriVision AI - Agricultural Price Intelligence & Demand Forecasting
Build Beyond'26 - BMS College of Engineering
Member 2 - AI & Data Science

End-to-End Orchestrator:
Executes Data Acquisition -> Preprocessing -> Feature Engineering ->
Price Model Benchmarking -> Demand Forecasting -> Explainability ->
Model Evaluation Reports -> Visualizations.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.data_collection import acquire_data
from src.data_preprocessing import preprocess_dataset
from src.feature_engineering import engineer_dataset
from src.price_prediction import train_and_evaluate_price_models
from src.demand_forecasting import train_demand_forecasting_model
from src.explainability import AgriExplainer, generate_feature_importance_plot
from src.evaluation import (
    plot_historical_price_trends,
    plot_forecast_uncertainty,
    generate_structured_evaluation_report
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AgriVision-Main")


def run_pipeline(
    crop: str = "Tomato",
    raw_dir: str = "data/raw",
    processed_dir: str = "data/processed",
    models_dir: str = "models",
    graphs_dir: str = "outputs/graphs",
    reports_dir: str = "outputs/reports"
):
    """Executes the full machine learning training and evaluation pipeline."""
    start_time = datetime.now()
    print("=" * 80)
    print(" AGRIVISION AI - AGRICULTURAL PRICE INTELLIGENCE & DEMAND FORECASTING")
    print(" Build Beyond'26 | BMS College of Engineering | Member 2: AI & Data Science")
    print("=" * 80)
    
    # 1. Data Collection
    logger.info(">>> STEP 1: Acquiring Agricultural Market Dataset...")
    raw_csv_path = acquire_data(raw_output_dir=raw_dir, crop=crop)
    
    meta_json_path = os.path.join(raw_dir, f"{crop.lower()}_karnataka_raw_meta.json")
    dataset_meta = {}
    if os.path.exists(meta_json_path):
        with open(meta_json_path, "r", encoding="utf-8") as f:
            dataset_meta = json.load(f)

    # 2. Data Preprocessing
    logger.info(">>> STEP 2: Preprocessing and Validating Market Data...")
    clean_csv_path, prep_stats = preprocess_dataset(
        raw_path=raw_csv_path,
        processed_dir=processed_dir,
        crop=crop
    )
    dataset_meta.update(prep_stats)

    # 3. Feature Engineering
    logger.info(">>> STEP 3: Engineering Temporal, Seasonal, Lag, and Rolling Features...")
    df_features = engineer_dataset(clean_csv_path)

    # 4. Price Prediction Models (Baseline, Random Forest, Gradient Boosting)
    logger.info(">>> STEP 4: Training & Benchmarking Agricultural Price Prediction Models...")
    price_predictor, price_metrics = train_and_evaluate_price_models(
        df=df_features,
        models_dir=models_dir,
        graphs_dir=graphs_dir
    )

    # 5. Demand Forecasting Module
    logger.info(">>> STEP 5: Training Demand Pressure Trend Forecaster (Supply Proxy Analysis)...")
    demand_forecaster, demand_metrics = train_demand_forecasting_model(
        df=df_features,
        models_dir=models_dir,
        graphs_dir=graphs_dir
    )

    # 6. Explainable AI & Feature Importance
    logger.info(">>> STEP 6: Generating Explainability Attributions & Feature Importances...")
    explainer = AgriExplainer(
        price_predictor.model,
        price_predictor.preprocessor,
        price_predictor.feature_names
    )
    if hasattr(price_predictor.model, "feature_importances_"):
        generate_feature_importance_plot(
            feature_names=price_predictor.feature_names,
            importances=price_predictor.model.feature_importances_,
            output_path=os.path.join(graphs_dir, "feature_importance.png")
        )

    # 7. Comprehensive Visualizations & Evaluation Reports
    logger.info(">>> STEP 7: Generating Price Trends, Uncertainty Fan-Chart, and Markdown Reports...")
    plot_historical_price_trends(
        clean_csv_path=clean_csv_path,
        output_path=os.path.join(graphs_dir, "price_trends.png")
    )
    plot_forecast_uncertainty(
        predictor=price_predictor,
        clean_csv_path=clean_csv_path,
        output_path=os.path.join(graphs_dir, "forecast_uncertainty.png"),
        market="Kolar",
        forecast_days=14
    )
    report_file = generate_structured_evaluation_report(
        price_metrics=price_metrics,
        demand_metrics=demand_metrics,
        dataset_metadata=dataset_meta,
        reports_dir=reports_dir
    )

    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 80)
    print(" PIPELINE EXECUTION SUCCESSFUL")
    print(f" Execution Time: {elapsed:.2f} seconds")
    print(f" Champion Price Model: {price_metrics.get('best_model')}")
    print(f" Test MAE:  INR {price_metrics.get('test_metrics', {}).get('MAE')}/quintal")
    print(f" Test MAPE: {price_metrics.get('test_metrics', {}).get('MAPE_pct')}%")
    print(f" Test R²:   {price_metrics.get('test_metrics', {}).get('R2')}")
    print(f" Demand Model Accuracy: {demand_metrics.get('accuracy') * 100:.2f}%")
    print(f" Evaluation Report: {report_file}")
    print(" Generated Graphs:")
    print("   - outputs/graphs/price_trends.png")
    print("   - outputs/graphs/actual_vs_predicted.png")
    print("   - outputs/graphs/model_comparison.png")
    print("   - outputs/graphs/feature_importance.png")
    print("   - outputs/graphs/demand_trend.png")
    print("   - outputs/graphs/forecast_uncertainty.png")
    print("\nNext Steps for the Team:")
    print("  1. Run tests:      python -m pytest tests/")
    print("  2. Start API:      python src/api.py")
    print("  3. Django Backend: Connect to http://127.0.0.1:5000/predict-price")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline()
