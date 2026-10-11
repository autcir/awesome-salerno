#!/usr/bin/env python3
"""Valida tutti i data/*.json contro gli schema in schema/ (JSON Schema 2020-12).

Tre livelli:
  1. Schema: struttura e tipi di ogni file (errori duri).
  2. Controlli incrociati: id unici, all.json = unione delle sei categorie,
     limiti GPS (schema/limits.json), liste eventi non vuote (errori duri).
  3. Qualita' con ratchet: i problemi gia' presenti stanno in
     schema/quality-baseline.json e non fanno fallire la CI; fallisce solo una
     violazione NUOVA. I dati non vengono mai modificati da questo script.

Uso:
    python3 scripts/validate_data.py                  # valida (esce 1 se errori o violazioni nuove)
    python3 scripts/validate_data.py --write-reports  # riscrive data/reports/*.json
    python3 scripts/validate_data.py --check-reports  # esce 1 se i report sono fuori sincrono
    python3 scripts/validate_data.py --update-baseline  # accetta le violazioni attuali (da usare con motivo)

Richiede jsonschema (requirements.txt).
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
except ImportError:
    sys.exit("manca jsonschema: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMA = ROOT / "schema"
REPORTS = DATA / "reports"
BASELINE = SCHEMA / "quality-baseline.json"
CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]
MAX_SHOWN = 15

# file in data/ -> schema. I file senza schema (derivati o non JSON) non si elencano.
SCHEMAS = {
    "all.json": "all.schema.json",
    "sentieri.json": ("poi.schema.json", "list"),
    "monumenti.json": ("poi.schema.json", "list"),
    "spiagge.json": ("poi.schema.json", "list"),
    "panorami.json": ("poi.schema.json", "list"),
    "parchi.json": ("poi.schema.json", "list"),
    "eventi.json": ("evento.schema.json", "list"),
    "eventi_scraped.json": ("evento-scraped.schema.json", "list"),
    "sources.json": "sources.schema.json",
    "comuni_provincia.json": "comuni.schema.json",
    "broken_links.json": "broken-links.schema.json",
    "voice-assistant.json": "voice-assistant.schema.json",
    "manifest.json": "manifest.schema.json",
}

# Stesse parole che un revisore noterebbe: tedesco rimasto da tag OSM in lingua.
GERMAN = re.compile(
    r"\b(der|die|das|und|ist|mit|von|für|fur|ein|eine|nicht|auf|zum|zur|den|dem|des"
    r"|bei|sich|auch|wird|werden|sind|aus|nach|über)\b", re.I)
UMLAUT = re.compile(r"[äöüß]", re.I)

RULES = {
    "dup_nome_citta": "stessa coppia nome+citta' (senza maiuscole/spazi) su piu' voci",
    "tipo_altro": "tipo \"altro\": voce non classificata",
    "descr_tipo_osm": "descrizione con \"Tipo:\" (tag OSM grezzi finiti nel testo)",
    "descr_tedesca": "descrizione (in parte) in tedesco",
    "nome_virgolette": "nome con virgolette doppie",
    "descr_oltre_200": "descrizione oltre 200 caratteri (regola di CONTRIBUTING.md)",
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def make_registry():
    resources = []
    for p in sorted(SCHEMA.glob("*.schema.json")):
        doc = load_json(p)
        resources.append((p.name, Resource.from_contents(doc)))
        resources.append((doc["$id"], Resource.from_contents(doc)))
    return Registry().with_resources(resources)


def norm(s):
    return re.sub(r"\s+", " ", str(s).casefold().strip())


# -- livello 1: schema ----------------------------------------------------

def check_schemas(registry):
    errors = []
    for fname, spec in SCHEMAS.items():
        path = DATA / fname
        if not path.exists():
            errors.append(f"{fname}: file assente")
            continue
        schema_name, mode = (spec if isinstance(spec, tuple) else (spec, "doc"))
        validator = Draft202012Validator(load_json(SCHEMA / schema_name), registry=registry)
        doc = load_json(path)
        if mode == "list":
            if not isinstance(doc, list):
                errors.append(f"{fname}: deve essere una lista JSON")
                continue
            if not doc:
                errors.append(f"{fname}: lista vuota (contratto: non vuota)")
                continue
            for i, item in enumerate(doc):
                for e in validator.iter_errors(item):
                    where = "/".join(str(x) for x in e.absolute_path)
                    errors.append(f"{fname}[{i}] id={item.get('id') if isinstance(item, dict) else '?'} "
                                  f"{where}: {e.message[:140]}")
        else:
            for e in validator.iter_errors(doc):
                where = "/".join(str(x) for x in list(e.absolute_path)[:3])
                errors.append(f"{fname} {where}: {e.message[:140]}")
    return errors


# -- livello 2: controlli incrociati --------------------------------------

def check_cross(all_data):
    errors = []
    limits = load_json(SCHEMA / "limits.json")
    lat_lo, lat_hi = limits["lat"]["min"], limits["lat"]["max"]
    lng_lo, lng_hi = limits["lng"]["min"], limits["lng"]["max"]

    ids = Counter()
    for cat in CATEGORIES:
        file_items = load_json(DATA / f"{cat}.json")
        if all_data.get(cat) != file_items:
            errors.append(f"all.json['{cat}'] non coincide con {cat}.json")
        for i, it in enumerate(file_items):
            ids[it.get("id")] += 1
            lat, lng = it.get("lat"), it.get("lng")
            if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
                       for x in (lat, lng)):
                continue  # lo segnala lo schema
            if limits.get("reject_null_island") and lat == 0 and lng == 0:
                errors.append(f"{cat}[{i}] id={it.get('id')}: GPS (0,0)")
            elif not (lat_lo <= lat <= lat_hi and lng_lo <= lng <= lng_hi):
                errors.append(f"{cat}[{i}] id={it.get('id')}: GPS fuori limiti ({lat},{lng})")
    dup = sorted(k for k, n in ids.items() if n > 1)
    if dup:
        errors.append(f"id duplicati: {dup[:10]}{' ...' if len(dup) > 10 else ''}")

    scraped = load_json(DATA / "eventi_scraped.json")
    sid = Counter(e.get("id") for e in scraped)
    sdup = sorted(k for k, n in sid.items() if n > 1)
    if sdup:
        errors.append(f"eventi_scraped.json: id duplicati {sdup[:5]}")
    return errors


# -- livello 3: qualita' --------------------------------------------------

def haversine_m(a, b):
    r = 6371000
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dphi = p2 - p1
    dl = math.radians(b["lng"] - a["lng"])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def collect_quality(all_data):
    """Ritorna (violazioni {regola: {id: categoria}}, gruppi di duplicati)."""
    viol = {r: {} for r in RULES}
    groups = defaultdict(list)
    for cat in CATEGORIES:
        for it in all_data[cat]:
            iid = it["id"]
            desc = it.get("descrizione") or ""
            groups[(norm(it.get("nome", "")), norm(it.get("citta", "")))].append((cat, it))
            if it.get("tipo") == "altro":
                viol["tipo_altro"][iid] = cat
            if re.search(r"\bTipo\s*:", desc):
                viol["descr_tipo_osm"][iid] = cat
            n = len(GERMAN.findall(desc))
            if n >= 2 or (n >= 1 and UMLAUT.search(desc)):
                viol["descr_tedesca"][iid] = cat
            if re.search(r'["“”«»]', it.get("nome", "")):
                viol["nome_virgolette"][iid] = cat
            if len(desc) > 200:
                viol["descr_oltre_200"][iid] = cat
    dup_groups = []
    for (nome, citta), members in sorted(groups.items()):
        if len(members) < 2:
            continue
        for cat, it in members:
            viol["dup_nome_citta"][it["id"]] = cat
        dists = [haversine_m(a[1], b[1]) for i, a in enumerate(members) for b in members[i + 1:]]
        dup_groups.append({
            "nome": members[0][1]["nome"],
            "citta": members[0][1]["citta"],
            "voci": sorted(({"id": it["id"], "categoria": cat, "source": it.get("source"),
                             "lat": it["lat"], "lng": it["lng"]} for cat, it in members),
                           key=lambda m: m["id"]),
            "distanza_max_m": round(max(dists)),
        })
    return viol, dup_groups


def build_reports(viol, dup_groups, all_data):
    names = {it["id"]: it["nome"] for cat in CATEGORIES for it in all_data[cat]}
    total = sum(len(all_data[c]) for c in CATEGORIES)
    quality = {
        "note": "Problemi gia' presenti, segnalati e non corretti. La CI blocca solo quelli nuovi "
                "(schema/quality-baseline.json). Rigenerato da scripts/validate_data.py --write-reports.",
        "voci_totali": total,
        "regole": {},
    }
    for rule, desc in RULES.items():
        ids = viol[rule]
        quality["regole"][rule] = {
            "descrizione": desc,
            "conteggio": len(ids),
            "per_categoria": dict(sorted(Counter(ids.values()).items())),
            "esempi": [{"id": i, "nome": names[i]} for i in sorted(ids)[:20]],
        }
    duplicates = {
        "note": "Gruppi con stesso nome e citta'. Nessuna voce e' stata rimossa o unita: decidere "
                "quale tenere e' una scelta editoriale (gli id sono parte del contratto con er0s).",
        "gruppi_totali": len(dup_groups),
        "voci_coinvolte": sum(len(g["voci"]) for g in dup_groups),
        "gruppi": dup_groups,
    }
    return {"quality.json": quality, "duplicates.json": duplicates}


def render(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def baseline_from(viol):
    return {
        "note": "Violazioni di qualita' gia' presenti (ratchet). La CI fallisce solo per id NON elencati "
                "qui. Si accorcia quando si correggono i dati; allungarla richiede una PR motivata.",
        "regole": {r: sorted(viol[r]) for r in RULES},
    }


def main():
    argv = sys.argv[1:]
    registry = make_registry()
    errors = check_schemas(registry)
    all_data = load_json(DATA / "all.json")
    if not errors:
        errors += check_cross(all_data)
    elif isinstance(all_data, dict):
        # con errori di schema i controlli incrociati possono non avere senso, ma i limiti GPS si
        # applicano comunque alle categorie ben formate
        try:
            errors += check_cross(all_data)
        except Exception as e:  # noqa: BLE001 - un dato malformato non deve nascondere l'errore di schema
            errors.append(f"controlli incrociati saltati: {type(e).__name__}")
    if errors:
        print(f"ERRORE: {len(errors)} problemi di schema/coerenza", file=sys.stderr)
        for e in errors[:MAX_SHOWN]:
            print("  -", e, file=sys.stderr)
        if len(errors) > MAX_SHOWN:
            print(f"  ... altri {len(errors) - MAX_SHOWN}", file=sys.stderr)
        return 1

    viol, dup_groups = collect_quality(all_data)
    reports = build_reports(viol, dup_groups, all_data)

    if "--write-reports" in argv:
        REPORTS.mkdir(exist_ok=True)
        for name, obj in reports.items():
            (REPORTS / name).write_text(render(obj), encoding="utf-8")
        print(f"report scritti in {REPORTS.relative_to(ROOT)}/")
    if "--update-baseline" in argv:
        BASELINE.write_text(render(baseline_from(viol)), encoding="utf-8")
        print(f"baseline riscritto: {BASELINE.relative_to(ROOT)}")
        return 0
    if "--check-reports" in argv:
        stale = [n for n, obj in reports.items()
                 if not (REPORTS / n).exists() or (REPORTS / n).read_text(encoding="utf-8") != render(obj)]
        if stale:
            print(f"ERRORE: report fuori sincrono: {stale}; lancia --write-reports", file=sys.stderr)
            return 1
        print("report aggiornati")

    if not BASELINE.exists():
        print("ERRORE: manca schema/quality-baseline.json (--update-baseline per crearlo)", file=sys.stderr)
        return 1
    base = load_json(BASELINE)["regole"]
    new, fixed = {}, {}
    for rule in RULES:
        known = set(base.get(rule, []))
        now = set(viol[rule])
        if now - known:
            new[rule] = sorted(now - known)
        if known - now:
            fixed[rule] = len(known - now)

    n_items = sum(len(all_data[c]) for c in CATEGORIES)
    print(f"schema ok su {len(SCHEMAS)} file, {n_items} voci, limiti GPS ok")
    for rule in RULES:
        print(f"  {rule}: {len(viol[rule])} esistenti (baseline {len(base.get(rule, []))})")
    if fixed:
        print(f"info: violazioni risolte rispetto al baseline {fixed}: "
              "puoi accorciarlo con --update-baseline")
    if new:
        print("ERRORE: violazioni di qualita' NUOVE (non nel baseline):", file=sys.stderr)
        for rule, ids in new.items():
            print(f"  {rule} ({RULES[rule]}): {len(ids)}", file=sys.stderr)
            for i in ids[:MAX_SHOWN]:
                print(f"    - {i}", file=sys.stderr)
        return 1
    print("nessuna violazione nuova")
    return 0


if __name__ == "__main__":
    sys.exit(main())
