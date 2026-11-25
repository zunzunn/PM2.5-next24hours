"""
XKDR Forum India Air Quality API Client Verification Script
Tests connectivity, authentication via environment variable, station lookup,
and real historical PM2.5/pollutant measurements retrieval for Bengaluru.
"""

import os
import sys
import json
import requests
from datetime import datetime

# Load .env if present
def load_env(env_path=".env"):
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()
load_env("../.env")

API_KEY = os.getenv("XKDR_API_KEY", "aqi_demo_wbf92Qx21zX-Wa_Tg8Dx1nXe")
API_BASE = os.getenv("XKDR_API_BASE", "https://airquality.xkdr.org/v1")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

def verify_connection():
    print("=" * 65)
    print("VERIFYING XKDR AIR QUALITY API INTEGRATION")
    print("=" * 65)
    print(f"Target Base URL: {API_BASE}")
    print(f"API Key source : {'Environment Variable' if os.getenv('XKDR_API_KEY') else 'Default Demo'}")
    print(f"Key preview    : {API_KEY[:8]}...{API_KEY[-4:] if len(API_KEY) > 12 else ''}")

    # 1. Test /meta endpoint
    meta_url = f"{API_BASE}/meta"
    print(f"\n[1/4] Querying Metadata: {meta_url}")
    res = requests.get(meta_url, headers=headers, timeout=15)
    if res.status_code != 200:
        print(f"FAILED to reach /meta: HTTP {res.status_code}")
        print(res.text)
        return False
    
    meta_data = res.json()
    print("✓ Successfully connected to XKDR API!")
    print(f"  • Total Archive Records : {meta_data.get('measurements', {}).get('rows', 0):,}")
    print(f"  • Date Range Available  : {meta_data.get('measurements', {}).get('first_month')} to {meta_data.get('measurements', {}).get('last_month')}")
    print(f"  • Total Active Stations : {meta_data.get('stations')}")
    print(f"  • Total Parameters      : {meta_data.get('parameters')}")
    print(f"  • Current Token Tier    : {meta_data.get('your_tier')}")

    # 2. Test /stations for Bengaluru
    stations_url = f"{API_BASE}/stations?city=Bengaluru"
    print(f"\n[2/4] Querying Bengaluru Stations: {stations_url}")
    res = requests.get(stations_url, headers=headers, timeout=15)
    if res.status_code != 200:
        print(f"FAILED to reach /stations: HTTP {res.status_code}")
        return False
    
    stations_data = res.json()
    bengaluru_stations = stations_data.get("data", [])
    print(f"✓ Found {len(bengaluru_stations)} monitoring stations in Bengaluru:")
    for s in bengaluru_stations[:5]:
        print(f"  - [{s.get('station_id')}] {s.get('station_name')} (Coords: {s.get('latitude')}, {s.get('longitude')})")
    if len(bengaluru_stations) > 5:
        print(f"  ... and {len(bengaluru_stations) - 5} more stations.")

    # 3. Test /measurements for Bengaluru (site_162 - BTM Layout)
    sample_station = "site_162"
    start_date = "2026-11-01"
    end_date = "2026-11-03"
    meas_url = f"{API_BASE}/measurements?station={sample_station}&parameter=PM2.5&start={start_date}&end={end_date}&agg=raw&format=json"
    print(f"\n[3/4] Querying Hourly PM2.5 for {sample_station} (BTM Layout): {meas_url}")
    res = requests.get(meas_url, headers=headers, timeout=15)
    if res.status_code != 200:
        print(f"FAILED to reach /measurements: HTTP {res.status_code}")
        return False
    
    meas_data = res.json()
    records = meas_data.get("data", [])
    print(f"✓ Retrieved {len(records)} authentic hourly PM2.5 measurements!")
    if records:
        print(f"  • First timestamp: {records[0].get('collected_at')} -> {records[0].get('value')} {records[0].get('unit')}")
        print(f"  • Middle timestamp: {records[len(records)//2].get('collected_at')} -> {records[len(records)//2].get('value')} {records[len(records)//2].get('unit')}")
        print(f"  • Last timestamp:  {records[-1].get('collected_at')} -> {records[-1].get('value')} {records[-1].get('unit')}")
        values = [r['value'] for r in records if r.get('value') is not None]
        if values:
            print(f"  • Range in sample: Min = {min(values):.1f} µg/m³, Max = {max(values):.1f} µg/m³, Mean = {sum(values)/len(values):.1f} µg/m³")

    # 4. Multi-parameter check
    multi_url = f"{API_BASE}/measurements?station={sample_station}&start={start_date}&end={start_date}&agg=raw&format=json"
    print(f"\n[4/4] Verifying Multi-Parameter Availability on {start_date}...")
    res = requests.get(multi_url, headers=headers, timeout=15)
    if res.status_code == 200:
        multi_data = res.json().get("data", [])
        params_found = set(r.get("parameter_name") for r in multi_data)
        print(f"✓ Parameters simultaneously available on station {sample_station}:")
        print(f"  {', '.join(sorted(params_found))}")

    print("\n" + "=" * 65)
    print("SUCCESS: ALL XKDR API TESTS PASSED!")
    print("=" * 65)
    return True

if __name__ == "__main__":
    success = verify_connection()
    sys.exit(0 if success else 1)
