#!/usr/bin/env python3
"""
Wikidata SPARQL scraper for tourism POI in Salerno province.
Queries: churches, castles, museums, archaeological sites, monuments.
"""
import json
import time
import urllib.request
import urllib.parse

WIKIDATA_URL = "https://query.wikidata.org/sparql"

# Salerno province Q-code: Q132653
# Campania region Q-code: Q1436

QUERIES = {
    "chiese_wikidata": """
SELECT ?item ?itemLabel ?itemDescription ?lat ?lon ?wikipedia ?image WHERE {
  ?item wdt:P31/wdt:P279* wd:Q16970.
  ?item wdt:P131* wd:Q132653.
  ?item p:P625 ?coord.
  ?coord psv:P625 ?coordinates.
  ?coordinates wikibase:latitude ?lat.
  ?coordinates wikibase:longitude ?lon.
  OPTIONAL { ?item wdt:P18 ?image. }
  OPTIONAL { ?item rdfs:label ?wikipedia. FILTER(LANG(?wikipedia) = "it") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
} LIMIT 1000
""",
    "castelli_wikidata": """
SELECT ?item ?itemLabel ?itemDescription ?lat ?lon ?wikipedia WHERE {
  ?item wdt:P31/wdt:P279* wd:Q23413.
  ?item wdt:P131* wd:Q132653.
  ?item p:P625 ?coord.
  ?coord psv:P625 ?coordinates.
  ?coordinates wikibase:latitude ?lat.
  ?coordinates wikibase:longitude ?lon.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
} LIMIT 500
""",
    "musei_wikidata": """
SELECT ?item ?itemLabel ?itemDescription ?lat ?lon ?wikipedia WHERE {
  ?item wdt:P31/wdt:P279* wd:Q33506.
  ?item wdt:P131* wd:Q132653.
  ?item p:P625 ?coord.
  ?coord psv:P625 ?coordinates.
  ?coordinates wikibase:latitude ?lat.
  ?coordinates wikibase:longitude ?lon.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
} LIMIT 500
""",
    "archeologico_wikidata": """
SELECT ?item ?itemLabel ?itemDescription ?lat ?lon ?wikipedia WHERE {
  ?item wdt:P31/wdt:P279* wd:Q83620.
  ?item wdt:P131* wd:Q132653.
  ?item p:P625 ?coord.
  ?coord psv:P625 ?coordinates.
  ?coordinates wikibase:latitude ?lat.
  ?coordinates wikibase:longitude ?lon.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
} LIMIT 500
""",
    "monumenti_wikidata": """
SELECT ?item ?itemLabel ?itemDescription ?lat ?lon ?wikipedia WHERE {
  ?item wdt:P31/wdt:P279* wd:Q5107.
  ?item wdt:P131* wd:Q132653.
  ?item p:P625 ?coord.
  ?coord psv:P625 ?coordinates.
  ?coordinates wikibase:latitude ?lat.
  ?coordinates wikibase:longitude ?lon.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
} LIMIT 500
""",
}


def query_wikidata(sparql):
    """Execute SPARQL query."""
    params = urllib.parse.urlencode({
        "query": sparql,
        "format": "json"
    })
    req = urllib.request.Request(f"{WIKIDATA_URL}?{params}")
    req.add_header("User-Agent", "awesome-salerno/1.0 (research)")
    req.add_header("Accept", "application/sparql-results+json")
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error: {e}")
        return None


def process_results(data, category):
    """Convert SPARQL results to our format."""
    results = []
    seen = set()
    
    for binding in data.get("results", {}).get("bindings", []):
        item_uri = binding.get("item", {}).get("value", "")
        qid = item_uri.split("/")[-1] if item_uri else ""
        
        if qid in seen:
            continue
        seen.add(qid)
        
        name = binding.get("itemLabel", {}).get("value", "")
        if not name:
            continue
        
        lat = float(binding.get("lat", {}).get("value", 0))
        lng = float(binding.get("lon", {}).get("value", 0))
        
        if lat == 0 and lng == 0:
            continue
        
        desc = binding.get("itemDescription", {}).get("value", "")
        
        wiki = binding.get("wikipedia", {}).get("value", "")
        
        entry = {
            "id": f"wikidata-{qid}",
            "nome": name,
            "descrizione": desc,
            "lat": lat,
            "lng": lng,
            "wikidata": qid,
            "source": "wikidata",
        }
        
        if wiki:
            entry["link"] = f"https://it.wikipedia.org/wiki/{wiki.replace(' ', '_')}"
        else:
            entry["link"] = f"https://www.wikidata.org/wiki/{qid}"
        
        results.append(entry)
    
    return results


def main():
    all_results = {}
    
    for name, sparql in QUERIES.items():
        print(f"Querying {name}...")
        data = query_wikidata(sparql)
        
        if data:
            processed = process_results(data, name)
            all_results[name] = processed
            print(f"  Found: {len(processed)}")
        else:
            all_results[name] = []
            print(f"  Failed")
        
        time.sleep(3)  # Rate limit
    
    # Save
    with open("wikidata_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    total = sum(len(v) for v in all_results.values())
    print(f"\nTotal: {total} POI")
    for k, v in all_results.items():
        print(f"  {k}: {len(v)}")


if __name__ == "__main__":
    main()
