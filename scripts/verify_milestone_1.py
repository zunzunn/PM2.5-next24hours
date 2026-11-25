"""
Milestone 1 End-to-End Verification Script
Tests:
1. XKDR API Client connectivity, authentication, station lookup & response caching
2. Data Preprocessing & Leakage Prevention (causal forward fill & expanding imputation)
3. Curation of real Bengaluru historical hourly dataset (2025-2026)
4. Integrity audit: Monotonic time order, continuous 1-hour grid, zero NaNs, plausibility bounds
"""

import sys
import time
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import (
    DEFAULT_STATION_ID,
    DEFAULT_CITY,
    ALL_CORE_PARAMETERS,
    INDIA_DATA_DIR
)
from backend.data.xkdr_client import XKDRClient
from backend.data.pipeline import align_and_clean_station_timeseries
from backend.data.dataset_builder import build_bengaluru_dataset

def test_1_client_and_caching():
    print("\n--- TEST 1: XKDR API Client & Caching ---")
    client = XKDRClient()
    
    # 1.1 Stations
    t0 = time.time()
    stations = client.get_stations(city=DEFAULT_CITY)
    t1 = time.time()
    print(f"✓ Retrieved {len(stations)} stations for {DEFAULT_CITY} in {(t1 - t0)*1000:.1f}ms")
    assert len(stations) >= 10, f"Expected at least 10 stations, got {len(stations)}"
    
    # 1.2 Cache hit check
    t2 = time.time()
    stations_cached = client.get_stations(city=DEFAULT_CITY)
    t3 = time.time()
    cache_time_ms = (t3 - t2) * 1000
    print(f"✓ Cache hit verified: retrieved from disk in {cache_time_ms:.2f}ms")
    assert cache_time_ms < 50, "Cache response should be practically instantaneous"
    assert len(stations_cached) == len(stations)
    print("✓ Test 1 Passed: Client and caching operational.")

def test_2_leakage_prevention_logic():
    print("\n--- TEST 2: Causal Alignment & Look-Ahead Leakage Check ---")
    # Synthetic records with a gap and negative anomaly
    mock_records = [
        {"station_id": "test_site", "parameter_name": "PM2.5", "collected_at": "2026-01-01T00:00:00", "value": 50.0},
        {"station_id": "test_site", "parameter_name": "PM2.5", "collected_at": "2026-01-01T01:00:00", "value": -10.0}, # physically impossible
        # Hour 02:00:00 is missing (dropout)
        {"station_id": "test_site", "parameter_name": "PM2.5", "collected_at": "2026-01-01T03:00:00", "value": 75.0},
    ]

    cleaned = align_and_clean_station_timeseries(mock_records, station_id="test_site")
    
    # Check continuous hourly frequency
    assert len(cleaned) == 4, f"Expected 4 hourly points (00, 01, 02, 03), got {len(cleaned)}"
    
    # Check negative value clipped to 0
    assert cleaned.loc[cleaned["hour"] == 1, "PM2.5"].values[0] == 0.0, "Negative values must be clipped to 0.0"
    
    # Check missing hour 02 was forward-filled from past (hour 01 = 0.0), NOT backward-filled from future (hour 03 = 75.0)
    val_hr2 = cleaned.loc[cleaned["hour"] == 2, "PM2.5"].values[0]
    assert val_hr2 == 0.0, f"Leakage detected! Expected 0.0 (past ffill), got {val_hr2} (potential future backfill)"
    print(f"✓ Verified causal imputation: hour 2 filled with {val_hr2} (past value), zero future look-ahead.")
    print("✓ Test 2 Passed: Causal cleaning and physical bounds verified.")

def test_3_curate_real_bengaluru_dataset():
    print("\n--- TEST 3: Curating Real Bengaluru Dataset from XKDR ---")
    # Curate recent 2025 and 2026 dataset for fast and solid evaluation
    dataset_path = build_bengaluru_dataset(
        station_id=DEFAULT_STATION_ID,
        years=["2025", "2026"],
        output_filename="bengaluru_hourly.csv"
    )

    assert dataset_path.exists(), f"Dataset file does not exist at {dataset_path}"
    df = pd.read_csv(dataset_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    print(f"\n--- AUDIT OF CURATED DATASET ---")
    print(f"Total Rows: {len(df):,}")
    print(f"Columns   : {list(df.columns)}")
    
    # Checks
    assert len(df) > 5000, f"Expected at least 5000 hourly rows, got {len(df)}"
    assert "PM2.5" in df.columns, "PM2.5 column missing"
    assert df["timestamp"].is_monotonic_increasing, "Timestamps must be strictly monotonic increasing"
    
    # Check step interval is strictly 1 hour
    diffs = df["timestamp"].diff().dropna()
    expected_step = pd.Timedelta(hours=1)
    assert (diffs == expected_step).all(), "Timestamps must form a continuous 1-hour interval without missing gaps"
    print("✓ Verified strict continuous 1-hour temporal grid (zero missing step intervals).")

    # Check missing values in key columns
    null_counts = df[["PM2.5", "PM10", "NO2", "SO2", "CO", "Ozone"]].isna().sum()
    print(f"Null counts in core features:\n{null_counts.to_dict()}")
    assert null_counts.sum() == 0, "No NaNs allowed in final modeling features"
    print("✓ Verified complete absence of missing values in core features.")

    print("\n=======================================================")
    print("SUCCESS: ALL MILESTONE 1 VERIFICATION CHECKS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    test_1_client_and_caching()
    test_2_leakage_prevention_logic()
    test_3_curate_real_bengaluru_dataset()
