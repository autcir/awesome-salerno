#!/usr/bin/env python3
"""
Export POI data from salernos data files to awesome-salerno/data/ as JSON and CSV.
"""
import json
import csv
import os
from pathlib import Path

SOURCE = Path("/home/autcir/Work/er0s/web/src/entities/tenant/salernos/data")
DEST = Path("/home/autcir/Work/awesome-salerno/data")

DEST.mkdir(exist_ok=True)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def flatten_poi(poi, category):
    """Flatten a POI dict to a simple format for awesome-salerno."""
    rating = poi.get("rating") or {}
    return {
        "id": poi.get("id", ""),
        "name": poi.get("title", ""),
        "category": category,
        "subcategory": poi.get("subcategory", ""),
        "address": poi.get("address", ""),
        "district": poi.get("district", ""),
        "lat": poi.get("lat") or "",
        "lng": poi.get("lng") or "",
        "rating_score": rating.get("score") or "",
        "rating_count": rating.get("count") or 0,
        "description": poi.get("description", ""),
        "source": poi.get("source", ""),
    }

def main():
    all_pois = []
    category_map = {
        "mangiare.json": "food",
        "luoghi.json": "attractions",
        "dormire.json": "accommodation",
        "spiagge.json": "beaches",
    }
    
    for filename, category in category_map.items():
        source_path = SOURCE / filename
        if not source_path.exists():
            print(f"  SKIP {filename}: not found")
            continue
        
        data = load_json(source_path)
        print(f"  {filename}: {len(data)} entries")
        
        # Save as JSON
        dest_json = DEST / filename.replace(".json", ".json")
        with open(dest_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"    -> {dest_json}")
        
        # Flatten for CSV
        for poi in data:
            all_pois.append(flatten_poi(poi, category))
    
    # Save combined JSON
    combined_path = DEST / "all-pois.json"
    with open(combined_path, 'w', encoding='utf-8') as f:
        json.dump(all_pois, f, indent=2, ensure_ascii=False)
    print(f"\n  Combined: {len(all_pois)} POI -> {combined_path}")
    
    # Save combined CSV
    csv_path = DEST / "all-pois.csv"
    if all_pois:
        fieldnames = all_pois[0].keys()
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_pois)
        print(f"  CSV: {len(all_pois)} rows -> {csv_path}")

if __name__ == "__main__":
    print("Exporting POI data...")
    main()
    print("Done!")
