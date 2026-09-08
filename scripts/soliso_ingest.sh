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

# La PR la aprirebbe .github/workflows/pr-ingest.yml al push su questo ramo,
# con il GITHUB_TOKEN di Actions e nessun token su questa VPS. Ma dal
# 2026-09-06 ogni run e' bloccato a monte: "The job was not started because
# your account is locked due to a billing issue". Finche' dura, il ramo e'
# la consegna e la PR si apre a mano.
echo "consegnati ${N} eventi sul ramo ${RAMO}"
echo "PR: https://github.com/autcir/awesome-salerno/compare/${RAMO}?expand=1"
