"""
Feature Engineering Module for Multi-Horizon 24-Hour PM2.5 Forecasting
Constructs:
- Multi-horizon targets: [y_{t+1}, y_{t+2}, ..., y_{t+24}]
- Cyclical trigonometric temporal encodings (hour, day of week, month)
- Strict historical lag variables (t, t-1, t-2, t-3, t-6, t-12, t-24, t-48)
- Rolling window statistics strictly over past observations (no future leakage)
- Co-pollutant and weather interaction features
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any

def create_multi_horizon_features(
    df: pd.DataFrame,
    horizon_hours: int = 24,
    target_col: str = "PM2.5"
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str], List[str]]:
    """
    Transforms clean continuous hourly time-series into (X, Y) pairs for 24-hour ahead forecasting.
    
    Guarantees:
    - Every feature at row index i uses strictly information available at or before timestamp i.
    - Targets Y at row index i represent PM2.5 values at timestamps i+1 to i+horizon_hours.
    """
    data = df.copy()
    if not isinstance(data.index, pd.DatetimeIndex):
        if "timestamp" in data.columns:
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data = data.sort_values("timestamp").reset_index(drop=True)
        else:
            raise ValueError("DataFrame must contain a 'timestamp' column or DatetimeIndex")

    # 1. Cyclical trigonometric time encodings
    hour = data["timestamp"].dt.hour
    dow = data["timestamp"].dt.dayofweek
    month = data["timestamp"].dt.month

    data["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    data["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    data["dow_sin"] = np.sin(2 * np.pi * dow / 7.0)
    data["dow_cos"] = np.cos(2 * np.pi * dow / 7.0)
    data["month_sin"] = np.sin(2 * np.pi * month / 12.0)
    data["month_cos"] = np.cos(2 * np.pi * month / 12.0)

    # 2. Historical Lags of PM2.5 (strictly past values)
    lags = [0, 1, 2, 3, 6, 12, 24, 48]
    for lag in lags:
        if lag == 0:
            data[f"{target_col}_lag0"] = data[target_col]
        else:
            data[f"{target_col}_lag{lag}"] = data[target_col].shift(lag)

    # 3. Rolling window statistics of PM2.5 (strictly over past values)
    # Using shift(0) means including current time t; to ensure causality, rolling on lag0 is fine at prediction time
    data[f"{target_col}_roll_mean_6h"] = data[target_col].rolling(window=6, min_periods=6).mean()
    data[f"{target_col}_roll_std_6h"] = data[target_col].rolling(window=6, min_periods=6).std()
    data[f"{target_col}_roll_mean_24h"] = data[target_col].rolling(window=24, min_periods=24).mean()
    data[f"{target_col}_roll_std_24h"] = data[target_col].rolling(window=24, min_periods=24).std()
    data[f"{target_col}_roll_min_24h"] = data[target_col].rolling(window=24, min_periods=24).min()
    data[f"{target_col}_roll_max_24h"] = data[target_col].rolling(window=24, min_periods=24).max()

    # 4. Co-pollutants and weather features at time t
    co_features = ["PM10", "NO2", "SO2", "CO", "Ozone", "AT", "RH", "WS", "WD"]
    available_co = [c for c in co_features if c in data.columns]
    
    # 24h lags for key co-pollutants
    for c in ["PM10", "NO2", "AT", "RH"]:
        if c in data.columns:
            data[f"{c}_lag24"] = data[c].shift(24)

    # 5. Multi-Horizon Targets: [t+1, t+2, ..., t+horizon_hours]
    target_cols = []
    for h in range(1, horizon_hours + 1):
        col_name = f"target_h{h}"
        data[col_name] = data[target_col].shift(-h)
        target_cols.append(col_name)

    # Also build persistence baseline features for every horizon:
    # Day-ahead diurnal persistence: y_hat_{t+h} = y_{t+h-24}
    # For h in 1..24, t+h-24 is in the past! (e.g. h=1 -> t-23, h=24 -> t-0)
    for h in range(1, horizon_hours + 1):
        past_shift = 24 - h
        data[f"persistence_h{h}"] = data[target_col].shift(past_shift)

    # Drop warmup rows (from 48-hour lag) and trailing rows (from 24-hour ahead target shifting)
    valid_data = data.dropna().reset_index(drop=True)

    # Identify feature columns
    excluded_cols = set(target_cols + [f"persistence_h{h}" for h in range(1, horizon_hours + 1)] + ["timestamp"])
    feature_cols = [c for c in valid_data.columns if c not in excluded_cols]

    X = valid_data[feature_cols].copy()
    Y = valid_data[target_cols].copy()
    persistence = valid_data[[f"persistence_h{h}" for h in range(1, horizon_hours + 1)]].copy()

    return valid_data, X, Y, persistence, feature_cols, target_cols

def chronological_split(
    X: pd.DataFrame,
    Y: pd.DataFrame,
    persistence: pd.DataFrame,
    train_pct: float = 0.70,
    val_pct: float = 0.15
) -> Dict[str, Any]:
    """
    Strict chronological split into Train, Validation, and Holdout Test partitions.
    Never random shuffling.
    """
    n = len(X)
    train_end = int(n * train_pct)
    val_end = int(n * (train_pct + val_pct))

    splits = {
        "X_train": X.iloc[:train_end].copy(),
        "Y_train": Y.iloc[:train_end].copy(),
        "persist_train": persistence.iloc[:train_end].copy(),

        "X_val": X.iloc[train_end:val_end].copy(),
        "Y_val": Y.iloc[train_end:val_end].copy(),
        "persist_val": persistence.iloc[train_end:val_end].copy(),

        "X_test": X.iloc[val_end:].copy(),
        "Y_test": Y.iloc[val_end:].copy(),
        "persist_test": persistence.iloc[val_end:].copy(),
        
        "indices": {
            "train": (0, train_end),
            "val": (train_end, val_end),
            "test": (val_end, n)
        }
    }
    return splits
