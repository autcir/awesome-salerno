# Changelog

Formato basato su [Keep a Changelog](https://keepachangelog.com/it-IT/1.1.0/).
Il dataset non ha rilasci numerati: le modifiche stanno sotto "Non rilasciato"
finche' il titolare non decide una versione. Il contenuto dei dati (voci e
eventi) non cambia in nessuna delle voci sotto: `all.json`, `eventi.json` e
`eventi_scraped.json` conservano lo stesso sha256 del baseline.

## [Non rilasciato]

### Aggiunto

- `schema/` con JSON Schema 2020-12 per voci ed eventi e `scripts/validate_data.py`
  che lo applica a tutti i `data/*.json`; i problemi che i dati hanno gia'
  (duplicati nome+citta', tipo "altro", tag "Tipo:", tedesco, virgolette nei
  nomi) stanno in un baseline: la CI fallisce solo per violazioni nuove.
  `data/reports/` li rende leggibili. (26c7d57)
- `scripts/check_er0s_contract.py`: porta in Python la logica del consumatore
  `er0s-domain-salernos` e verifica gli invarianti di `docs/CONTRACT.md`
  (sei chiavi in `all.json`, campi delle voci, liste eventi non vuote,
  `scripts/soliso_ingest.sh` eseguibile). (26c7d57)
- `docs/CONTRACT.md`: chi legge i dati e cosa non si deve rompere. (9b42f16)
- `DATA-LICENSES.md` e `data/manifest.json` (conteggi, sha256 e licenze per
  fonte; riproducibile, senza orologio) con `scripts/build_manifest.py`. (2995d99)
- Campi additivi nei link check: `last_checked`, `last_status`,
  `link_type: osm_generated`. (1419ad3)
- `.github/dependabot.yml` per github-actions, pip e npm con cooldown di 7 giorni;
  `.github/actionlint.yaml` e `.github/zizmor.yml` per i controlli sui workflow.
- `SECURITY.md`, questo `CHANGELOG.md`, `.python-version`, `.node-version` e
  `engines` in `package.json`.

### Modificato

- La licenza dei dati non e' piu' dichiarata CC0 uniforme: i dati OpenStreetMap
  sono ODbL, Wikipedia e Wikidata hanno condizioni proprie; la licenza del
  dataset composto resta una decisione del titolare. (2995d99)
- README dei dati descrive i file e i campi reali (non piu' `mangiare`, `luoghi`,
  `dormire`, `all-pois`); i limiti GPS stanno in `schema/limits.json` e le doc
  lo citano. (9b42f16)
- `scripts/export_data.py` e' l'unica fonte per `all.json`, GeoJSON e `docs/data/`
  (`--docs` sincronizza, `--check` non scrive e segnala il drift); sostituisce lo
  script inline di `auto-refresh.yml` e la copia manuale di `deploy-pages`.
  (cc75ceb)
- `docs/data/`, GeoJSON e manifest rigenerati da `data/` (una tantum): il GeoJSON
  era indietro su `last_verified` e quattro link e `docs/data/` mancava di cinque
  file. (8134d34)
- `scripts/verify_links.py`: `last_verified` si muove solo se una richiesta vera al
  link esterno riesce; HEAD poi GET, User-Agent dichiarato, timeout, retry con
  backoff, un secondo tentativo prima di dire "rotto", un accesso al secondo per
  host; 401/403/429/999 sono "blocked". (1419ad3)
- Workflow CI: action fissate a SHA di 40 caratteri con commento di versione,
  `permissions` minimi per job, `persist-credentials: false` dove non si spinge,
  `concurrency`, `timeout-minutes`, `npm ci --ignore-scripts`; `ci.yml` esegue
  `validate_data.py`, `check_er0s_contract.py` e il controllo di drift;
  `link-check.yml` controlla il contratto prima di committare. `runs-on` e'
  invariato (runner self-hosted `obscura`). (580afb6)
- `.gitignore`: ambienti virtuali, cache, log, backup `*.bak-*` e file `.env`.

### Corretto

- `last_verified` veniva scritto per i 5004 link OpenStreetMap senza alcuna
  richiesta; la documentazione diceva che il workflow non applica `--fix` ma lo
  applica. (1419ad3)
- `auto-refresh.yml` perdeva `provincia`, `sigla_provincia` e `in_ambito` dalle
  proprieta' del GeoJSON e scriveva senza newline finale. (cc75ceb)
- `README.md` linkava tre volte `DATA-LICENSES.md` e `awesome-lint` falliva con
  `double-link`. (d53ccaa)
