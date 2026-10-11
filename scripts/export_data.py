#!/usr/bin/env python3
"""Rigenera i file derivati dei dati e lo specchio del sito, partendo da data/.

Fonte unica: i sei file di categoria in data/ (sentieri, monumenti, spiagge, eventi,
panorami, parchi). Da questi si ricostruiscono:

  data/all.json                 le sei categorie, nello stesso ordine di sempre
  data/awesome-salerno.geojson  un Point per ogni voce con lat e lng

Con --docs, dopo, docs/data/ diventa uno specchio identico di data/ (e' quello che
pubblica GitHub Pages). KML, KMZ, events.xml e data/rag/ li producono api/kml_export.py
e scripts/build_rag.py: vanno lanciati prima di --docs, qui si copiano soltanto.

Uso:
    python3 scripts/export_data.py            # ricostruisce all.json e GeoJSON
    python3 scripts/export_data.py --docs     # ... e rigenera docs/data/ da data/
    python3 scripts/export_data.py --check    # non scrive: esce 1 se all.json/GeoJSON sono fuori sincrono
    python3 scripts/export_data.py --check --docs   # ... e se docs/data/ differisce da data/

Solo libreria standard. Non modifica mai i file di categoria.
"""
import filecmp
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS_DATA = ROOT / "docs" / "data"
# ordine storico di all.json: lo leggono in quest'ordine anche i consumatori
CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]
# le stesse proprieta' (e lo stesso ordine) del GeoJSON pubblicato: provincia, sigla_provincia
# e in_ambito ci sono dall'arricchimento ISTAT, il vecchio script inline le perdeva
GEOJSON_PROPS = ["id", "nome", "descrizione", "zona", "citta", "quartiere", "provincia",
                 "sigla_provincia", "in_ambito", "tipo", "link", "last_verified"]
MAX_SHOWN = 10


def render(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def build_all():
    return {c: json.loads((DATA / f"{c}.json").read_text(encoding="utf-8")) for c in CATEGORIES}


def build_geojson(all_data):
    features = []
    for items in all_data.values():
        for it in items:
            if it.get("lat") and it.get("lng"):
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [it["lng"], it["lat"]]},
                    "properties": {k: it.get(k) for k in GEOJSON_PROPS},
                })
    return {"type": "FeatureCollection", "features": features}


def derived():
    all_data = build_all()
    return {"all.json": render(all_data), "awesome-salerno.geojson": render(build_geojson(all_data))}


def mirror_diff():
    """Differenze tra data/ e docs/data/: (mancanti, in piu', diversi)."""
    src = {p.relative_to(DATA).as_posix() for p in DATA.rglob("*") if p.is_file()}
    dst = {p.relative_to(DOCS_DATA).as_posix() for p in DOCS_DATA.rglob("*") if p.is_file()} \
        if DOCS_DATA.exists() else set()
    differ = sorted(n for n in src & dst if not filecmp.cmp(DATA / n, DOCS_DATA / n, shallow=False))
    return sorted(src - dst), sorted(dst - src), differ


def sync_docs():
    if DOCS_DATA.exists():
        shutil.rmtree(DOCS_DATA)
    shutil.copytree(DATA, DOCS_DATA)


def main(argv):
    check, docs = "--check" in argv, "--docs" in argv
    files = derived()
    problems = []
    for name, text in files.items():
        path = DATA / name
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                problems.append(f"data/{name} non coincide con i file di categoria: "
                                "lancia python3 scripts/export_data.py")
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            print(f"riscritto data/{name}")
        else:
            print(f"data/{name} gia' aggiornato")
    if docs:
        if check:
            missing, extra, differ = mirror_diff()
            if missing or extra or differ:
                shown = (missing + extra + differ)[:MAX_SHOWN]
                problems.append(f"docs/data fuori sincrono da data/ (mancanti {len(missing)}, in piu' "
                                f"{len(extra)}, diversi {len(differ)}; es. {shown}): "
                                "lancia python3 scripts/export_data.py --docs")
        else:
            sync_docs()
            print("docs/data rigenerato da data/")
    if problems:
        for p in problems:
            print("ERRORE:", p, file=sys.stderr)
        return 1
    if check:
        print("derivati" + (" e docs/data" if docs else "") + " aggiornati")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
