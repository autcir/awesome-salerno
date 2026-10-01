# Dati

Punti di interesse (POI) ed eventi di Salerno, Costiera Amalfitana e Cilento.
Questa pagina descrive i file che ci sono davvero in `data/` e lo schema che le
voci hanno oggi. Il contratto con i consumatori esterni e' in `docs/CONTRACT.md`,
le licenze per fonte in `DATA-LICENSES.md`.

## File

Fonte primaria (modificata a mano o dagli script di ingest/merge):

| File | Contenuto | Voci |
|---|---|---|
| `sentieri.json` | Sentieri e percorsi | 1658 |
| `monumenti.json` | Chiese, castelli, musei, grotte, fonti, luci d'artista... | 3479 |
| `spiagge.json` | Spiagge | 78 |
| `panorami.json` | Punti panoramici | 253 |
| `parchi.json` | Parchi e aree naturali | 12 |
| `eventi.json` | Eventi curati (feste patronali, sagre, festival) | 49 |
| `eventi_scraped.json` | Eventi raccolti da `scripts/ingest_events.py`, `curated: false`, mai mescolati a `eventi.json` | 44 |
| `sources.json` | Registro delle fonti degli eventi, con stato misurato | 14 fonti |
| `comuni_provincia.json` | Comune -> provincia, sigla, regione (elenco ISTAT) | 102 |
| `broken_links.json` | Esito dell'ultimo controllo dei link | - |

Derivati dai file sopra (non si modificano a mano; per `events.xml` e `voice-assistant.json` vedi la colonna):

| File | Generato da | Contenuto |
|---|---|---|
| `all.json` | `scripts/export_data.py` | Dizionario con le 6 chiavi `sentieri`, `monumenti`, `spiagge`, `eventi`, `panorami`, `parchi` (5529 voci in tutto) |
| `awesome-salerno.geojson` | `scripts/export_data.py` | FeatureCollection di soli `Point` |
| `awesome-salerno.kml`, `.kmz` | `api/kml_export.py` | Una cartella per categoria |
| `events.xml` | nessuno script nel repo (da `eventi.json`, oggi non rigenerato) | Feed RSS dei 49 eventi curati |
| `rag/chunks.jsonl` | `scripts/build_rag.py` | Un chunk per voce, per il retrieval |
| `voice-assistant.json` | a mano | Definizione degli intent per assistenti vocali; i conteggi in `data_summary` sono vecchi (5547 POI contro i 5529 reali) |

`all.json` e' l'unione dei sei file di categoria e deve coincidere con essi.
`docs/data/` e' la copia pubblicata sul sito: si rigenera da qui, non si modifica.

## Schema delle voci

Ogni voce dei sei file di categoria e' un oggetto JSON. Lo schema formale
(JSON Schema 2020-12) e' in `schema/`; `scripts/validate_data.py` lo applica.

Campi presenti su ogni voce:

| Campo | Tipo | Note |
|---|---|---|
| `id` | stringa | Univoco in tutto il dataset, stabile: non si cambia mai |
| `nome` | stringa | |
| `descrizione` | stringa | |
| `lat`, `lng` | numero | WGS84, gradi decimali; vedi "Limiti GPS" |
| `citta` | stringa | Comune |
| `zona` | stringa | `salerno`, `costiera` o `cilento` |
| `tipo` | stringa | Vedi CONTRIBUTING.md |
| `source` | stringa | `osm`, `hand-written`, `curated` o `web` |
| `link` | stringa (URL) | Fonte ufficiale, Wikipedia, oppure link OpenStreetMap generato dalle coordinate |
| `last_verified` | data `AAAA-MM-GG` | Ultima volta che una richiesta HTTP vera al link esterno e' riuscita. Mai impostata per i link generati dalle coordinate e mai spostata da un fallimento (vedi sotto) |
| `provincia`, `sigla_provincia`, `regione` | stringa | Dall'elenco ISTAT dei comuni |
| `in_ambito` | booleano | `false` = fuori da Salerno/Costiera/Cilento: segnalato, non rimosso |

Campi opzionali:

| Campo | Dove | Note |
|---|---|---|
| `quartiere` | Salerno citta' | |
| `osm_id`, `osm_type` | voci OSM | `node`, `way` o `relation` |
| `link_rotto` | dopo un link check con `--fix` | URL originale sostituito dal link OSM |
| `last_checked`, `last_status` | dopo un link check | Data dell'ultima richiesta vera e suo esito (`200`, `404`, `timeout`, `dns`, `tls`, ...), qualunque esso sia |
| `link_type` | dopo un link check | `osm_generated` = link OSM costruito da lat/lng (non si richiede e non si timbra), `external` = link esterno |
| `link_rotto_checked`, `link_rotto_status` | voci con `link_rotto` | Riesame dell'URL originale: se risponde di nuovo compare in `data/broken_links.json` (`alive_again`) |
| `difficolta`, `dislivello_m`, `lunghezza_km`, `periodo`, `frequenza` | sentieri, alcune voci di monumenti/panorami/parchi | Spesso stringa vuota o `null` |
| `artista` | luci d'artista | |
| `data_inizio`, `data_fine` | eventi, luci d'artista | `AAAA-MM-GG` |
| `edizione`, `anno_inizio`, `ricorrenza`, `luoghi` | eventi | `ricorrenza` oggi vale sempre `annuale` |

I campi nuovi sono sempre additivi: nessun campo esistente si rinomina o si
toglie (vedi `docs/CONTRACT.md`).

### Eventi raccolti (`eventi_scraped.json`)

Ogni record porta `id`, `nome`, `link`, `data_inizio`, `data_fine`, `tipo`
(`evento`), `curated` (`false`), `source` (oggetto con `id`, `name`, `url`,
`type`), `license`, `retrieved_at`, `provenance`, `visto_prima_volta`,
`visto_ultima_volta` e, quando la fonte e' ufficiale, `ufficiale` e `data_via`.
Gli eventi non riconfermati per oltre 21 giorni escono da soli.

## Limiti GPS

Fonte unica, leggibile da macchina: `schema/limits.json`. Sono i limiti che la
CI applica:

- latitudine tra **39 e 42**, longitudine tra **14 e 16**;
- la coppia (0, 0) e' sempre un errore.

Sono larghi di proposito: il dataset contiene anche voci in provincia di
Napoli, Cosenza, Avellino, Latina e Potenza, marcate `in_ambito: false`. Il
perimetro editoriale (cosa e' Salerno, Costiera, Cilento) non si decide con un
rettangolo ma con `provincia` e `in_ambito`.

## Fonti e licenze

`source` dice da dove viene la voce:

- `osm` - OpenStreetMap, estratto con l'Overpass API;
- `hand-written` - scritta a mano dai curatori;
- `curated` - verificata a mano su una fonte pubblica;
- `web` - evento raccolto dal web (vedi `sources.json` per la fonte e la licenza).

Le licenze non sono uniformi: dati OSM, Wikipedia e Wikidata hanno ciascuno la
propria. L'elenco per fonte e' in `DATA-LICENSES.md`; `data/manifest.json`
riporta gli stessi dati in forma leggibile da macchina insieme agli hash dei file.

## Problemi noti

Il report dei problemi di qualita' gia' presenti (duplicati nome+citta', tipo
`altro`, descrizioni generiche o in tedesco, nomi con virgolette) sta in
`data/reports/`. Non vengono corretti qui: sono segnalati, e la CI blocca solo
quelli nuovi.
