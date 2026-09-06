#!/usr/bin/env python3
"""
Overpass API scraper for tourism POI in Salerno province.
Queries: hiking trails, churches, castles, museums, beaches, parks, viewpoints, springs.
"""
import json
import time
import urllib.request
import urllib.parse

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Salerno province bounding box
BBOX = "39.9,14.4,40.8,15.5"

QUERIES = {
    "sentieri": f"""
[out:json][timeout:120];
(
  way["highway"="footway"]["sac_scale"]["name"]({BBOX});
  way["highway"="path"]["sac_scale"]["name"]({BBOX});
  way["route"="hiking"]["name"]({BBOX});
  relation["route"="hiking"]["name"]({BBOX});
);
out center tags;
""",
    "chiese": f"""
[out:json][timeout:120];
(
  way["amenity"="place_of_worship"]["religion"="christian"]["building"]["name"]({BBOX});
  node["amenity"="place_of_worship"]["religion"="christian"]["name"]({BBOX});
  relation["amenity"="place_of_worship"]["religion"="christian"]["name"]({BBOX});
);
out center tags;
""",
    "castelli": f"""
[out:json][timeout:120];
(
  way["historic"="castle"]["name"]({BBOX});
  node["historic"="castle"]["name"]({BBOX});
  way["historic"="fortress"]["name"]({BBOX});
  node["historic"="fortress"]["name"]({BBOX});
  way["man_made"="tower"]["name"]({BBOX});
  node["man_made"="tower"]["name"]({BBOX});
);
out center tags;
""",
    "musei": f"""
[out:json][timeout:120];
(
  way["tourism"="museum"]["name"]({BBOX});
  node["tourism"="museum"]["name"]({BBOX});
  way["tourism"="gallery"]["name"]({BBOX});
  node["tourism"="gallery"]["name"]({BBOX});
);
out center tags;
""",
    "spiagge": f"""
[out:json][timeout:120];
(
  way["natural"="beach"]["name"]({BBOX});
  node["natural"="beach"]["name"]({BBOX});
  way["leisure"="beach_resort"]["name"]({BBOX});
  node["leisure"="beach_resort"]["name"]({BBOX});
);
out center tags;
""",
    "parchi": f"""
[out:json][timeout:120];
(
  way["leisure"="nature_reserve"]["name"]({BBOX});
  relation["leisure"="nature_reserve"]["name"]({BBOX});
  way["boundary"="national_park"]["name"]({BBOX});
  relation["boundary"="national_park"]["name"]({BBOX});
  way["boundary"="protected_area"]["name"]({BBOX});
  relation["boundary"="protected_area"]["name"]({BBOX});
);
out center tags;
""",
    "panorami": f"""
[out:json][timeout:120];
(
  node["tourism"="viewpoint"]["name"]({BBOX});
  way["tourism"="viewpoint"]["name"]({BBOX});
);
out center tags;
""",
    "fonti": f"""
[out:json][timeout:120];
(
  node["natural"="spring"]["name"]({BBOX});
  way["natural"="spring"]["name"]({BBOX});
  node["amenity"="fountain"]["name"]({BBOX});
  way["amenity"="fountain"]["name"]({BBOX});
);
out center tags;
""",
    "archeologico": f"""
[out:json][timeout:120];
(
  way["historic"="archaeological_site"]["name"]({BBOX});
  node["historic"="archaeological_site"]["name"]({BBOX});
  way["historic"="temple"]["name"]({BBOX});
  node["historic"="temple"]["name"]({BBOX});
  way["historic"="ruins"]["name"]({BBOX});
  node["historic"="ruins"]["name"]({BBOX});
);
out center tags;
""",
    "grotte": f"""
[out:json][timeout:120];
(
  node["natural"="cave_entrance"]["name"]({BBOX});
  way["natural"="cave_entrance"]["name"]({BBOX});
  node["tourism"="cave"]["name"]({BBOX});
);
out center tags;
""",
    "monumenti": f"""
[out:json][timeout:120];
(
  node["historic"="monument"]["name"]({BBOX});
  way["historic"="monument"]["name"]({BBOX});
  node["historic"="memorial"]["name"]({BBOX});
  way["historic"="memorial"]["name"]({BBOX});
  node["historic"="statue"]["name"]({BBOX});
  way["historic"="statue"]["name"]({BBOX});
);
out center tags;
"""
}


def query_overpass(ql):
    """Execute Overpass query and return results."""
    data = urllib.parse.urlencode({"data": ql}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data, method="POST")
    req.add_header("User-Agent", "awesome-salerno/1.0")
    
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error: {e}")
        return None


def extract_tags(tags):
    """Extract useful fields from OSM tags."""
    name = tags.get("name", "")
    if not name:
        name = tags.get("name:it", tags.get("name:en", ""))
    
    desc_parts = []
    if tags.get("description"):
        desc_parts.append(tags["description"])
    if tags.get("historic"):
        desc_parts.append(f"Tipo: {tags['historic']}")
    if tags.get("religion"):
        desc_parts.append(f"Religione: {tags['religion']}")
    if tags.get("denomination"):
        desc_parts.append(f"Denominazione: {tags['denomination']}")
    
    return {
        "nome": name,
        "descrizione": ". ".join(desc_parts) if desc_parts else "",
        "wikipedia": tags.get("wikipedia", ""),
        "wikidata": tags.get("wikidata", ""),
        "website": tags.get("website", tags.get("contact:website", "")),
        "addr": tags.get("addr:street", "") + " " + tags.get("addr:housenumber", ""),
    }


def process_results(overpass_data, category):
    """Convert Overpass results to our format."""
    results = []
    
    for elem in overpass_data.get("elements", []):
        tags = elem.get("tags", {})
        lat = elem.get("lat") or (elem.get("center", {}).get("lat"))
        lng = elem.get("lon") or (elem.get("center", {}).get("lon"))
        
        if not lat or not lng:
            continue
        
        extracted = extract_tags(tags)
        if not extracted["nome"]:
            continue
        
        osm_id = elem.get("id", "")
        osm_type = elem.get("type", "")
        
        entry = {
            "id": f"osm-{osm_id}",
            "nome": extracted["nome"],
            "descrizione": extracted["descrizione"],
            "lat": lat,
            "lng": lng,
            "source": "osm",
            "osm_id": osm_id,
            "osm_type": osm_type,
        }
        
        # Add link
        if extracted["website"]:
            entry["link"] = extracted["website"]
        elif extracted["wikipedia"]:
            wiki = extracted["wikipedia"]
            if wiki.startswith("it:"):
                wiki = wiki[3:]
            entry["link"] = f"https://it.wikipedia.org/wiki/{wiki.replace(' ', '_')}"
        else:
            entry["link"] = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
        
        results.append(entry)
    
    return results


def main():
    all_results = {}
    
    for name, query in QUERIES.items():
        print(f"Querying {name}...")
        data = query_overpass(query)
        
        if data:
            processed = process_results(data, name)
            all_results[name] = processed
            print(f"  Found: {len(processed)}")
        else:
            all_results[name] = []
            print(f"  Failed")
        
        time.sleep(2)  # Rate limit
    
    # Save results
    with open("overpass_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    total = sum(len(v) for v in all_results.values())
    print(f"\nTotal: {total} POI")
    for k, v in all_results.items():
        print(f"  {k}: {len(v)}")


if __name__ == "__main__":
    main()
