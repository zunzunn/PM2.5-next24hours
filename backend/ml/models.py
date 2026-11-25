"""
Machine Learning & Deep Learning Model Architectures for 24-Hour PM2.5 Forecasting
Algorithms:
1. Persistence Baseline (Diurnal y_{t+h-24})
2. Random Forest Regressor (Multi-Output)
3. XGBoost Regressor (Multi-Output)
4. LSTM Recurrent Neural Network (PyTorch Sequential Multi-Horizon)
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import torch
torch.set_num_threads(1)
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# ==============================================================================
# 1. EVALUATION METRICS UTILITY
# ==============================================================================
def compute_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """
    Computes RMSE, MAE, and R² overall across all 24 horizons,
    as well as individual horizon milestones (1h, 6h, 12h, 24h).
    """
    # Clip negative predictions to 0 for physical realism
    y_pred_clipped = np.clip(y_pred, a_min=0.0, a_max=None)
    
    overall_rmse = float(np.sqrt(mean_squared_error(y_true, y_pred_clipped)))
    overall_mae = float(mean_absolute_error(y_true, y_pred_clipped))
    overall_r2 = float(r2_score(y_true, y_pred_clipped))

    horizon_metrics = {}
    n_horizons = y_true.shape[1] if len(y_true.shape) > 1 else 1
    
    for h in range(n_horizons):
        yt_h = y_true[:, h]
        yp_h = y_pred_clipped[:, h]
        h_num = h + 1
        horizon_metrics[f"h{h_num}"] = {
            "rmse": round(float(np.sqrt(mean_squared_error(yt_h, yp_h))), 2),
            "mae": round(float(mean_absolute_error(yt_h, yp_h)), 2),
            "r2": round(float(r2_score(yt_h, yp_h)), 3)
        }

    return {
        "rmse": round(overall_rmse, 2),
        "mae": round(overall_mae, 2),
        "r2": round(overall_r2, 3),
        "horizons": horizon_metrics
    }

# ==============================================================================
# 2. PERSISTENCE BASELINE MODEL
# ==============================================================================
class PersistenceBaselineModel:
    """
    Academic benchmark persistence model:
    Predicts tomorrow's hourly level using the day-ahead diurnal observation:
    y_hat_{t+h} = y_{t+h-24}
    """
    def __init__(self):
        self.name = "Persistence Baseline (Diurnal)"

    def predict(self, persist_df: pd.DataFrame) -> np.ndarray:
        return persist_df.to_numpy()

# ==============================================================================
# 3. TREE-BASED ENSEMBLE MODELS (NATIVE MULTI-OUTPUT)
# ==============================================================================
def create_random_forest_model(n_estimators: int = 80, max_depth: int = 12, random_state: int = 42):
    """Native multi-output Random Forest regressor."""
    return RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1
    )

def create_xgboost_model(n_estimators: int = 100, max_depth: int = 6, learning_rate: float = 0.08, random_state: int = 42):
    """Native multi-output XGBoost regressor using fast histogram tree method."""
    return XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.85,
        colsample_bytree=0.85,
        tree_method="hist",
        random_state=random_state,
        n_jobs=-1,
        verbosity=0
    )

# ==============================================================================
# 4. PYTORCH LSTM NEURAL NETWORK
# ==============================================================================
class PyTorchLSTM(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 1, output_dim: int = 24, dropout: float = 0.1):
        super(PyTorchLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)  # seq_len = 1
        lstm_out, _ = self.lstm(x)
        out = self.fc(lstm_out[:, -1, :])
        return out

class LSTMForecaster:
    """Wrapper to fit and predict with PyTorch LSTM following scikit-learn API."""
    def __init__(self, input_dim: int, hidden_dim: int = 64, output_dim: int = 24, lr: float = 0.005, epochs: int = 15, batch_size: int = 256):
        self.device = torch.device("cpu")
        self.model = PyTorchLSTM(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim).to(self.device)
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: Optional[np.ndarray] = None, y_val: Optional[np.ndarray] = None):
        X_t = torch.from_numpy(np.ascontiguousarray(X_train, dtype=np.float32))
        y_t = torch.from_numpy(np.ascontiguousarray(y_train, dtype=np.float32))
        dataset = TensorDataset(X_t, y_t)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-5)
        
        self.model.train()
        best_val_loss = float("inf")
        best_weights = None

        if X_val is not None and y_val is not None:
            X_v = torch.from_numpy(np.ascontiguousarray(X_val, dtype=np.float32)).to(self.device)
            y_v = torch.from_numpy(np.ascontiguousarray(y_val, dtype=np.float32)).to(self.device)

        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                optimizer.zero_grad()
                pred = self.model(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()

            if X_val is not None and y_val is not None:
                self.model.eval()
                with torch.no_grad():
                    val_pred = self.model(X_v)
                    v_loss = float(criterion(val_pred, y_v).item())
                    if v_loss < best_val_loss:
                        best_val_loss = v_loss
                        best_weights = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                self.model.train()

        if best_weights:
            self.model.load_state_dict({k: v.to(self.device) for k, v in best_weights.items()})

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            X_t = torch.from_numpy(np.ascontiguousarray(X, dtype=np.float32)).to(self.device)
            preds = self.model(X_t).cpu().numpy()
        return preds
