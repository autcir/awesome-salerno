#!/usr/bin/env python3
"""Genera data/manifest.json: conteggi, sha256 di ogni file in data/, fonti e licenze.

Il manifest e' un file a parte: non entra mai in all.json (vedi docs/CONTRACT.md).

Riproducibile e idempotente: nessun orologio. `generated_at` e' la data piu'
recente trovata nei dati (`last_verified`, `retrieved_at`), oppure
SOURCE_DATE_EPOCH se impostata. Stessi dati -> stesso byte.

Uso:
    python3 scripts/build_manifest.py           # scrive data/manifest.json
    python3 scripts/build_manifest.py --check   # esce 1 se il file e' fuori sincrono
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MANIFEST = DATA / "manifest.json"
SCHEMA_VERSION = 1
CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]

# Licenza per valore di `source`. Specchio di DATA-LICENSES.md. Non e' un parere
# legale: la licenza del dataset composto la conferma il titolare.
SOURCE_LICENSES = {
    "osm": {
        "name": "OpenStreetMap",
        "license": "ODbL-1.0",
        "attribution": "© OpenStreetMap contributors",
        "url": "https://www.openstreetmap.org/copyright",
        "obligations": "attribuzione; condivisione allo stesso modo per i database derivati",
    },
    "hand-written": {
        "name": "Curatori del progetto (scritte a mano)",
        "license": "da confermare dal titolare (LICENSE dichiara CC0-1.0)",
        "attribution": None,
        "url": None,
        "obligations": None,
    },
    "curated": {
        "name": "Curatori del progetto (verificate su fonti pubbliche)",
        "license": "da confermare dal titolare (LICENSE dichiara CC0-1.0)",
        "attribution": None,
        "url": None,
        "obligations": None,
    },
    "web": {
        "name": "Eventi da pagine di enti e testate (vedi data/sources.json)",
        "license": "per fonte, vedi data/sources.json; spesso da verificare",
        "attribution": None,
        "url": None,
        "obligations": None,
    },
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def latest_date(all_data, scraped):
    dates = [it["last_verified"] for items in all_data.values() for it in items
             if isinstance(it.get("last_verified"), str)]
    dates += [it["retrieved_at"][:10] for it in scraped
              if isinstance(it.get("retrieved_at"), str)]
    return max(dates) if dates else "1970-01-01"


def generated_at(all_data, scraped):
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        return datetime.fromtimestamp(int(epoch), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return latest_date(all_data, scraped) + "T00:00:00Z"


def data_files():
    out = []
    for p in sorted(DATA.rglob("*")):
        if p.is_file() and p != MANIFEST:
            out.append(p)
    return out


def build():
    all_data = load("all.json")
    scraped = load("eventi_scraped.json")
    eventi = load("eventi.json")

    counts = {k: len(all_data[k]) for k in CATEGORIES}
    items = [it for k in CATEGORIES for it in all_data[k]]
    by_source = {}
    for it in items:
        by_source[it.get("source")] = by_source.get(it.get("source"), 0) + 1
    wiki_links = sum(1 for it in items
                     if (urlparse(it.get("link") or "").hostname or "").endswith("wikipedia.org"))

    sources = []
    for key in sorted(SOURCE_LICENSES):
        entry = {"source": key, "records": by_source.get(key, 0)}
        entry.update(SOURCE_LICENSES[key])
        sources.append(entry)
    unknown = sorted(str(k) for k in by_source if k not in SOURCE_LICENSES)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at(all_data, scraped),
        "generator": "scripts/build_manifest.py",
        "dataset": {"name": "awesome-salerno", "scope": "Salerno, Costiera Amalfitana, Cilento"},
        "counts": {
            "all_json": {"total": sum(counts.values()), **counts},
            "eventi_json": len(eventi),
            "eventi_scraped_json": len(scraped),
            "link_wikipedia": wiki_links,
        },
        "licensing": {
            "note": "Le licenze dipendono dalla fonte (DATA-LICENSES.md). "
                    "La licenza del dataset composto la conferma il titolare.",
            "sources": sources,
            "sources_without_license_entry": unknown,
        },
        "files": [
            {"path": p.relative_to(DATA).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in data_files()
        ],
    }


def render(manifest):
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main():
    text = render(build())
    if "--check" in sys.argv:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        if current != text:
            print("data/manifest.json fuori sincrono: lancia python3 scripts/build_manifest.py",
                  file=sys.stderr)
            return 1
        print("data/manifest.json aggiornato")
        return 0
    MANIFEST.write_text(text, encoding="utf-8")
    print(f"scritto {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
