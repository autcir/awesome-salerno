#!/usr/bin/env python3
"""
JSON API server for awesome-salerno data.

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
    GET /api/geojson
    GET /api/cities
    GET /api/health
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

def filter_items(items, params):
    """Filter items by zona, tipo, citta, and quartiere query params."""
    zona = params.get("zona", [""])[0].lower()
    tipo = params.get("tipo", [""])[0].lower()
    citta = params.get("citta", [""])[0].lower()
    quartiere = params.get("quartiere", [""])[0].lower()
    
    result = items
    if zona:
        result = [i for i in result if zona in i.get("zona", "").lower()]
    if tipo:
        result = [i for i in result if tipo in i.get("tipo", "").lower() or tipo in i.get("subcategoria", "").lower()]
    if citta:
        result = [i for i in result if citta in i.get("citta", "").lower()]
    if quartiere:
        result = [i for i in result if quartiere in i.get("quartiere", "").lower()]
    return result

def fuzzy_match(query, text):
    """Simple fuzzy matching - check if query words appear in text."""
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Exact match
    if query_lower in text_lower:
        return True
    
    # Word match
    query_words = query_lower.split()
    text_words = text_lower.split()
    
    for qw in query_words:
        if not any(tw.startswith(qw) for tw in text_words):
            return False
    
    return True

def search_data(query, data):
    """Search across all data with fuzzy matching on name, description, city, and quartiere."""
    results = []
    for category, items in data.items():
        for item in items:
            nome = item.get("nome", "")
            desc = item.get("descrizione", "")
            citta = item.get("citta", "")
            quartiere = item.get("quartiere", "")
            
            # Check all fields
            if (fuzzy_match(query, nome) or
                fuzzy_match(query, desc) or
                fuzzy_match(query, citta) or
                fuzzy_match(query, quartiere)):
                results.append({**item, "categoria": category})
    
    return results

def to_geojson(data):
    """Convert all data to GeoJSON format."""
    features = []
    for category, items in data.items():
        for item in items:
            if item.get("lat") and item.get("lng"):
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [item["lng"], item["lat"]]
                    },
                    "properties": {
                        "id": item.get("id"),
                        "nome": item.get("nome"),
                        "descrizione": item.get("descrizione"),
                        "zona": item.get("zona"),
                        "citta": item.get("citta"),
                        "quartiere": item.get("quartiere"),
                        "tipo": item.get("tipo"),
                        "categoria": category,
                        "link": item.get("link")
                    }
                }
                features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

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
            data = filter_items(load_json("sentieri.json"), params)
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/monumenti":
            data = filter_items(load_json("monumenti.json"), params)
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/spiagge":
            data = filter_items(load_json("spiagge.json"), params)
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/eventi":
            data = filter_items(load_json("eventi.json"), params)
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/panorami":
            data = filter_items(load_json("panorami.json"), params)
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/parchi":
            data = filter_items(load_json("parchi.json"), params)
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/all":
            all_data = {
                "sentieri": filter_items(load_json("sentieri.json"), params),
                "monumenti": filter_items(load_json("monumenti.json"), params),
                "spiagge": filter_items(load_json("spiagge.json"), params),
                "eventi": filter_items(load_json("eventi.json"), params),
                "panorami": filter_items(load_json("panorami.json"), params),
                "parchi": filter_items(load_json("parchi.json"), params)
            }
            self.wfile.write(json.dumps(all_data, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/geojson":
            all_data = {
                "sentieri": load_json("sentieri.json"),
                "monumenti": load_json("monumenti.json"),
                "spiagge": load_json("spiagge.json"),
                "eventi": load_json("eventi.json"),
                "panorami": load_json("panorami.json"),
                "parchi": load_json("parchi.json")
            }
            geojson = to_geojson(all_data)
            self.wfile.write(json.dumps(geojson, ensure_ascii=False, indent=2).encode())
        
        elif path == "/api/cities":
            all_data = load_json("all.json")
            cities = {}
            for cat, items in all_data.items():
                for item in items:
                    citta = item.get("citta", "")
                    if citta:
                        if citta not in cities:
                            cities[citta] = {"nome": citta, "count": 0, "zona": item.get("zona", "")}
                        cities[citta]["count"] += 1
            self.wfile.write(json.dumps(list(cities.values()), ensure_ascii=False, indent=2).encode())
        
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
            self.wfile.write(json.dumps({"status": "ok", "version": "2.0.0"}, indent=2).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}, indent=2).encode())
    
    def log_message(self, format, *args):
        print(f"[API] {args[0]}")

def main():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"=== Awesome Salerno API v2.0 ===")
    print(f"Listening on http://localhost:{port}")
    print(f"\nEndpoints:")
    print(f"  GET /api/sentieri?zona=<costiera|cilento|salerno>")
    print(f"  GET /api/monumenti?tipo=<chiesa|castello|museo|archeologico>")
    print(f"  GET /api/all?citta=<nome>&quartiere=<nome>")
    print(f"  GET /api/search?q=<query>")
    print(f"  GET /api/geojson")
    print(f"  GET /api/cities")
    print(f"  GET /api/health")
    print(f"\nPress Ctrl+C to stop.")
    server.serve_forever()

if __name__ == "__main__":
    main()
