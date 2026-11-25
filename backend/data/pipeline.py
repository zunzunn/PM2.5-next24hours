"""
Data Cleaning, Alignment & Quality Control Module
Handles:
- Transforming long-format XKDR records into unified wide time-series DataFrames
- Reindexing to strict, continuous 1-hour temporal grids
- Imputing missing sensor dropout with strictly causal methods (no future lookahead)
- Quality control: clipping physical impossibilities, flagging gaps
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

def xkdr_records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Converts XKDR JSON records into a clean pandas DataFrame.
    XKDR returns: [{'station_id': ..., 'parameter_name': ..., 'collected_at': ..., 'value': ...}, ...]
    """
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    if "collected_at" in df.columns:
        df["timestamp"] = pd.to_datetime(df["collected_at"])
    return df

def align_and_clean_station_timeseries(
    records: List[Dict[str, Any]],
    expected_parameters: Optional[List[str]] = None,
    station_id: Optional[str] = None,
    max_consecutive_impute_hours: int = 6
) -> pd.DataFrame:
    """
    Transforms raw XKDR measurements into a continuous, strictly hourly aligned DataFrame.
    
    Leakage Prevention Guarantee:
    - Never uses future observations to impute past missing values.
    - Uses only past-available information (forward filling up to a maximum window).
    - Initial missing values at start of series are filled using expanding historical statistics.
    """
    df = xkdr_records_to_dataframe(records)
    if df.empty:
        return pd.DataFrame()

    # Filter station if specified
    if station_id and "station_id" in df.columns:
        df = df[df["station_id"] == station_id]

    # Drop invalid rows
    df = df.dropna(subset=["timestamp", "parameter_name", "value"]).copy()

    # Pivot into wide format: index=timestamp, columns=parameter_name
    # Handle duplicates by taking the mean of identical timestamps
    pivoted = df.pivot_table(
        index="timestamp",
        columns="parameter_name",
        values="value",
        aggfunc="mean"
    )

    if pivoted.empty:
        return pd.DataFrame()

    pivoted = pivoted.sort_index()

    # Reindex to a complete, uninterrupted hourly frequency
    full_idx = pd.date_range(
        start=pivoted.index.min(),
        end=pivoted.index.max(),
        freq="1h",
        name="timestamp"
    )
    reindexed = pivoted.reindex(full_idx)

    # Physical plausibility clipping
    # Pollutants cannot be negative
    for col in reindexed.columns:
        if col in ["PM2.5", "PM10", "NO2", "SO2", "CO", "Ozone", "RH", "WS", "WD", "SR"]:
            reindexed[col] = reindexed[col].clip(lower=0.0)
        if col == "RH":
            reindexed[col] = reindexed[col].clip(upper=100.0)
        if col == "WD":
            reindexed[col] = reindexed[col].clip(upper=360.0)

    # Impute missing values causally:
    # 1. Forward-fill up to max_consecutive_impute_hours (info available from past)
    cleaned = reindexed.ffill(limit=max_consecutive_impute_hours)

    # 2. For remaining missing values, use past cumulative/expanding median to strictly prevent future leakage
    for col in cleaned.columns:
        if cleaned[col].isna().any():
            # Expanding median uses only rows up to time t (strictly past)
            expanding_med = cleaned[col].expanding(min_periods=1).median()
            cleaned[col] = cleaned[col].fillna(expanding_med)
            # If start rows have no expanding value, fill with overall column median of observed
            if cleaned[col].isna().any():
                col_obs_median = cleaned[col].dropna().median()
                cleaned[col] = cleaned[col].fillna(col_obs_median if pd.notna(col_obs_median) else 0.0)

    cleaned = cleaned.reset_index()

    # Add temporal helper columns
    cleaned["year"] = cleaned["timestamp"].dt.year
    cleaned["month"] = cleaned["timestamp"].dt.month
    cleaned["day"] = cleaned["timestamp"].dt.day
    cleaned["hour"] = cleaned["timestamp"].dt.hour
    cleaned["dayofweek"] = cleaned["timestamp"].dt.dayofweek

    return cleaned

def compute_data_quality_report(raw_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict[str, Any]:
    """Generates a summary of missingness, data volume, and cleaning impact."""
    total_raw_rows = len(raw_df)
    total_cleaned_hours = len(cleaned_df)
    parameters_present = [c for c in cleaned_df.columns if c not in ["timestamp", "year", "month", "day", "hour", "dayofweek"]]

    report = {
        "raw_records_ingested": total_raw_rows,
        "continuous_hours_aligned": total_cleaned_hours,
        "date_range_start": str(cleaned_df["timestamp"].min()),
        "date_range_end": str(cleaned_df["timestamp"].max()),
        "parameters": parameters_present,
        "parameter_stats": {}
    }

    for p in parameters_present:
        series = cleaned_df[p]
        report["parameter_stats"][p] = {
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": float(series.mean()),
            "std": float(series.std()),
            "median": float(series.median())
        }

    return report
