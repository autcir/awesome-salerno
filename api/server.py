#!/usr/bin/env python3
"""
Simple JSON API server for awesome-salerno data.

Usage:
    python3 api/server.py

Endpoints:
    GET /api/sentieri
    GET /api/monumenti
    GET /api/spiagge
    GET /api/eventi
    GET /api/panorami
    GET /api/parchi
    GET /api/all
    GET /api/search?q=<query>
"""
import json
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DATA_DIR = Path(__file__).parent.parent / "data"

def load_json(filename):
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return []

def search_data(query, data):
    """Search across all data by name and description."""
    query_lower = query.lower()
    results = []
    for category, items in data.items():
        for item in items:
            if (query_lower in item.get("nome", "").lower() or
                query_lower in item.get("descrizione", "").lower() or
                query_lower in item.get("comune", "").lower()):
                results.append({**item, "categoria": category})
    return results

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # CORS headers
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        
        if path == "/api/sentieri":
            data = load_json("sentieri.json")
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/monumenti":
            data = load_json("monumenti.json")
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/spiagge":
            data = load_json("spiagge.json")
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/eventi":
            data = load_json("eventi.json")
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/panorami":
            data = load_json("panorami.json")
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/parchi":
            data = load_json("parchi.json")
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/all":
            all_data = {
                "sentieri": load_json("sentieri.json"),
                "monumenti": load_json("monumenti.json"),
                "spiagge": load_json("spiagge.json"),
                "eventi": load_json("eventi.json"),
                "panorami": load_json("panorami.json"),
                "parchi": load_json("parchi.json")
            }
            self.wfile.write(json.dumps(all_data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/search":
            query = params.get("q", [""])[0]
            if query:
                all_data = {
                    "sentieri": load_json("sentieri.json"),
                    "monumenti": load_json("monumenti.json"),
                    "spiagge": load_json("spiagge.json"),
                    "eventi": load_json("eventi.json"),
                    "panorami": load_json("panorami.json"),
                    "parchi": load_json("parchi.json")
                }
                results = search_data(query, all_data)
                self.wfile.write(json.dumps(results, ensure_ascii=False, indent=2).encode())
            else:
                self.wfile.write(json.dumps({"error": "Missing query parameter 'q'"}, indent=2).encode())
        
        elif path == "/api/health":
            self.wfile.write(json.dumps({"status": "ok", "version": "1.0.0"}, indent=2).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}, indent=2).encode())
    
    def log_message(self, format, *args):
        print(f"[API] {args[0]}")

def main():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"=== Awesome Salerno API ===")
    print(f"Listening on http://localhost:{port}")
    print(f"\nEndpoints:")
    print(f"  GET /api/sentieri")
    print(f"  GET /api/monumenti")
    print(f"  GET /api/spiagge")
    print(f"  GET /api/eventi")
    print(f"  GET /api/panorami")
    print(f"  GET /api/parchi")
    print(f"  GET /api/all")
    print(f"  GET /api/search?q=<query>")
    print(f"  GET /api/health")
    print(f"\nPress Ctrl+C to stop.")
    server.serve_forever()

if __name__ == "__main__":
    main()
