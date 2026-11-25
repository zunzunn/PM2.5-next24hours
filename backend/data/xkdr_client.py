"""
XKDR Forum India Air Quality API Client
Features:
- Secure token authentication via environment variables
- Resilient retry mechanism with exponential backoff
- Disk-based caching to avoid redundant API queries and respect rate limits
- Support for stations, metadata, parameters, and time-series measurements
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from backend.config import XKDR_API_KEY, XKDR_API_BASE, CACHE_DIR

class XKDRClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, cache_enabled: bool = True):
        self.api_key = api_key or XKDR_API_KEY
        self.base_url = (base_url or XKDR_API_BASE).rstrip("/")
        self.cache_enabled = cache_enabled
        self.cache_dir = CACHE_DIR / "api_responses"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        })

    def _get_cache_path(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Path:
        cache_key_str = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        hashed_key = hashlib.md5(cache_key_str.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3, ttl_seconds: int = 3600) -> Dict[str, Any]:
        """Performs HTTP GET with caching and exponential backoff retry."""
        cache_path = self._get_cache_path(endpoint, params)
        if self.cache_enabled and cache_path.exists():
            file_age = time.time() - cache_path.stat().st_mtime
            if file_age < ttl_seconds:
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        delay = 1.0
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=25)
                if response.status_code == 200:
                    data = response.json()
                    if self.cache_enabled:
                        try:
                            with open(cache_path, "w", encoding="utf-8") as f:
                                json.dump(data, f)
                        except Exception:
                            pass
                    return data
                elif response.status_code == 429:
                    time.sleep(delay)
                    delay *= 2
                    continue
                else:
                    response.raise_for_status()
            except requests.RequestException as e:
                last_error = e
                time.sleep(delay)
                delay *= 2

        raise RuntimeError(f"XKDR API request failed after {max_retries} attempts: {last_error}")

    def get_meta(self) -> Dict[str, Any]:
        """Fetches API database metadata and schema specifications."""
        return self._request("meta", ttl_seconds=86400)

    def get_parameters(self) -> List[Dict[str, Any]]:
        """Lists available pollutant and weather parameters."""
        res = self._request("parameters", ttl_seconds=86400)
        return res.get("data", [])

    def get_stations(self, city: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists monitoring stations, optionally filtered by city or state."""
        params = {}
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        res = self._request("stations", params=params, ttl_seconds=86400)
        return res.get("data", [])

    def get_station_by_id(self, station_id: str) -> Optional[Dict[str, Any]]:
        """Finds details for a specific station identifier."""
        stations = self.get_stations()
        for s in stations:
            if s.get("station_id") == station_id:
                return s
        return None

    def get_measurements(
        self,
        station: Optional[str] = None,
        city: Optional[str] = None,
        parameter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        agg: str = "raw",
        ttl_seconds: int = 1800
    ) -> List[Dict[str, Any]]:
        """
        Retrieves time-series measurement rows from XKDR.
        Dates format: YYYY-MM-DD
        Agg: 'raw' (hourly), 'daily', or 'monthly'
        """
        params = {
            "agg": agg,
            "format": "json"
        }
        if station:
            params["station"] = station
        if city:
            params["city"] = city
        if parameter:
            params["parameter"] = parameter
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        res = self._request("measurements", params=params, ttl_seconds=ttl_seconds)
        return res.get("data", [])
