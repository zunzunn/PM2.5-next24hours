"""
Application Configuration
Loads configuration from environment variables (.env) securely.
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
INDIA_DATA_DIR = DATA_DIR / "india_xkdr"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
INDIA_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load .env file
def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

load_env()

# XKDR API Settings
# Never hardcode secrets. Reads from XKDR_API_KEY env var with fallback.
XKDR_API_KEY = os.getenv("XKDR_API_KEY", "aqi_LU-BSIcMRnXwkOjrMx21VdSufAmBAN9qDqFz9KNQ4pI")
XKDR_API_BASE = os.getenv("XKDR_API_BASE", "https://airquality.xkdr.org/v1")

# Default Target City and Station
DEFAULT_CITY = "Bengaluru"
DEFAULT_STATION_ID = "site_162"  # BTM Layout, Bengaluru - CPCB

# Core parameters to track
CORE_POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "CO", "Ozone"]
CORE_WEATHER = ["AT", "RH", "WS", "WD"]
ALL_CORE_PARAMETERS = CORE_POLLUTANTS + CORE_WEATHER

# CPCB Air Quality Index Breakpoints for PM2.5 (µg/m³, 24-hr standard)
CPCB_AQI_BREAKPOINTS = [
    {"category": "Good", "min": 0.0, "max": 30.0, "aqi_min": 0, "aqi_max": 50, "color": "#22c55e", "advice": "Minimal health impact. Ideal for all outdoor activities."},
    {"category": "Satisfactory", "min": 30.1, "max": 60.0, "aqi_min": 51, "aqi_max": 100, "color": "#84cc16", "advice": "Minor breathing discomfort to sensitive individuals."},
    {"category": "Moderate", "min": 60.1, "max": 90.0, "aqi_min": 101, "aqi_max": 200, "color": "#eab308", "advice": "Breathing discomfort to people with lung disease, asthma, and heart conditions."},
    {"category": "Poor", "min": 90.1, "max": 120.0, "aqi_min": 201, "aqi_max": 300, "color": "#f97316", "advice": "Breathing discomfort to most people on prolonged exposure. Sensitive groups should stay indoors."},
    {"category": "Very Poor", "min": 120.1, "max": 250.0, "aqi_min": 301, "aqi_max": 400, "color": "#ef4444", "advice": "Respiratory illness on prolonged exposure. Avoid morning/evening outdoor workouts."},
    {"category": "Severe", "min": 250.1, "max": 1000.0, "aqi_min": 401, "aqi_max": 500, "color": "#a855f7", "advice": "Serious health impacts on healthy people and severe impacts on vulnerable groups. Stay strictly indoors."}
]
