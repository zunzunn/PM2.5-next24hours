"""
Milestone 2 Verification Script
Trains and validates the 24-hour multi-horizon models, checks metrics,
verifies outperformance against persistence baseline, and validates serialized artifacts.
"""

import sys
import json
import joblib
import numpy as np
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.ml.trainer import train_and_evaluate_all, ARTIFACTS_DIR

def run_verification():
    print("=" * 65)
    print("RUNNING MILESTONE 2 VERIFICATION")
    print("=" * 65)

    # 1. Run full training and evaluation suite
    metrics = train_and_evaluate_all()

    # 2. Assert all 4 models evaluated
    expected_models = ["Persistence Baseline", "Random Forest", "XGBoost", "LSTM"]
    for m in expected_models:
        assert m in metrics, f"Model {m} missing from evaluation results"
        assert "rmse" in metrics[m], f"RMSE missing for {m}"
        assert "mae" in metrics[m], f"MAE missing for {m}"
        assert "r2" in metrics[m], f"R2 missing for {m}"
        assert len(metrics[m]["horizons"]) == 24, f"Expected 24 horizon metrics for {m}, got {len(metrics[m]['horizons'])}"

    # 3. Assert ML outperforms persistence baseline
    base_rmse = metrics["Persistence Baseline"]["rmse"]
    best_ml_rmse = min(metrics["Random Forest"]["rmse"], metrics["XGBoost"]["rmse"], metrics["LSTM"]["rmse"])
    assert best_ml_rmse < base_rmse, f"Best ML model ({best_ml_rmse}) did not beat persistence baseline ({base_rmse})"
    print(f"\n✓ Verified ML Superiority: Best ML model RMSE ({best_ml_rmse} µg/m³) outperforms Persistence Baseline ({base_rmse} µg/m³).")

    # 4. Check serialized artifacts existence and integrity
    required_files = [
        "scaler.joblib",
        "random_forest.joblib",
        "xgboost.joblib",
        "lstm_weights.pt",
        "model_metrics.json",
        "feature_importance.json",
        "forecast_comparison_sample.json",
        "feature_metadata.json"
    ]
    for filename in required_files:
        fpath = ARTIFACTS_DIR / filename
        assert fpath.exists(), f"Artifact {filename} missing at {fpath}"
        assert fpath.stat().st_size > 0, f"Artifact {filename} is empty"
    print(f"✓ Verified all 8 serialized model artifacts in {ARTIFACTS_DIR}.")

    # 5. Test model loading and single inference
    scaler = joblib.load(ARTIFACTS_DIR / "scaler.joblib")
    rf = joblib.load(ARTIFACTS_DIR / "random_forest.joblib")
    xgb = joblib.load(ARTIFACTS_DIR / "xgboost.joblib")
    
    with open(ARTIFACTS_DIR / "feature_metadata.json") as f:
        meta = json.load(f)
    n_features = len(meta["features"])
    
    dummy_input = np.ones((1, n_features))
    dummy_scaled = scaler.transform(dummy_input)
    
    pred_rf = rf.predict(dummy_scaled)
    pred_xgb = xgb.predict(dummy_scaled)
    
    assert pred_rf.shape == (1, 24), f"RF prediction shape mismatch: {pred_rf.shape}"
    assert pred_xgb.shape == (1, 24), f"XGB prediction shape mismatch: {pred_xgb.shape}"
    print(f"✓ Model reloading and single inference test passed (Output shape: {pred_xgb.shape}).")

    print("\n=======================================================")
    print("SUCCESS: ALL MILESTONE 2 CHECKS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    run_verification()
