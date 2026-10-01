# Contratto con i consumatori

Questo dataset non e' solo pubblicato: altri sistemi lo leggono. Questa pagina
elenca chi, cosa legge e cosa non si deve rompere. `scripts/check_er0s_contract.py`
verifica gli invarianti ed e' eseguito dalla CI.

Chi propone una modifica ai dati o agli script che li scrivono controlla prima
qui. Una modifica che viola un invariante non si unisce, anche se il resto dei
controlli e' verde.

## Consumatori

Sono tutti nel repository di prodotto ER0S (`er0s-new`), scritti in sola lettura
rispetto a questo repo.

| Consumatore | Cosa legge | Come |
|---|---|---|
| `domains/er0s-domain-salernos/src/repository.rs` (`from_json_str`) | `all.json` | Dizionario con le sei chiavi; per ogni voce `id`, `nome`, `descrizione`, `lat`, `lng`, `citta`, `source`, `link` |
| `domains/er0s-domain-salernos/src/catalog.rs` | copie vendorizzate in `data/catalog/` di `sentieri`, `monumenti`, `panorami`, `parchi`, `spiagge`, `eventi`, `sources`, `comuni_provincia` | `include_str!` a compile time; le copie si aggiornano con una PR in er0s |
| `infra/prod/systemd/salernos-sync-data.sh` | `data/eventi.json`, `data/eventi_scraped.json` | Copia in er0s con verifica md5 e conteggio > 0 |
| `infra/prod/systemd/salernos-ingest.sh` + `scripts/soliso_ingest.sh` | ramo `dati/eventi-automatici`, `data/eventi_scraped.json` | Timer systemd su soliso: ingest, push del solo ramo dati, mai `main` |

## Invarianti

### `data/all.json`

1. E' un dizionario con **esattamente** le sei chiavi `monumenti`, `parchi`,
   `spiagge`, `sentieri`, `panorami`, `eventi`. Nessuna chiave top-level nuova
   (metadati e conteggi stanno in `data/manifest.json`, un file a parte).
2. Ogni valore e' una lista di voci. Non si tolgono voci.
3. Ogni voce tiene `id`, `nome`, `descrizione`, `lat`, `lng`, `citta`, `source`,
   `link`. Nessuno di questi campi si rinomina o si toglie.
4. Un `id` esistente non cambia mai e non viene riusato per un'altra voce.
5. Un campo nuovo e' ammesso solo se **additivo** (opzionale, ignorabile da chi non
   lo conosce).
6. `all.json` e' l'unione dei sei file di categoria e li riproduce identici.

### `data/eventi.json` e `data/eventi_scraped.json`

1. Restano liste JSON **non vuote**: lo sync in er0s rifiuta una lista vuota.
2. Non si svuotano e non si spostano eventi fuori da `eventi.json`.
3. Gli eventi passati si filtrano **solo in presentazione** (`docs/calendar.html`,
   README), mai nei dati.
4. Lo scrapato non si mescola al curato: `eventi_scraped.json` resta separato.

### Script e flusso di ingest

1. `scripts/soliso_ingest.sh` resta allo stesso percorso, eseguibile, e consegna
   solo sul ramo `dati/eventi-automatici`, mai su `main`. Il comportamento non
   cambia; si ammettono solo correzioni di `shellcheck`.
2. Il runner dei workflow (`runs-on: [self-hosted, linux, obscura]`) non si cambia
   da una PR di qualita': dal 2026-09-06 le Actions ospitate da GitHub sono bloccate
   per fatturazione e un cambio potrebbe spegnere la CI.

### `data/sources.json` e `data/comuni_provincia.json`

Sono incorporati in er0s: struttura e chiavi (`fonti`, e per ogni comune `comune`,
`provincia`, `regione`, `sigla`) non cambiano senza una PR coordinata in er0s.

## Come si verifica

```bash
python3 scripts/check_er0s_contract.py
```

Esce con codice diverso da zero e dice quale invariante e' violato. Confronta
anche con `schema/contract-baseline.json` (conteggi per chiave e insieme degli
`id`): il baseline si aggiorna solo aggiungendo voci, mai togliendole.

## Cosa fa chi consuma

Chi legge questi file deve ignorare i campi che non conosce e non assumere che
`tipo` sia diverso da `altro` (oggi e' il valore piu' frequente). Lo schema
completo e' in `data/README.md`.
