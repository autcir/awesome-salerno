#!/bin/bash
# Ingest giornaliero su soliso: obscura sta qui, non sui runner GitHub.
# Consegna su un ramo dedicato, MAI su main: il diff lo guarda un umano.
set -euo pipefail
cd "$HOME/awesome-salerno"
RAMO="dati/eventi-automatici"

git fetch -q origin
git checkout -q main
git reset -q --hard origin/main

python3 scripts/ingest_events.py || { echo "ingest fallito: nulla da consegnare"; exit 1; }

# git diff non vede i file non tracciati: al primo giro il file non esiste
# ancora su main e "nessuna novita" era una bugia. status --porcelain li vede.
if [ -z "$(git status --porcelain -- data/eventi_scraped.json)" ]; then
  echo "nessuna novita negli eventi"
  exit 0
fi

N=$(python3 -c 'import json; print(len(json.load(open("data/eventi_scraped.json"))))')

git checkout -q -B "$RAMO"
git add data/eventi_scraped.json
git commit -q -m "dati: ingest eventi $(date +%F) — ${N} eventi

Generato da scripts/ingest_events.py su soliso.
Ogni record porta source, license, retrieved_at, provenance e curated:false."
git push -q -f origin "$RAMO"

# t6 — una PR vera, non solo un ramo: il diff si guarda e si discute li'.
# gh non c'e' su questa macchina e non serve: bastano l API e un token con
# il solo permesso sulle pull request, letto da un file a 600.
TOKEN_FILE="$HOME/.config/awesome-salerno/github_token"
if [ ! -r "$TOKEN_FILE" ]; then
  echo "ramo ${RAMO} aggiornato con ${N} eventi; PR non aperta (manca $TOKEN_FILE)"
  exit 0
fi
TOKEN=$(cat "$TOKEN_FILE")
API="https://api.github.com/repos/autcir/awesome-salerno/pulls"

# se una PR aperta da questo ramo esiste gia, il push l ha appena aggiornata
APERTE=$(curl -sS -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "${API}?state=open&head=autcir:${RAMO}" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')

if [ "$APERTE" != "0" ]; then
  echo "consegnati ${N} eventi: PR gia aperta, aggiornata dal push"
  exit 0
fi

CORPO="Ingest automatico del $(date +%F) da soliso: ${N} eventi.

Ogni record porta source, license, retrieved_at, provenance e curated:false.
Gli eventi non riconfermati per oltre 21 giorni escono da soli.

Generato da scripts/ingest_events.py. Il diff va guardato prima di unire."

python3 - "$TOKEN" "$RAMO" "$N" "$CORPO" <<PYEOF
import json, sys, urllib.request
token, ramo, n, corpo = sys.argv[1:5]
req = urllib.request.Request(
    "https://api.github.com/repos/autcir/awesome-salerno/pulls",
    data=json.dumps({"title": f"dati: ingest eventi {n} eventi",
                     "head": ramo, "base": "main", "body": corpo}).encode(),
    headers={"Authorization": f"Bearer {token}",
             "Accept": "application/vnd.github+json",
             "Content-Type": "application/json"},
    method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("PR aperta:", json.load(r)["html_url"])
except Exception as e:
    print("PR non aperta:", e)
    sys.exit(0)
PYEOF
echo "consegnati ${N} eventi sul ramo ${RAMO}"
