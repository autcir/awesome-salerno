#!/usr/bin/env python3
"""Verifica gli invarianti del contratto con er0s (docs/CONTRACT.md).

Controlla, in sola lettura:
  - all.json: dizionario con ESATTAMENTE le sei chiavi, liste di voci, ogni voce con
    id/nome/descrizione/lat/lng/citta/source/link del tipo che repository.rs si aspetta;
  - nessuna voce tolta e nessun id cambiato rispetto a schema/contract-baseline.json
    (si aggiungono voci, non se ne tolgono);
  - eventi.json e eventi_scraped.json: liste JSON non vuote (lo sync in er0s rifiuta le vuote);
  - sources.json e comuni_provincia.json: struttura che er0s incorpora;
  - scripts/soliso_ingest.sh: presente, eseguibile, consegna solo su dati/eventi-automatici;
  - workflow: `runs-on` resta il runner self-hosted.

Uso:
    python3 scripts/check_er0s_contract.py
    python3 scripts/check_er0s_contract.py --update-baseline   # solo per AGGIUNGERE voci

Non richiede dipendenze oltre alla libreria standard.
"""
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASELINE = ROOT / "schema" / "contract-baseline.json"
CATEGORIES = ["monumenti", "parchi", "spiagge", "sentieri", "panorami", "eventi"]
STR_FIELDS = ["id", "nome", "descrizione", "citta", "source"]
RUNS_ON = "[self-hosted, linux, obscura]"
INGEST_BRANCH = "dati/eventi-automatici"
MAX_SHOWN = 15


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def check_all_json(all_data):
    errors = []
    if not isinstance(all_data, dict):
        return ["all.json non e' un dizionario"]
    keys = set(all_data)
    if keys != set(CATEGORIES):
        errors.append(f"all.json: chiavi top-level {sorted(keys)} != {sorted(CATEGORIES)} "
                      f"(mancanti {sorted(set(CATEGORIES) - keys)}, in piu' {sorted(keys - set(CATEGORIES))})")
    for cat in CATEGORIES:
        items = all_data.get(cat)
        if not isinstance(items, list):
            errors.append(f"all.json['{cat}'] non e' una lista")
            continue
        for i, it in enumerate(items):
            where = f"{cat}[{i}]"
            if not isinstance(it, dict):
                errors.append(f"{where}: voce non e' un oggetto")
                continue
            for f in STR_FIELDS:
                if not isinstance(it.get(f), str):
                    errors.append(f"{where} id={it.get('id')}: '{f}' assente o non stringa "
                                  "(repository.rs usa un valore di ripiego, il catalogo no)")
            for f in ("lat", "lng"):
                if not is_number(it.get(f)):
                    errors.append(f"{where} id={it.get('id')}: '{f}' assente o non numerico")
            if "link" not in it or not (it["link"] is None or isinstance(it["link"], str)):
                errors.append(f"{where} id={it.get('id')}: 'link' deve esistere ed essere stringa o null")
    return errors


def check_baseline(all_data):
    """Nessuna voce tolta: ogni id del baseline e' ancora nella sua categoria."""
    if not BASELINE.exists():
        return ["manca schema/contract-baseline.json (--update-baseline per crearlo)"]
    base = load(BASELINE)
    errors = []
    for cat in CATEGORIES:
        known = base["ids"].get(cat, [])
        now = {it.get("id") for it in all_data.get(cat, []) if isinstance(it, dict)}
        gone = [i for i in known if i not in now]
        if gone:
            errors.append(f"all.json['{cat}']: {len(gone)} voci tolte o con id cambiato rispetto al "
                          f"baseline, es. {gone[:5]}")
        if len(now) < base["counts"].get(cat, 0):
            errors.append(f"all.json['{cat}']: {len(now)} voci < {base['counts'][cat]} del baseline")
    return errors


def check_event_lists():
    errors = []
    for name in ("eventi.json", "eventi_scraped.json"):
        path = DATA / name
        if not path.exists():
            errors.append(f"{name}: assente")
            continue
        doc = load(path)
        if not isinstance(doc, list) or not doc:
            errors.append(f"{name}: deve essere una lista JSON non vuota (sync er0s: count>0)")
    return errors


def check_embedded():
    errors = []
    sources = load(DATA / "sources.json")
    if not isinstance(sources, dict) or not isinstance(sources.get("fonti"), list):
        errors.append("sources.json: manca la lista 'fonti'")
    comuni = load(DATA / "comuni_provincia.json")
    if not isinstance(comuni, dict) or not comuni:
        errors.append("comuni_provincia.json: deve essere un dizionario non vuoto")
    else:
        for name, rec in comuni.items():
            if not isinstance(rec, dict) or not all(isinstance(rec.get(k), str)
                                                    for k in ("comune", "provincia", "regione", "sigla")):
                errors.append(f"comuni_provincia.json['{name}']: servono comune/provincia/regione/sigla")
                break
    return errors


def check_ingest_script():
    errors = []
    path = ROOT / "scripts" / "soliso_ingest.sh"
    if not path.exists():
        return ["scripts/soliso_ingest.sh: assente (lo usa infra/prod/systemd/salernos-ingest.sh)"]
    if not os.access(path, os.X_OK):
        errors.append("scripts/soliso_ingest.sh: non eseguibile")
    text = path.read_text(encoding="utf-8")
    if INGEST_BRANCH not in text:
        errors.append(f"scripts/soliso_ingest.sh: non cita il ramo {INGEST_BRANCH}")
    if re.search(r"git\s+push[^\n]*\bmain\b", text):
        errors.append("scripts/soliso_ingest.sh: un push su main e' vietato")
    return errors


def check_runner():
    errors = []
    for wf in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        for n, line in enumerate(wf.read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if s.startswith("runs-on:") and RUNS_ON not in s:
                errors.append(f"{wf.name}:{n}: runs-on diverso da {RUNS_ON} "
                              "(le Actions ospitate da GitHub sono bloccate per fatturazione)")
    return errors


def main():
    all_data = load(DATA / "all.json")

    if "--update-baseline" in sys.argv:
        if BASELINE.exists():
            old = load(BASELINE)
            for cat in CATEGORIES:
                now = {it["id"] for it in all_data[cat]}
                gone = [i for i in old["ids"].get(cat, []) if i not in now]
                if gone:
                    print(f"ERRORE: il baseline si aggiorna solo aggiungendo voci; "
                          f"{cat} ne ha perse {len(gone)}", file=sys.stderr)
                    return 1
        new = {
            "note": "Insieme degli id che er0s puo' referenziare. Si allunga quando si aggiungono voci, "
                    "non si accorcia mai (docs/CONTRACT.md).",
            "counts": {cat: len(all_data[cat]) for cat in CATEGORIES},
            "ids": {cat: sorted(it["id"] for it in all_data[cat]) for cat in CATEGORIES},
        }
        BASELINE.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"baseline scritto: {BASELINE.relative_to(ROOT)}")
        return 0

    errors = check_all_json(all_data)
    if not errors:
        errors += check_baseline(all_data)
    errors += check_event_lists() + check_embedded() + check_ingest_script() + check_runner()
    if errors:
        print(f"ERRORE: {len(errors)} invarianti del contratto er0s violati", file=sys.stderr)
        for e in errors[:MAX_SHOWN]:
            print("  -", e, file=sys.stderr)
        if len(errors) > MAX_SHOWN:
            print(f"  ... altri {len(errors) - MAX_SHOWN}", file=sys.stderr)
        return 1
    counts = ", ".join(f"{c}={len(all_data[c])}" for c in CATEGORIES)
    print(f"contratto er0s ok ({counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
