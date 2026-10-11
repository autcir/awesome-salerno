# Licenze dei dati, per fonte

Il repository dichiarava tutto "CC0". Non regge: il dataset contiene dati di
terzi, e una dichiarazione CC0 del curatore non puo' rilasciare cio' che non e'
suo. Questa pagina dice, **per fonte**, quale licenza si applica secondo il
fornitore. Non e' un parere legale e non decide la licenza del dataset composto:
**quella la conferma il titolare del progetto** (vedi "Da confermare").

Il campo `source` di ogni voce dice a quale riga di questa tabella appartiene.
`data/manifest.json` riporta le stesse informazioni in forma leggibile da
macchina, con il numero di voci per fonte.

| Fonte (`source`) | Voci | Licenza del fornitore | Obblighi |
|---|---|---|---|
| OpenStreetMap (`osm`) | 5367 | Open Database License (ODbL) 1.0 | Attribuzione "© OpenStreetMap contributors"; condivisione allo stesso modo per i database derivati; mantenere aperta la copia. Vedi https://www.openstreetmap.org/copyright |
| Scritte a mano (`hand-written`) | 77 | Dei curatori del progetto | Vedi "Da confermare" |
| Curate (`curated`) | 46 | Dei curatori del progetto, su fonti pubbliche | Vedi "Da confermare" |
| Eventi dal web (`web`) | 39 | Dipende dalla fonte, registrata in `data/sources.json` | Vedi sotto |
| Eventi raccolti (`data/eventi_scraped.json`) | 44 | Per record, campo `license` | Vedi sotto |

## OpenStreetMap

Le voci con `source: osm` (coordinate, nomi, tipo, `osm_id`) vengono da
OpenStreetMap tramite l'Overpass API. I dati OSM sono sotto ODbL 1.0, non CC0.
In sintesi quello che la licenza chiede: citare OpenStreetMap e i suoi
contributori, e, se si pubblica un database derivato, rilasciarlo con la stessa
licenza (ODbL) o una compatibile. `data/all.json`, i file di categoria, il
GeoJSON, il KML/KMZ e `data/rag/chunks.jsonl` contengono o derivano da queste
voci. Se il dataset composto sia un "database derivato" nel senso dell'ODbL o
un'opera prodotta e' una valutazione che spetta al titolare.

Attribuzione da riportare a chi riusa i dati:

> Contiene dati © OpenStreetMap contributors, disponibili con licenza ODbL 1.0.

## Wikipedia e Wikidata

- **Wikipedia**: il dataset salva solo l'indirizzo della voce (campo `link`, 244
  voci puntano a `it.wikipedia.org`), non il testo. Un indirizzo non e' contenuto
  Wikipedia. Il testo di Wikipedia e' CC BY-SA 4.0: se in futuro se ne copia
  testo, valgono attribuzione e condivisione allo stesso modo.
- **Wikidata**: i dati strutturati sono CC0 1.0. Oggi non sono uniti al dataset
  (`docs/wikidata.md`); quando entreranno, restano CC0 e vanno indicati come fonte.

## Voci dei curatori (`hand-written`, `curated`)

Descrizioni e selezione scritte dai curatori del progetto, su fonti pubbliche. La
licenza con cui vengono rilasciate la decide il titolare. Il repository oggi
dichiara CC0 (`LICENSE`); er0s, che le incorpora, dichiara invece "SalernOS
editorial, CC BY 4.0" per le stesse voci (`OPEN_DATA_LICENSE` in
`domains/er0s-domain-salernos/src/catalog.rs`). Le due dichiarazioni non
coincidono: va scelta una.

## Eventi

Le voci di `eventi.json` con `source: web` e i record di
`eventi_scraped.json` vengono da pagine di enti e testate. Il registro
`data/sources.json` riporta la licenza per fonte, e ogni record raccolto la
ripete nel campo `license`. Oggi i valori sono:

- Comuni (PA italiana): "da confermare (di norma CC-BY 4.0)" o solo "da confermare";
- SalernoToday e altre testate: "da verificare", contenuti protetti.

Per le testate l'ingest registra fatti (nome, data, luogo) e il link, mai il
testo. Finche' la licenza di una fonte e' "da verificare" va trattata come non
rilasciata: non si assume CC0.

## Altri file

- `data/comuni_provincia.json`: elenco comuni, province e regioni, dichiarato
  nel README come derivato dall'elenco ISTAT. Condizioni di riuso ISTAT da
  verificare sul sito ISTAT.
- Link a siti terzi (`link`): sono indirizzi, non contenuto.
- Codice (`scripts/`, `api/`, `mcp/`, `docs/*.html`): dei curatori, sotto `LICENSE`.

## Da confermare (titolare)

1. Licenza del dataset composto: con voci OSM dentro, CC0 sull'intero non e'
   sostenibile; le opzioni sono ODbL sull'intero dataset (la piu' lineare) oppure
   separare le voci OSM da quelle dei curatori.
2. Licenza delle voci dei curatori: CC0 (qui) o CC BY 4.0 (er0s).
3. Licenza delle fonti eventi oggi "da verificare".

Fino alla conferma, chi riusa i dati deve dare per applicabili gli obblighi della
tabella per ogni fonte.
