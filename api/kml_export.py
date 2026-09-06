#!/usr/bin/env python3
"""
KML/KMZ export for awesome-salerno data.

Reads the six per-category JSON files from data/ and generates:
  - data/awesome-salerno.kml  (plain KML, one Folder per category)
  - data/awesome-salerno.kmz  (zipped KML containing doc.kml)

Each category becomes a KML <Folder> holding one <Placemark> per POI
with GPS coordinates (Point + coordinates lng,lat,0).

Usage:
    python3 api/kml_export.py
"""

import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

KML_PATH = DATA_DIR / "awesome-salerno.kml"
KMZ_PATH = DATA_DIR / "awesome-salerno.kmz"

CATEGORIES = {
    "sentieri": {
        "folder_name": "Sentieri",
        "icon": "http://maps.google.com/mapfiles/kml/paddle/go.png",
        "color": "ff00ae14",
    },
    "monumenti": {
        "folder_name": "Monumenti",
        "icon": "http://maps.google.com/mapfiles/kml/paddle/red-circle.png",
        "color": "ff3498db",
    },
    "spiagge": {
        "folder_name": "Spiagge",
        "icon": "http://maps.google.com/mapfiles/kml/paddle/ylw-stars.png",
        "color": "ff00f3f9",
    },
    "eventi": {
        "folder_name": "Eventi",
        "icon": "http://maps.google.com/mapfiles/kml/paddle/red-stars.png",
        "color": "ff4ecdc4",
    },
    "panorami": {
        "folder_name": "Panorami",
        "icon": "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png",
        "color": "ff1abc9c",
    },
    "parchi": {
        "folder_name": "Parchi",
        "icon": "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png",
        "color": "ff2980b9",
    },
}


def load_category(name):
    """Load one data/<name>.json file, returning a list (empty if missing)."""
    filepath = DATA_DIR / f"{name}.json"
    if not filepath.exists():
        print(f"  WARN: {filepath} not found, skipping")
        return []
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    # data files are plain lists; tolerate a dict wrapper just in case
    if isinstance(data, dict):
        data = data.get(name, [])
    return data if isinstance(data, list) else []


def esc_attr(value):
    """Escape a string for use inside an XML/HTML attribute."""
    return escape(str(value), {'"': "&quot;"})


def build_description(item, category):
    """Human-readable HTML description for a Placemark balloon."""
    parts = []
    if item.get("descrizione"):
        parts.append(escape(item["descrizione"]))

    meta = []
    if item.get("zona"):
        meta.append(f"Zona: {escape(str(item['zona']).title())}")
    if item.get("citta"):
        meta.append(f"Città: {escape(str(item['citta']))}")
    if item.get("quartiere"):
        meta.append(f"Quartiere: {escape(str(item['quartiere']))}")
    if item.get("tipo"):
        meta.append(f"Tipo: {escape(str(item['tipo']))}")
    if meta:
        parts.append(" | ".join(meta))

    if category == "eventi":
        dates = []
        if item.get("data_inizio"):
            dates.append(f"Da: {escape(str(item['data_inizio']))}")
        if item.get("data_fine"):
            dates.append(f"A: {escape(str(item['data_fine']))}")
        if dates:
            parts.append(" | ".join(dates))
        if item.get("ricorrenza"):
            parts.append(f"Ricorrenza: {escape(str(item['ricorrenza']))}")
        if item.get("edizione"):
            parts.append(f"Edizione: {escape(str(item['edizione']))}")
        if item.get("luoghi"):
            luoghi = ", ".join(escape(str(x)) for x in item["luoghi"])
            parts.append(f"Luoghi: {luoghi}")

    if item.get("link"):
        parts.append(f'<a href="{esc_attr(item["link"])}">Link</a>')

    return "<br/>\n".join(parts)


def style_id_for(category):
    return f"style-{category}"


def build_placemark(item, category):
    """One KML Placemark for a single POI dict."""
    name = escape(str(item.get("nome", "Senza nome")))
    desc = build_description(item, category)
    lat = item.get("lat", 0)
    lng = item.get("lng", 0)
    id_attr = ""
    if item.get("id"):
        id_attr = f' id="{esc_attr(item["id"])}"'

    return (
        f"      <Placemark{id_attr}>\n"
        f"        <name>{name}</name>\n"
        f"        <description><![CDATA[{desc}]]></description>\n"
        f"        <styleUrl>#{style_id_for(category)}</styleUrl>\n"
        f"        <Point>\n"
        f"          <coordinates>{lng},{lat},0</coordinates>\n"
        f"        </Point>\n"
        f"      </Placemark>"
    )


def build_kml(data_by_category):
    """Assemble the full KML document with one Folder per category."""
    total_loaded = sum(len(v) for v in data_by_category.values())

    style_defs = []
    for cat_key, cat_info in CATEGORIES.items():
        style_defs.append(
            f'      <Style id="{style_id_for(cat_key)}">\n'
            f"        <IconStyle>\n"
            f"          <color>{cat_info['color']}</color>\n"
            f"          <scale>1.0</scale>\n"
            f"          <Icon>\n"
            f"            <href>{cat_info['icon']}</href>\n"
            f"          </Icon>\n"
            f"        </IconStyle>\n"
            f"        <LabelStyle>\n"
            f"          <scale>0.8</scale>\n"
            f"        </LabelStyle>\n"
            f"      </Style>"
        )

    folders = []
    placed_total = 0
    for cat_key, cat_info in CATEGORIES.items():
        items = data_by_category.get(cat_key, [])
        placemarks = []
        for item in items:
            lat = item.get("lat")
            lng = item.get("lng")
            if lat is None or lng is None:
                continue
            try:
                float(lat)
                float(lng)
            except (TypeError, ValueError):
                continue
            if not lat and not lng:
                continue
            placemarks.append(build_placemark(item, cat_key))
        placed_total += len(placemarks)
        if not placemarks:
            continue
        folder_xml = (
            f"    <Folder>\n"
            f"      <name>{cat_info['folder_name']} ({len(placemarks)})</name>\n"
            f"      <description>POI categoria {cat_info['folder_name']}</description>\n"
            + "\n".join(placemarks)
            + "\n    </Folder>"
        )
        folders.append(folder_xml)

    kml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2"\n'
        '     xmlns:gx="http://www.google.com/kml/ext/2.2">\n'
        "  <Document>\n"
        "    <name>Awesome Salerno</name>\n"
        f"    <description>Curated tourism data for Salerno, Amalfi Coast and Cilento. "
        f"{placed_total} POI with GPS coordinates.</description>\n"
        "    <open>1</open>\n"
        "    <visibility>1</visibility>\n"
        "\n"
        '    <Style id="style-default">\n'
        "      <IconStyle>\n"
        "        <scale>1.0</scale>\n"
        "      </IconStyle>\n"
        "    </Style>\n"
        "\n"
        + "\n".join(style_defs)
        + "\n\n"
        + "\n".join(folders)
        + "\n\n  </Document>\n</kml>\n"
    )

    return kml, total_loaded, placed_total


def build_kmz(kml_content, kmz_path):
    """Write the KMZ zip containing the KML as doc.kml."""
    with zipfile.ZipFile(kmz_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_content)


def main():
    print("=== Awesome Salerno KML Export ===\n")

    data_by_category = {}
    for cat_key in CATEGORIES:
        print(f"  Loading {cat_key}.json ...")
        data_by_category[cat_key] = load_category(cat_key)

    kml_content, total_loaded, placed_total = build_kml(data_by_category)
    print(f"\n  Total POI loaded: {total_loaded}")
    print(f"  Placemarks with coordinates: {placed_total}")

    with open(KML_PATH, "w", encoding="utf-8") as f:
        f.write(kml_content)
    print(f"  Written: {KML_PATH}")

    build_kmz(kml_content, KMZ_PATH)
    print(f"  Written: {KMZ_PATH}")

    print(f"\n  Done! {placed_total} POI exported.")


if __name__ == "__main__":
    main()
