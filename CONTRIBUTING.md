# Contributing to Awesome Salerno

Grazie per il tuo interesse nel contribuire a questa lista! Le contribuzioni sono fondamentali per mantenere questa risorsa aggiornata e utile.

## Come aggiungere un POI

1. **Fork** questo repository
2. **Crea un branch** per la tua modifica: `git checkout -b add-mio-poi`
3. **Aggiungi il POI** nel file JSON corretto nella cartella `data/`
4. **Segui lo schema JSON** esatto (vedi sotto)
5. **Apri un PR** con il titolo descrittivo: `Add: Nome del POI`

## Schema JSON

Ogni POI deve seguire questo formato:

```json
{
  "id": "custom-nome-poi",
  "nome": "Nome del POI",
  "descrizione": "Breve descrizione di una riga (max 200 caratteri)",
  "lat": 40.6892,
  "lng": 14.7681,
  "zona": "salerno | costiera | cilento",
  "citta": "Nome del comune",
  "quartiere": "Solo per Salerno (opzionale)",
  "tipo": "chiesa | castello | museo | archeologico | grotta | fonte | sentiero | panorama | spiaggia | piazza | monumento | torre | ponte | porta | scala | altro",
  "source": "curated | osm | wikipedia",
  "link": "https://..."
}
```

### Campi obbligatori

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `id` | string | ID univoco. Formato: `custom-nome-poi` per contributi manuali, `osm-{id}` per OSM |
| `nome` | string | Nome ufficiale del POI |
| `descrizione` | string | Descrizione concisa (max 200 caratteri) |
| `lat` | float | Latitudine GPS (range: 39.85 - 40.85) |
| `lng` | float | Longitudine GPS (range: 14.3 - 15.6) |
| `zona` | string | Una tra: `salerno`, `costiera`, `cilento` |
| `citta` | string | Nome del comune (es. "Salerno", "Amalfi", "Capaccio Paestum") |
| `tipo` | string | Categoria del POI (vedi lista sopra) |
| `source` | string | Origine dei dati: `curated`, `osm`, `wikipedia` |

### Campi opzionali

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `quartiere` | string | Quartiere di Salerno (es. "Centro Storico", "Pastena", "Mercato", "Fratte", "Fuorni") |
| `link` | string | URL ufficiale o Wikipedia |
| `osm_id` | int | ID OpenStreetMap (se source=osm) |
| `osm_type` | string | Tipo OSM: `way`, `node`, o `relation` |
| `difficolta` | string | Per sentieri: `facile`, `medio`, `difficile`, `molto_difficile` |
| `dislivello` | int | Dislivello in metri (per sentieri) |
| `lunghezza_km` | float | Lunghezza in km (per sentieri) |

## File JSON

I dati sono organizzati per categoria nella cartella `data/`:

| File | Contenuto | Esempio |
|------|-----------|---------|
| `sentieri.json` | Sentieri e percorsi | Sentiero degli Dei |
| `monumenti.json` | Chiese, castelli, musei | Duomo di Salerno |
| `spiagge.json` | Spiagge e lidi | Spiaggia Grande |
| `panorami.json` | Punti panoramici | Belvedere di Ravello |
| `parchi.json` | Parchi naturali | Parco del Cilento |
| `eventi.json` | Eventi e manifestazioni | Ravello Festival |

## Regole per le entry

- **GPS obbligatorio.** Ogni POI deve avere coordinate GPS valide.
- **Descrizione concisa.** Una riga, max 200 caratteri, senza punteggiatura finale.
- **Zona corretta.** Classifica nella zona giusta:
  - `salerno`: città di Salerno e dintorni (lat > 40.55, lng < 14.85)
  - `costiera`: Costiera Amalfitana (lat > 40.45, lng < 15.10)
  - `cilento`: tutto il resto
- **Link verificati.** Solo link funzionanti a fonti ufficiali o Wikipedia.
- **Niente duplicati.** Controlla che il POI non sia già presente.
- **Niente spam.** Non aggiungere attività commerciali, servizi a pagamento, o link promozionali.

## Classificazione `tipo`

| Tipo | Descrizione | Esempi |
|------|-------------|--------|
| `chiesa` | Chiese, cattedrali, santuari | Duomo di Salerno |
| `castello` | Castelli, fortezze, rocche | Castello di Arechi |
| `museo` | Musei, gallerie, mostre | Museo della Carta |
| `archeologico` | Siti archeologici, templi | Tempio di Nettuno |
| `grotta` | Grotte, caverne | Grotta di Castelcivita |
| `fonte` | Fontane, sorgenti, acquedotti | Fontana dei Quattro Cancelli |
| `sentiero` | Sentieri, cammini, percorsi | Sentiero degli Dei |
| `panorama` | Punti panoramici, belvedere | Terrazza dell'Infinito |
| `spiaggia` | Spiagge, lidi, cala | Spiaggia Grande |
| `piazza` | Piazze, larghi, chiostri | Piazza Flavio Gioia |
| `monumento` | Monumenti, statue, colonne | Statua di规范 |
| `torre` | Torri, faraglioni | Torre Normanna |
| `ponte` | Ponti, viadotti | Ponte dei Patizzi |
| `porta` | Porte, mura, cittadelle | Porta della Persona |
| `scala` | Scale, scalinate, gradinate | Scalinata di Via Cannuta |
| `altro` | Altro | Non categorizzato |

## Verifica automatica

Ogni PR viene verificato automaticamente:

1. **awesome-lint** - Controlla il formato della README
2. **JSON validation** - Verifica che tutti i JSON siano validi
3. **GPS bounds check** - Controlla che le coordinate siano nel range corretto
4. **Link check** - Verifica che i link siano funzionanti

## Issue

Se vuoi segnalare un link morto, un errore, o suggerire una nuova sezione, apri un [Issue](https://github.com/autcir/awesome-salerno/issues).

## Code of Conduct

Sii rispettoso, costruttivo e inclusivo. Non tolleriamo spam, hate speech, o comportamenti tossici.

## License

Contribuendo a questo progetto, accetti che i tuoi contributi siano rilasciati sotto la [CC0 1.0 Universal](LICENSE) license.
