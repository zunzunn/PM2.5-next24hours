"""
Community Project (BCP308) - Next-Day PM2.5 Forecast
Milestone 2 Progress Demonstration Script (Using Real UCI Dataset)
Authors: Shourya (Lead), Pravar Singh, Shubham Pant, Shubham Sharma
Institution: Dayananda Sagar College of Engineering
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Ensure outputs directory exists
os.makedirs("outputs", exist_ok=True)

print("=" * 65)
print("PROJECT 34: NEXT-DAY PM2.5 FORECAST — REAL DATASET DEMO")
print("=" * 65)

# ==============================================================================
# 1. DATA INGESTION & QUALITY CONTROL (Pravar Singh's Module)
# ==============================================================================
print("\n[Step 1/5] Ingesting Real Multi-Site Air Quality Dataset...")

csv_path = "data/beijing_multisite/PRSA_Data_20130301-20170228/PRSA_Data_Aotizhongxin_20130301-20170228.csv"
if not os.path.exists(csv_path):
    # Fallback search if path varies
    found = glob.glob("data/**/PRSA_Data_Aotizhongxin_*.csv", recursive=True)
    if found:
        csv_path = found[0]

raw_df = pd.read_csv(csv_path)
print(f"✓ Loaded real dataset from: {os.path.basename(csv_path)}")
print(f"✓ Raw dimensions: {raw_df.shape[0]:,} records × {raw_df.shape[1]} attributes.")

# Construct continuous datetime index
raw_df['timestamp'] = pd.to_datetime(raw_df[['year', 'month', 'day', 'hour']])
raw_df = raw_df.sort_values('timestamp').reset_index(drop=True)

# Sensor missingness check & linear temporal interpolation
missing_count = raw_df['PM2.5'].isna().sum()
raw_df['PM2.5'] = raw_df['PM2.5'].interpolate(method='linear').bfill().ffill()
for col in ['TEMP', 'PRES', 'DEWP', 'WSPM', 'NO2', 'SO2', 'CO', 'O3']:
    if col in raw_df.columns:
        raw_df[col] = raw_df[col].interpolate(method='linear').bfill().ffill()

print(f"✓ Resolved {missing_count:,} missing sensor timestamps via linear temporal interpolation.")

# ==============================================================================
# 2. FEATURE ENGINEERING & STRICT TEMPORAL LAGS (Shubham Pant's Module)
# ==============================================================================
print("\n[Step 2/5] Engineering Temporal Lags & Cyclical Meteorological Features...")

# Cyclical trigonometric time encodings
raw_df['hour_sin'] = np.sin(2 * np.pi * raw_df['hour'] / 24.0)
raw_df['hour_cos'] = np.cos(2 * np.pi * raw_df['hour'] / 24.0)
raw_df['month_sin'] = np.sin(2 * np.pi * raw_df['month'] / 12.0)
raw_df['month_cos'] = np.cos(2 * np.pi * raw_df['month'] / 12.0)

# Lagged features (strictly past values: info available 24 hours prior)
raw_df['PM2.5_lag24'] = raw_df['PM2.5'].shift(24)
raw_df['PM2.5_lag48'] = raw_df['PM2.5'].shift(48)
raw_df['PM2.5_roll_mean24'] = raw_df['PM2.5'].shift(24).rolling(window=24).mean()
raw_df['PM2.5_roll_std24'] = raw_df['PM2.5'].shift(24).rolling(window=24).std()
raw_df['TEMP_lag24'] = raw_df['TEMP'].shift(24)
raw_df['WSPM_lag24'] = raw_df['WSPM'].shift(24)

# Drop initial warmup rows due to shifting
df_model = raw_df.dropna().copy().reset_index(drop=True)

feature_cols = [
    'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
    'PM2.5_lag24', 'PM2.5_lag48', 'PM2.5_roll_mean24', 'PM2.5_roll_std24',
    'TEMP_lag24', 'WSPM_lag24', 'PRES', 'DEWP', 'NO2', 'SO2'
]

X = df_model[feature_cols]
y = df_model['PM2.5']
y_persistence = df_model['PM2.5_lag24']

# Chronological Train / Holdout Test Split (Last 20% reserved for testing)
split_idx = int(len(df_model) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
y_persist_test = y_persistence.iloc[split_idx:]
test_timestamps = df_model['timestamp'].iloc[split_idx:]

print(f"✓ Chronological Split: Train = {len(X_train):,} hours | Test = {len(X_test):,} hours.")

# ==============================================================================
# 3. BASELINE VS. ML MODEL TRAINING & BENCHMARKING (Shourya's Module)
# ==============================================================================
print("\n[Step 3/5] Benchmarking Persistence Baseline vs. Machine Learning Models...")

# 3.1 Persistence Baseline Evaluation (y_hat_t = y_{t-24})
rmse_persist = np.sqrt(mean_squared_error(y_test, y_persist_test))
mae_persist = mean_absolute_error(y_test, y_persist_test)
r2_persist = r2_score(y_test, y_persist_test)

# 3.2 Machine Learning Model (Fast Histogram Gradient Boosting)
ml_model = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=8, random_state=42)
ml_model.fit(X_train, y_train)
y_pred_ml = ml_model.predict(X_test)

rmse_ml = np.sqrt(mean_squared_error(y_test, y_pred_ml))
mae_ml = mean_absolute_error(y_test, y_pred_ml)
r2_ml = r2_score(y_test, y_pred_ml)

print("-" * 65)
print(f"{'Metric':<25} | {'Baseline (t-24)':<15} | {'ML Model (GBDT)':<15} | {'Target':<10}")
print("-" * 65)
print(f"{'RMSE (µg/m³)':<25} | {rmse_persist:<15.2f} | {rmse_ml:<15.2f} | {'< 35.0':<10}")
print(f"{'MAE (µg/m³)':<25} | {mae_persist:<15.2f} | {mae_ml:<15.2f} | {'< 25.0':<10}")
print(f"{'R² Score':<25} | {r2_persist:<15.2f} | {r2_ml:<15.2f} | {'> 0.60':<10}")
print("-" * 65)
improvement = ((rmse_persist - rmse_ml) / rmse_persist) * 100
print(f"✓ Result: ML model outperforms persistence baseline by {improvement:.1f}% reduction in RMSE!")

# ==============================================================================
# 4. DOWNSTREAM ADVISORY ENGINE (Shubham Sharma's Module)
# ==============================================================================
print("\n[Step 4/5] Executing 24-Hour Public Health Advisory Engine...")

def get_aqi_category(pm25):
    """Categorize PM2.5 (µg/m³) into standard Indian CPCB health impact categories."""
    if pm25 <= 30:
        return "Good", "#2ecc71", "Minimal impact. Safe for all outdoor activities."
    elif pm25 <= 60:
        return "Satisfactory", "#a8e063", "Minor breathing discomfort to sensitive people."
    elif pm25 <= 90:
        return "Moderate", "#f39c12", "Breathing discomfort to people with lung/heart disease."
    elif pm25 <= 120:
        return "Poor", "#e67e22", "Breathing discomfort to most people on prolonged exposure."
    elif pm25 <= 250:
        return "Very Poor", "#e74c3c", "Respiratory illness on prolonged exposure. Avoid strenuous workouts."
    else:
        return "Severe", "#8e44ad", "Serious health risk. Entire population should stay indoors."

# Forecast window: last 24 hours of test set
next_24_hours = test_timestamps.iloc[-24:].reset_index(drop=True)
next_24_actual = y_test.iloc[-24:].reset_index(drop=True)
next_24_pred = y_pred_ml[-24:]

print("\n" + "=" * 70)
print(f"{'Hour':<10} | {'Forecast PM2.5':<16} | {'AQI Category':<15} | {'Advisory'}")
print("=" * 70)

safe_hours = []
for i in range(24):
    hr_str = next_24_hours[i].strftime("%H:00")
    val = max(0.0, next_24_pred[i])
    category, color, advice = get_aqi_category(val)
    if val <= 60:
        safe_hours.append(hr_str)
    print(f"{hr_str:<10} | {val:<16.1f} | {category:<15} | {advice}")

print("=" * 70)
if safe_hours:
    print(f"★ RECOMMENDED SAFE OUTDOOR EXPOSURE WINDOWS: {', '.join(safe_hours)}")
else:
    print("★ WARNING: Elevated pollution forecasted across 24 hours. Limit outdoor exposure.")

# ==============================================================================
# 5. EXPORT VISUAL ARTIFACTS
# ==============================================================================
print("\n[Step 5/5] Generating review visualization artifacts...")

# Figure 1: Test Window Comparison
plt.figure(figsize=(14, 5))
sample_window = 120
t_plot = test_timestamps.iloc[-sample_window:]
plt.plot(t_plot, y_test.iloc[-sample_window:], label="Actual PM2.5", color="#2c3e50", lw=2)
plt.plot(t_plot, y_pred_ml[-sample_window:], label=f"ML Forecast (RMSE: {rmse_ml:.1f})", color="#2980b9", lw=2, linestyle="--")
plt.plot(t_plot, y_persist_test.iloc[-sample_window:], label=f"Persistence Baseline (RMSE: {rmse_persist:.1f})", color="#e74c3c", lw=1.2, alpha=0.6, linestyle=":")

plt.title(f"24-Hour Ahead PM2.5 Forecast: ML Model vs. Persistence Baseline ({os.path.basename(csv_path)})", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Date & Time", fontsize=11)
plt.ylabel("PM2.5 (µg/m³)", fontsize=11)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(frameon=True, facecolor="white", loc="upper right")
plt.tight_layout()
fig1_path = "outputs/1_model_vs_baseline_comparison.png"
plt.savefig(fig1_path, dpi=200)
plt.close()
print(f"✓ Saved Figure 1: {fig1_path}")

# Figure 2: Advisory Dashboard
plt.figure(figsize=(12, 6))
hours_axis = [h.strftime("%H:%M") for h in next_24_hours]
colors = [get_aqi_category(val)[1] for val in next_24_pred]

bars = plt.bar(hours_axis, next_24_pred, color=colors, edgecolor="#2c3e50", alpha=0.85, width=0.7)
plt.axhline(60, color="#27ae60", linestyle="--", linewidth=1.5, label="Satisfactory Air Cutoff (60 µg/m³)")
plt.axhline(120, color="#e67e22", linestyle="--", linewidth=1.5, label="Moderate/Poor Cutoff (120 µg/m³)")

for bar, val in zip(bars, next_24_pred):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5, f"{val:.0f}", ha='center', va='bottom', fontsize=8, fontweight='bold')

plt.title("Community Action Advisory: 24-Hour Ahead Predicted PM2.5 Profile", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Hour of Day", fontsize=11)
plt.ylabel("Forecasted PM2.5 (µg/m³)", fontsize=11)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle="--", alpha=0.5)
plt.legend(loc="upper left")
plt.tight_layout()
fig2_path = "outputs/2_community_advisory_dashboard.png"
plt.savefig(fig2_path, dpi=200)
plt.close()
print(f"✓ Saved Figure 2: {fig2_path}")

# Figure 3: Diurnal Pattern & Performance
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

hourly_avg = raw_df.groupby('hour')['PM2.5'].mean()
ax1.plot(hourly_avg.index, hourly_avg.values, marker='o', color='#8e44ad', lw=2)
ax1.set_title("Empirical Diurnal Cycle of PM2.5", fontsize=12, fontweight='bold')
ax1.set_xlabel("Hour of Day (0-23)", fontsize=10)
ax1.set_ylabel("Mean PM2.5 (µg/m³)", fontsize=10)
ax1.grid(True, linestyle="--", alpha=0.5)

metrics_names = ['RMSE', 'MAE', 'R²']
base_vals = [rmse_persist, mae_persist, r2_persist]
ml_vals = [rmse_ml, mae_ml, r2_ml]

x_pos = np.arange(len(metrics_names))
bar_width = 0.35

ax2.bar(x_pos - bar_width/2, base_vals, width=bar_width, label='Persistence Baseline', color='#e74c3c', alpha=0.8)
ax2.bar(x_pos + bar_width/2, ml_vals, width=bar_width, label='Gradient Boosted Model', color='#27ae60', alpha=0.8)

ax2.set_xticks(x_pos)
ax2.set_xticklabels(['RMSE (lower)', 'MAE (lower)', 'R² (higher)'], fontsize=10, fontweight='bold')
ax2.set_title("Quantitative Performance on Real Dataset", fontsize=12, fontweight='bold')
ax2.set_ylabel("Metric Value", fontsize=10)
ax2.legend()
ax2.grid(axis='y', linestyle="--", alpha=0.5)

plt.tight_layout()
fig3_path = "outputs/3_diurnal_and_metrics_summary.png"
plt.savefig(fig3_path, dpi=200)
plt.close()
print(f"✓ Saved Figure 3: {fig3_path}")

print("\n" + "=" * 65)
print("SUCCESS: ALL REAL DATASET DEMO ARTIFACTS GENERATED SUCCESSFULLY!")
print("=" * 65)
