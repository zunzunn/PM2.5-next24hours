"""
Model Training & Benchmarking Pipeline
Trains:
- Persistence Baseline
- Random Forest Regressor
- XGBoost Regressor
- PyTorch LSTM
Evaluates chronologically on unseen test data and exports serialized model artifacts.
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler

import torch
torch.set_num_threads(1)

from backend.config import INDIA_DATA_DIR, BASE_DIR
from backend.ml.features import create_multi_horizon_features, chronological_split
from backend.ml.models import (
    PersistenceBaselineModel,
    create_random_forest_model,
    create_xgboost_model,
    LSTMForecaster,
    compute_regression_metrics
)

ARTIFACTS_DIR = BASE_DIR / "backend" / "ml" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def train_and_evaluate_all():
    print("=" * 65)
    print("MILESTONE 2: TRAINING 24-HOUR MULTI-HORIZON ML FORECASTING SUITE")
    print("=" * 65)

    # 1. Load curated Indian dataset
    csv_path = INDIA_DATA_DIR / "bengaluru_hourly.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}. Run Milestone 1 first.")

    raw_df = pd.read_csv(csv_path)
    print(f"[Step 1/6] Ingesting Bengaluru dataset: {len(raw_df):,} hourly records.")

    # 2. Engineer multi-horizon features
    print("[Step 2/6] Engineering 24-hour targets, temporal encodings, and strict causal lags...")
    valid_df, X, Y, persistence, feature_cols, target_cols = create_multi_horizon_features(raw_df, horizon_hours=24)
    print(f"✓ Valid modeling samples: {len(X):,} hours (warmup rows dropped).")
    print(f"✓ Total engineered features : {len(feature_cols)}")
    print(f"✓ Forecasting horizon targets: {len(target_cols)} (h1 through h24)")

    # 3. Strict chronological split (70% train, 15% val, 15% test)
    print("\n[Step 3/6] Applying strict chronological partition (70% Train, 15% Val, 15% Holdout Test)...")
    splits = chronological_split(X, Y, persistence, train_pct=0.70, val_pct=0.15)
    
    X_train, Y_train = splits["X_train"], splits["Y_train"]
    X_val, Y_val = splits["X_val"], splits["Y_val"]
    X_test, Y_test = splits["X_test"], splits["Y_test"]
    persist_test = splits["persist_test"]

    print(f"  • Training set   : {len(X_train):,} hours ({valid_df['timestamp'].iloc[0]} to {valid_df['timestamp'].iloc[len(X_train)-1]})")
    print(f"  • Validation set : {len(X_val):,} hours")
    print(f"  • Holdout Test set: {len(X_test):,} hours ({valid_df['timestamp'].iloc[-len(X_test)]} to {valid_df['timestamp'].iloc[-1]})")

    # 4. Fit Scaler ONLY on Training data (Strict Zero-Leakage)
    print("\n[Step 4/6] Standardizing features using statistics fit strictly on Training split...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    Y_train_np = Y_train.to_numpy()
    Y_val_np = Y_val.to_numpy()
    Y_test_np = Y_test.to_numpy()
    persist_test_np = persist_test.to_numpy()

    # 5. Model Training & Evaluation
    results = {}
    predictions_test = {}

    # 5.1 Persistence Baseline
    print("\n--- [Model 1/4] Persistence Baseline Model (Diurnal y_{t+h-24}) ---")
    persist_preds = persist_test_np
    persist_metrics = compute_regression_metrics(Y_test_np, persist_preds)
    results["Persistence Baseline"] = persist_metrics
    predictions_test["Persistence Baseline"] = persist_preds
    print(f"✓ Persistence Baseline -> RMSE: {persist_metrics['rmse']:.2f} µg/m³ | MAE: {persist_metrics['mae']:.2f} µg/m³ | R²: {persist_metrics['r2']:.3f}")

    # 5.2 Random Forest Regressor
    print("\n--- [Model 2/4] Random Forest Regressor (Multi-Output) ---")
    t0 = time.time()
    rf_model = create_random_forest_model(n_estimators=100, max_depth=12, random_state=42)
    rf_model.fit(X_train_scaled, Y_train_np)
    rf_preds = rf_model.predict(X_test_scaled)
    rf_metrics = compute_regression_metrics(Y_test_np, rf_preds)
    results["Random Forest"] = rf_metrics
    predictions_test["Random Forest"] = rf_preds
    t_rf = time.time() - t0
    print(f"✓ Random Forest -> RMSE: {rf_metrics['rmse']:.2f} µg/m³ | MAE: {rf_metrics['mae']:.2f} µg/m³ | R²: {rf_metrics['r2']:.3f} (Trained in {t_rf:.1f}s)")

    # 5.3 XGBoost Regressor
    print("\n--- [Model 3/4] XGBoost Regressor (Multi-Output) ---")
    t0 = time.time()
    xgb_model = create_xgboost_model(n_estimators=120, max_depth=6, learning_rate=0.08, random_state=42)
    xgb_model.fit(X_train_scaled, Y_train_np)
    xgb_preds = xgb_model.predict(X_test_scaled)
    xgb_metrics = compute_regression_metrics(Y_test_np, xgb_preds)
    results["XGBoost"] = xgb_metrics
    predictions_test["XGBoost"] = xgb_preds
    t_xgb = time.time() - t0
    print(f"✓ XGBoost -> RMSE: {xgb_metrics['rmse']:.2f} µg/m³ | MAE: {xgb_metrics['mae']:.2f} µg/m³ | R²: {xgb_metrics['r2']:.3f} (Trained in {t_xgb:.1f}s)")

    # 5.4 PyTorch LSTM
    print("\n--- [Model 4/4] PyTorch Sequential LSTM ---")
    t0 = time.time()
    lstm_forecaster = LSTMForecaster(input_dim=X_train_scaled.shape[1], hidden_dim=64, output_dim=24, epochs=15, lr=0.005)
    lstm_forecaster.fit(X_train_scaled, Y_train_np, X_val_scaled, Y_val_np)
    lstm_preds = lstm_forecaster.predict(X_test_scaled)
    lstm_metrics = compute_regression_metrics(Y_test_np, lstm_preds)
    results["LSTM"] = lstm_metrics
    predictions_test["LSTM"] = lstm_preds
    t_lstm = time.time() - t0
    print(f"✓ PyTorch LSTM -> RMSE: {lstm_metrics['rmse']:.2f} µg/m³ | MAE: {lstm_metrics['mae']:.2f} µg/m³ | R²: {lstm_metrics['r2']:.3f} (Trained in {t_lstm:.1f}s)")

    # 6. Comparative Benchmark Summary Table
    print("\n" + "=" * 75)
    print(f"{'Model Name':<25} | {'RMSE (µg/m³)':<14} | {'MAE (µg/m³)':<14} | {'R² Score':<12}")
    print("=" * 75)
    for model_name, m in results.items():
        print(f"{model_name:<25} | {m['rmse']:<14.2f} | {m['mae']:<14.2f} | {m['r2']:<12.3f}")
    print("=" * 75)

    base_rmse = results["Persistence Baseline"]["rmse"]
    best_model_name = min(["Random Forest", "XGBoost", "LSTM"], key=lambda k: results[k]["rmse"])
    best_rmse = results[best_model_name]["rmse"]
    pct_gain = ((base_rmse - best_rmse) / base_rmse) * 100
    print(f"★ Best Performer: {best_model_name} with {pct_gain:.1f}% reduction in RMSE over Persistence Baseline!")

    # 7. Extract Feature Importances (from XGBoost / Random Forest)
    print("\n[Step 5/6] Extracting feature importance rankings...")
    mean_importances = xgb_model.feature_importances_
    top_indices = np.argsort(mean_importances)[::-1]
    
    feature_importance_list = [
        {"feature": feature_cols[idx], "importance": round(float(mean_importances[idx]), 4)}
        for idx in top_indices
    ]
    print("Top 8 Influential Features:")
    for item in feature_importance_list[:8]:
        print(f"  • {item['feature']:<20}: {item['importance']*100:.2f}%")

    # 8. Save Serialized Artifacts
    print("\n[Step 6/6] Serializing model weights, scalers, and evaluation metrics...")
    joblib.dump(scaler, ARTIFACTS_DIR / "scaler.joblib")
    joblib.dump(rf_model, ARTIFACTS_DIR / "random_forest.joblib")
    joblib.dump(xgb_model, ARTIFACTS_DIR / "xgboost.joblib")
    import torch
    torch.save(lstm_forecaster.model.state_dict(), ARTIFACTS_DIR / "lstm_weights.pt")

    # Metadata & Metrics JSON
    with open(ARTIFACTS_DIR / "model_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    with open(ARTIFACTS_DIR / "feature_importance.json", "w") as f:
        json.dump(feature_importance_list, f, indent=2)

    metadata = {
        "dataset": "Bengaluru_BTM_Layout_XKDR",
        "station_id": "site_162",
        "num_train_hours": len(X_train),
        "num_val_hours": len(X_val),
        "num_test_hours": len(X_test),
        "features": feature_cols,
        "targets": target_cols,
        "best_model": best_model_name,
        "rmse_gain_pct": round(pct_gain, 1),
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(ARTIFACTS_DIR / "feature_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # 24-hour test window forecast sample comparison for frontend charts
    test_dates = valid_df["timestamp"].iloc[-len(X_test):].reset_index(drop=True)
    sample_idx = -24  # last 24 hours
    sample_origin_timestamp = str(test_dates.iloc[sample_idx])
    
    sample_actual = [float(x) for x in Y_test_np[sample_idx]]
    sample_persist = [float(x) for x in persist_test_np[sample_idx]]
    sample_rf = [float(x) for x in rf_preds[sample_idx]]
    sample_xgb = [float(x) for x in xgb_preds[sample_idx]]
    sample_lstm = [float(x) for x in lstm_preds[sample_idx]]

    comparison_sample = {
        "origin_timestamp": sample_origin_timestamp,
        "horizons": [
            {
                "hour": h + 1,
                "horizon_label": f"+{h+1}h",
                "actual": round(sample_actual[h], 1),
                "persistence": round(sample_persist[h], 1),
                "random_forest": round(sample_rf[h], 1),
                "xgboost": round(sample_xgb[h], 1),
                "lstm": round(sample_lstm[h], 1)
            }
            for h in range(24)
        ]
    }
    with open(ARTIFACTS_DIR / "forecast_comparison_sample.json", "w") as f:
        json.dump(comparison_sample, f, indent=2)

    print(f"✓ Successfully exported all artifacts to: {ARTIFACTS_DIR}")
    print("=" * 65)
    return results

if __name__ == "__main__":
    train_and_evaluate_all()
