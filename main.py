"""
Root Entrypoint for AgriVision AI
Forwards execution to agrivision-ml/main.py
"""
import os
import sys
import subprocess

if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agrivision-ml")
    os.chdir(base_dir)
    sys.path.insert(0, base_dir)
    from main import run_pipeline
    run_pipeline()
