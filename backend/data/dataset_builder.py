"""
Historical Indian Air Quality Dataset Builder
Curates continuous hourly multivariate air quality and weather records for Bengaluru
from the XKDR Forum API, applies quality control and saves ready-for-modeling datasets.
"""

import sys
import json
import time
import pandas as pd
from pathlib import Path
from typing import List, Optional

from backend.config import (
    DEFAULT_STATION_ID,
    DEFAULT_CITY,
    CORE_POLLUTANTS,
    CORE_WEATHER,
    ALL_CORE_PARAMETERS,
    INDIA_DATA_DIR
)
from backend.data.xkdr_client import XKDRClient
from backend.data.pipeline import align_and_clean_station_timeseries, compute_data_quality_report

def build_bengaluru_dataset(
    station_id: str = DEFAULT_STATION_ID,
    years: Optional[List[str]] = None,
    output_filename: str = "bengaluru_hourly.csv"
) -> Path:
    """
    Pulls historical data for Bengaluru from XKDR, aligns timestamps,
    cleans missing values without look-ahead bias, and saves as CSV.
    """
    if years is None:
        years = ["2024", "2025", "2026"]

    client = XKDRClient()
    print(f"\n=======================================================")
    print(f"BUILDING BENGALURU HISTORICAL DATASET (Station: {station_id})")
    print(f"=======================================================")

    # 1. Fetch & cache station metadata
    print("[Step 1/4] Retrieving Bengaluru station network metadata...")
    stations = client.get_stations(city=DEFAULT_CITY)
    stations_path = INDIA_DATA_DIR / "bengaluru_stations.json"
    with open(stations_path, "w", encoding="utf-8") as f:
        json.dump(stations, f, indent=2)
    print(f"✓ Saved {len(stations)} Bengaluru stations to: {stations_path}")

    # 2. Retrieve measurements across core parameters
    print(f"\n[Step 2/4] Ingesting authentic measurements across {len(ALL_CORE_PARAMETERS)} parameters: {ALL_CORE_PARAMETERS}")
    all_records = []
    
    # Query parameter by parameter in yearly slices to avoid max_rows (10,000) truncation
    for param in ALL_CORE_PARAMETERS:
        param_records = 0
        for yr in years:
            start_date = f"{yr}-01-01"
            end_date = f"{yr}-12-31" if yr != "2026" else "2026-11-08"
            
            try:
                records = client.get_measurements(
                    station=station_id,
                    parameter=param,
                    start_date=start_date,
                    end_date=end_date,
                    agg="raw"
                )
                if records:
                    all_records.extend(records)
                    param_records += len(records)
            except Exception as e:
                print(f"  ⚠ Warning: Could not fetch {param} for {yr}: {e}")
                time.sleep(0.5)
        
        print(f"  • {param:<10}: {param_records:,} hourly readings ingested.")

    print(f"✓ Total raw measurement records collected: {len(all_records):,}")

    # 3. Clean and causally align time series
    print("\n[Step 3/4] Aligning to continuous hourly time grid & performing causal cleaning...")
    cleaned_df = align_and_clean_station_timeseries(
        records=all_records,
        station_id=station_id,
        expected_parameters=ALL_CORE_PARAMETERS,
        max_consecutive_impute_hours=6
    )

    if cleaned_df.empty:
        raise ValueError("Failed to construct cleaned dataset: no records were aligned.")

    # 4. Save and export quality report
    print(f"\n[Step 4/4] Exporting curated dataset and quality audit...")
    out_path = INDIA_DATA_DIR / output_filename
    cleaned_df.to_csv(out_path, index=False)
    print(f"✓ Curated dataset saved to: {out_path}")
    print(f"  • Total continuous hourly observations : {len(cleaned_df):,}")
    print(f"  • Date range                           : {cleaned_df['timestamp'].min()} to {cleaned_df['timestamp'].max()}")
    print(f"  • Features included                    : {list(cleaned_df.columns)}")

    # Audit report
    raw_df = pd.DataFrame(all_records)
    quality_report = compute_data_quality_report(raw_df, cleaned_df)
    report_path = INDIA_DATA_DIR / "dataset_quality_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)
    print(f"✓ Data quality audit saved to: {report_path}")

    # PM2.5 summary
    if "PM2.5" in cleaned_df.columns:
        p = cleaned_df["PM2.5"]
        print("\n--- PM2.5 STATISTICAL PROFILE (Bengaluru - BTM Layout) ---")
        print(f"  Mean: {p.mean():.2f} µg/m³ | Std: {p.std():.2f} µg/m³")
        print(f"  Min : {p.min():.2f} µg/m³ | Median: {p.median():.2f} µg/m³ | Max: {p.max():.2f} µg/m³")
        print(f"  25th percentile: {p.quantile(0.25):.2f} | 75th percentile: {p.quantile(0.75):.2f} | 95th percentile: {p.quantile(0.95):.2f}")

    return out_path

if __name__ == "__main__":
    build_bengaluru_dataset()
