#!/usr/bin/env python3
"""Genera voci Markdown per il README dai file data/*.json reali.

Regole (contenuto solo verificato):
- ogni voce usa SOLO: nome (title) + comune/district dal file dati;
- link mappa OpenStreetMap in formato ``#map=16/LAT/LNG`` SOLO se lat/lng
  presenti (mai ID numerici node/way/relation, mai TripAdvisor);
- niente indirizzi, niente domini esterni, niente superlativi.

Uso:
    python3 scripts/gen_pois_md.py [--section spiagge|attrazioni|food|stay|all]
                                   [--limit N] [--min-count N] [--stats]
"""

import argparse
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

OSM_URL = "https://www.openstreetmap.org/#map=16/{lat:.5f}/{lng:.5f}"

# Titoli che indicano approdi/infrastrutture (non spiagge balneabili).
BEACH_EXCLUDE = (
    "marina",
    "porto",
    "porticciolo",
    "ormeggi",
    "yachting",
    "militare",
    "azimut",
    "associazione",
    "imbarco",
)

# Categorie di luoghi.json ammesse nella sezione Attrazioni.
ATTRACTION_CATEGORIES = {"monument", "church", "museum", "art", "gallery"}


def load(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def clean_title(title):
    return re.sub(r"\s+", " ", (title or "").strip())


def norm(title):
    return clean_title(title).lower()


def rating_of(entry):
    rating = entry.get("rating") or {}
    try:
        count = int(rating.get("count") or 0)
    except (TypeError, ValueError):
        count = 0
    return count


def has_coords(entry):
    return isinstance(entry.get("lat"), (int, float)) and isinstance(
        entry.get("lng"), (int, float)
    )


def osm_link(entry):
    if not has_coords(entry):
        return None
    return OSM_URL.format(lat=entry["lat"], lng=entry["lng"])


def dedup(entries):
    seen = set()
    out = []
    for e in entries:
        key = norm(e.get("title", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def district_of(entry):
    return (entry.get("district") or "Salerno").strip() or "Salerno"


def to_line(entry, kind_label):
    """Una voce: nome linkato alla mappa OSM + etichetta di categoria.
    Niente comune: il campo district dei dati vale sempre "Salerno" anche
    per record fuori comune (es. Maiori) — scriverlo mentirebbe."""
    title = clean_title(entry.get("title", ""))
    link = osm_link(entry)
    if link:
        return f"- [{title}]({link}) - {kind_label}."
    return f"- {title} - {kind_label}."


def pick(entries, limit, min_count=0, curated_first=True):
    rows = [e for e in entries if rating_of(e) >= min_count]
    # curated prima, poi count discendente, poi titolo A-Z
    rows.sort(
        key=lambda e: (
            not e.get("curated") if curated_first else False,
            -rating_of(e),
            norm(e.get("title", "")),
        )
    )
    return dedup(rows)[:limit]


def spiagge_entries():
    out = []
    for e in load("spiagge.json"):
        t = norm(e.get("title", ""))
        if not t:
            continue
        if ("spiaggia" not in t and "lido" not in t and "beach" not in t
                and "duoglio" not in t):
            continue
        if any(tok in t for tok in BEACH_EXCLUDE):
            continue
        out.append(e)
    return out


def attrazioni_entries():
    out = []
    for e in load("luoghi.json"):
        if e.get("category") not in ATTRACTION_CATEGORIES:
            continue
        if not clean_title(e.get("title")):
            continue
        out.append(e)
    return out


def food_entries():
    return [e for e in load("mangiare.json") if clean_title(e.get("title"))]


def stay_entries():
    return [e for e in load("dormire.json") if clean_title(e.get("title"))]


SECTIONS = {
    "spiagge": (spiagge_entries, "Spiaggia", 10, 0),
    "attrazioni": (attrazioni_entries, "Luogo di interesse", 12, 10),
    "food": (food_entries, "Locale", 10, 0),
    "stay": (stay_entries, "Struttura", 10, 0),
}


def render(section, limit=None, min_count=None):
    loader, label, default_limit, default_min = SECTIONS[section]
    entries = pick(
        loader(),
        limit=limit or default_limit,
        min_count=default_min if min_count is None else min_count,
    )
    return [to_line(e, label) for e in entries]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", default="all",
                        choices=list(SECTIONS) + ["all"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-count", type=int, default=None)
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args(argv)

    sections = list(SECTIONS) if args.section == "all" else [args.section]
    total = 0
    for section in sections:
        lines = render(section, limit=args.limit, min_count=args.min_count)
        total += len(lines)
        if args.stats:
            print(f"{section}: {len(lines)} voci")
        else:
            print(f"### {section.capitalize()}")
            print()
            for line in lines:
                print(line)
            print()
    if args.stats:
        print(f"totale: {total} voci")


if __name__ == "__main__":
    sys.exit(main())
