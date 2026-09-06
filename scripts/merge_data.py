#!/usr/bin/env python3
"""
Merge all POI data sources into awesome-salerno JSON files.
Sources: Overpass, agent outputs, hand-written data.
Deduplication by GPS proximity + name similarity.
"""
import json
import math
import re
from pathlib import Path

DATA_DIR = Path("data")
OVERPASS_FILE = "overpass_results.json"
AGENT_FILE = "/tmp/useful_pois.json"


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def is_duplicate(existing, new, threshold_m=100):
    for e in existing:
        dist = haversine(e["lat"], e["lng"], new["lat"], new["lng"])
        if dist < threshold_m:
            name1 = e.get("nome", "").lower().strip()
            name2 = new.get("nome", "").lower().strip()
            if name1 == name2:
                return True
            if name1 and name2 and (name1 in name2 or name2 in name1):
                return True
    return False


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-")


# ---- OVERPASS CATEGORIZATION ----
# Overpass subcategories map directly to our categories
OVERPASS_MAP = {
    "sentieri": "sentieri",
    "chiese": "monumenti",
    "castelli": "monumenti",
    "musei": "monumenti",
    "monumenti": "monumenti",
    "archeologico": "monumenti",
    "fonti": "monumenti",
    "grotte": "monumenti",
    "spiagge": "spiagge",
    "parchi": "parchi",
    "panorami": "panorami",
}

# ---- AGENT CATEGORIZATION ----
AGENT_MAP = {
    "cima": "panorami",
    "mirador": "panorami",
    "viewpoint": "panorami",
    "peak": "panorami",
    "chiesa": "monumenti",
    "cattedrale": "monumenti",
    "museo": "monumenti",
    "monumento": "monumenti",
    "castillo": "monumenti",
    "castello": "monumenti",
    "atraccion": "monumenti",
    "attraction": "monumenti",
    "yacimiento": "monumenti",
    "archaeological_site": "monumenti",
    "fuente": "monumenti",
    "spring": "monumenti",
    "religion": "monumenti",
    "history": "monumenti",
    "nature": "panorami",
}


def categorize_overpass(item):
    subcat = item.get("subcategoria", "")
    return OVERPASS_MAP.get(subcat, "monumenti")


def categorize_agent(item):
    subcat = item.get("subcategoria", item.get("categoria", "")).lower()
    return AGENT_MAP.get(subcat, "monumenti")


def load_overpass():
    with open(OVERPASS_FILE) as f:
        data = json.load(f)

    all_pois = []
    for category, items in data.items():
        for item in items:
            target = OVERPASS_MAP.get(category, "monumenti")
            all_pois.append({
                "nome": item.get("nome", ""),
                "descrizione": item.get("descrizione", ""),
                "lat": item.get("lat", 0),
                "lng": item.get("lng", 0),
                "source": "osm",
                "link": item.get("link", ""),
                "_target": target,
            })
    return all_pois


def load_agents():
    try:
        with open(AGENT_FILE) as f:
            data = json.load(f)

        all_pois = []
        for item in data:
            subcat = item.get("subcategoria", item.get("categoria", "")).lower()
            target = AGENT_MAP.get(subcat, "monumenti")
            all_pois.append({
                "nome": item.get("nome", ""),
                "descrizione": item.get("descrizione", ""),
                "lat": item.get("lat", 0),
                "lng": item.get("lng", 0),
                "source": "osm",
                "link": "",
                "_target": target,
            })
        return all_pois
    except FileNotFoundError:
        return []


def load_handwritten():
    all_pois = []
    for f in ["sentieri.json", "monumenti.json", "spiagge.json", "eventi.json", "panorami.json", "parchi.json"]:
        filepath = DATA_DIR / f
        if filepath.exists():
            with open(filepath) as fh:
                data = json.load(fh)
            category = f.replace(".json", "")
            for item in data:
                all_pois.append({
                    "nome": item.get("nome", ""),
                    "descrizione": item.get("descrizione", ""),
                    "lat": item.get("lat", 0),
                    "lng": item.get("lng", 0),
                    "source": item.get("source", "hand-written"),
                    "link": item.get("link", ""),
                    "_target": category,
                    "id": item.get("id", ""),
                    "difficolta": item.get("difficolta", ""),
                    "lunghezza_km": item.get("lunghezza_km", None),
                    "dislivello_m": item.get("dislivello_m", None),
                    "periodo": item.get("periodo", ""),
                    "frequenza": item.get("frequenza", ""),
                    "tipo": item.get("tipo", ""),
                })
    return all_pois


def main():
    print("Loading data sources...")

    overpass = load_overpass()
    agents = load_agents()
    handwritten = load_handwritten()

    print(f"  Overpass: {len(overpass)}")
    print(f"  Agents:   {len(agents)}")
    print(f"  Written:  {len(handwritten)}")

    # Combine (hand-written takes priority for dedup)
    all_pois = handwritten + overpass + agents

    # Validate GPS
    valid = [p for p in all_pois if 39 < p["lat"] < 42 and 14 < p["lng"] < 16]
    print(f"  Valid GPS: {len(valid)}")

    # Split by target category BEFORE dedup
    by_cat = {}
    for poi in valid:
        cat = poi.pop("_target")
        by_cat.setdefault(cat, []).append(poi)

    # Dedup within each category
    final = {}
    for cat, items in by_cat.items():
        deduped = []
        for poi in items:
            if not is_duplicate(deduped, poi):
                deduped.append(poi)
        final[cat] = deduped

    # Add IDs and clean up
    for cat, items in final.items():
        for i, item in enumerate(items):
            if "id" not in item or not item["id"]:
                item["id"] = f"{cat}-{slugify(item['nome'])}-{i}"
            # Remove internal fields
            item.pop("_target", None)
            # Ensure link
            if not item.get("link"):
                item["link"] = f"https://www.openstreetmap.org/?mlat={item['lat']}&mlon={item['lng']}#map=16/{item['lat']}/{item['lng']}"

    # Save per-category files
    for cat, items in final.items():
        filepath = DATA_DIR / f"{cat}.json"
        with open(filepath, "w") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"  {cat}.json: {len(items)}")

    # Save all.json
    with open(DATA_DIR / "all.json", "w") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    total = sum(len(v) for v in final.values())
    print(f"\nTotal: {total} POI")
    for k, v in sorted(final.items()):
        print(f"  {k}: {len(v)}")


if __name__ == "__main__":
    main()
