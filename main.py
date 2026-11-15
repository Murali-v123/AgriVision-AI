"""
Root Entrypoint for AgriVision AI
=================================
Orchestrates ML pipeline training and the Flask microservice.

Usage:
  python main.py          -> Run end-to-end ML training & evaluation pipeline
  python main.py --serve  -> Start Flask ML microservice on port 5000
  python main.py --train  -> Retrain models & generate visualizations
"""
import os
import sys
from src.api import app, load_artifacts

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agrivision-ml")
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)



if __name__ == "__main__":
    os.chdir(base_dir)

    if "--serve" in sys.argv or "-s" in sys.argv:
        
        load_artifacts()
        port = int(os.environ.get("PORT", 5000))
        print(f"Starting AgriVision AI ML API on port {port}...")
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        from main import run_pipeline
        run_pipeline()
