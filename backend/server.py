"""
Lightweight REST API & Web Application Server
Powered by Python's standard library http.server (100% portable, zero deprecation issues).

Endpoints:
- /api/health
- /api/stations
- /api/forecast?station_id=...&model=...
- /api/advisory
- Static files for the web app (index.html, dashboard.html, css/*, js/*, data/*)
"""

import os
import sys
import json
import urllib.parse
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
DATA_DIR = WEB_DIR / "data"

class AirQualityAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # REST API Routes
        if path == "/api/health":
            self._send_json({
                "status": "healthy",
                "service": "PM2.5 Next-Day Forecast Engine",
                "version": "1.0.0"
            })
            return

        if path == "/api/stations":
            stations_file = DATA_DIR / "stations.json"
            if stations_file.exists():
                with open(stations_file, "r", encoding="utf-8") as f:
                    self._send_json(json.load(f))
            else:
                self._send_error(404, "Stations file not found")
            return

        if path == "/api/stations/all":
            all_geo_file = DATA_DIR / "all_stations_geo.json"
            if all_geo_file.exists():
                with open(all_geo_file, "r", encoding="utf-8") as f:
                    self._send_json(json.load(f))
            else:
                self._send_error(404, "All stations geo file not found")
            return

        if path == "/api/states":
            states_file = DATA_DIR / "states_summary.json"
            if states_file.exists():
                with open(states_file, "r", encoding="utf-8") as f:
                    self._send_json(json.load(f))
            else:
                self._send_error(404, "States summary file not found")
            return

        if path == "/api/forecast":
            forecasts_file = DATA_DIR / "forecasts.json"
            station_id = query.get("station_id", ["site_162"])[0]
            model = query.get("model", ["lstm"])[0]

            if forecasts_file.exists():
                with open(forecasts_file, "r", encoding="utf-8") as f:
                    all_forecasts = json.load(f)
                
                target = all_forecasts.get(station_id, all_forecasts.get("site_162", {}))
                self._send_json({
                    "station_id": station_id,
                    "selected_model": model,
                    "data": target
                })
            else:
                self._send_error(404, "Forecasts file not found")
            return

        # Default static file serving (redirect root to index.html if needed)
        if path == "/":
            self.path = "/index.html"
            
        return super().do_GET()

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def run_server(port: int = 8000, host: str = "0.0.0.0"):
    ThreadingHTTPServer.allow_reuse_address = True
    server_address = (host, port)
    try:
        httpd = ThreadingHTTPServer(server_address, AirQualityAppHandler)
    except OSError as e:
        if e.errno == 48:
            print(f"\n⚠️  Port {port} is already in use.")
            print(f"• To free port {port}, run: lsof -ti :{port} | xargs kill -9")
            print(f"• Or start on another port: python3 backend/server.py 8080\n")
            sys.exit(1)
        raise e

    print(f"===========================================================")
    print(f"PM2.5 FORECAST WEATHER-THEMED WEB SERVER RUNNING")
    print(f"• URL: http://localhost:{port}/")
    print(f"• Dashboard: http://localhost:{port}/dashboard.html")
    print(f"• API Stations: http://localhost:{port}/api/stations")
    print(f"• API Forecast: http://localhost:{port}/api/forecast?station_id=site_162")
    print(f"===========================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port=port)
