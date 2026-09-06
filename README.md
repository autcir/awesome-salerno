<div align="center">

# 🌊 Awesome Salerno

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

**La raccolta completa di dati turistici per Salerno, Costiera Amalfitana e Cilento.**

3615 POI con coordinate GPS — sentieri, monumenti, spiagge, panorami, parchi, eventi.

[Scarica i dati](#download) · [Usa l'API](#api) · [Contribuisci](#contributing)

</div>

---

## Perché

Google non ha una struttura dati pulita per il turismo campano.
Questi dati sono **liberi, aperti e verificati** — pronti per app, siti web e assistenti vocali.

Ogni POI ha:
- Coordinate GPS reali
- Link a fonti ufficiali (Wikipedia, CAI, siti ufficiali)
- Descrizione accurata

---

## 🥾 Sentieri — 318

| Sentiero | Difficoltà | Zona |
|----------|------------|------|
| [Sentiero degli Dei](https://www.caimontilattari.it/sentiero/327/) | Media | Costiera |
| [Path of the Lemons](https://www.alltrails.com/trail/italy/campania/sentiero-dei-limoni) | Facile | Costiera |
| [Valle dei Mulini](https://www.caimontilattari.it/sentiero/325/) | Media | Amalfi |
| [Alta Via Monti Lattari](https://www.altaviadeimontilattari.it/) | Difficile | Lattari |
| [Cammino di San Nilo](https://www.italiadeicammini.it/) | Difficile | Cilento |
| [Costa degli Infreschi](https://www.komoot.com/it-it/smarttour/e1084969073/) | Media | Cilento |
| [Sentiero della Primula](https://www.sentieridelcilento.it/sentierodellaprimula/) | Media | Palinuro |
| [Sentiero del Monte Stella](https://www.cilentolifestyle.it/) | Media | Cilento |

📁 [`data/sentieri.json`](data/sentieri.json)

---

## 🏛️ Monumenti — 2600

| Monumento | Tipo | Zona |
|-----------|------|------|
| [Duomo di Salerno](https://it.wikipedia.org/wiki/Duomo_di_Salerno) | Chiesa | Salerno |
| [Castello di Arechi](https://it.wikipedia.org/wiki/Castello_di_Arechi) | Castello | Salerno |
| [Scuola Medica Salernitana](https://it.wikipedia.org/wiki/Scuola_medica_salernitana) | Monumento | Salerno |
| [Duomo di Amalfi](https://it.wikipedia.org/wiki/Cattedrale_di_Sant%27Andrea_(Amalfi)) | Chiesa | Amalfi |
| [Villa Rufolo](https://www.villarufolo.it) | Monumento | Ravello |
| [Villa Cimbrone](https://www.villacimbrone.com) | Monumento | Ravello |
| [Tempio di Nettuno](https://www.museopaestum.beniculturali.it) | Archeologico | Paestum |
| [Tomba del Tuffatore](https://www.museopaestum.beniculturali.it) | Archeologico | Paestum |
| [Grotta di Castelcivita](https://www.grottedicastelcivita.it) | Grotta | Cilento |

📁 [`data/monumenti.json`](data/monumenti.json)

---

## 🏖️ Spiagge — 126

| Spiaggia | Zona |
|----------|------|
| [Spiaggia Grande](https://www.openstreetmap.org/#map=16/40.6278/14.4872) | Positano |
| [Fiordo di Furore](https://www.openstreetmap.org/#map=16/40.6143/14.5546) | Furore |
| [Spiaggia di Maiori](https://www.openstreetmap.org/#map=16/40.6472/14.6422) | Maiori |
| [Spiaggia di Paestum](https://www.openstreetmap.org/#map=16/40.4180/15.0070) | Capaccio |
| [Spiaggia di Palinuro](https://www.openstreetmap.org/#map=16/40.0360/15.2881) | Centola |
| [Trentova](https://www.openstreetmap.org/#map=16/40.3436/14.9723) | Agropoli |
| [Cala degli Infreschi](https://www.openstreetmap.org/#map=16/40.0330/15.3780) | Camerota |

📁 [`data/spiagge.json`](data/spiagge.json)

---

## 🗺️ Panorami — 544

| Panorama | Zona |
|----------|------|
| [Monte Centaurino](https://www.openstreetmap.org/?mlat=40.2144&mlon=15.4711) | Cilento |
| [Monte Cervati](https://www.openstreetmap.org/?mlat=40.2849&mlon=15.4836) | Cilento |
| [Monte Finestra](https://www.openstreetmap.org/?mlat=40.6889&mlon=14.6714) | Lattari |
| [Terrazza dell'Infinito](https://www.villacimbrone.com) | Ravello |

📁 [`data/panorami.json`](data/panorami.json)

---

## 🌿 Parchi — 19

| Parco | Zona |
|-------|------|
| [Parco Nazionale del Cilento](https://www.parcocesto.it) | Cilento |
| [Parco delle Ferriere](https://www.parcoamalfi.it) | Costiera |
| [Riserva Costiera Amalfitana](https://www.parcoamalfi.it) | Costiera |
| [Area Marina Infreschi](https://www.parcocesto.it) | Cilento |

📁 [`data/parchi.json`](data/parchi.json)

---

## 🎉 Eventi — 8

| Evento | Quando | Link |
|--------|--------|------|
| [Ravello Festival](https://www.ravellofestival.it) | Giu — Set | Sito |
| [Paestum Festival](https://www.paestumfestival.it) | Lug — Ago | Sito |
| [Festa di San Matteo](https://www.comune.salerno.it) | 19-21 Set | Comune |
| [Festa di Sant'Andrea](https://www.comune.amalfi.it) | 27-30 Nov | Comune |
| [Sagra del Pesce](https://www.sagradelpescecetara.it) | Agosto | Sito |
| [Festa della Ceramica](https://www.festadellaceramica.it) | Settembre | Sito |
| [Battentieri](https://www.battentieri.it) | Agosto | Sito |
| [Regata Repubbliche Marinare](https://www.regatarepubblichemarinare.it) | Giugno | Sito |

📁 [`data/eventi.json`](data/eventi.json)

---

## Download

Tutti i dati in formato JSON:

| File | Entries |
|------|---------|
| [`data/sentieri.json`](data/sentieri.json) | 318 |
| [`data/monumenti.json`](data/monumenti.json) | 2600 |
| [`data/spiagge.json`](data/spiagge.json) | 126 |
| [`data/panorami.json`](data/panorami.json) | 544 |
| [`data/parchi.json`](data/parchi.json) | 19 |
| [`data/eventi.json`](data/eventi.json) | 8 |
| [`data/all.json`](data/all.json) | **3615** |

---

## API

```bash
python3 api/server.py
```

```
GET /api/sentieri      → 318 sentieri
GET /api/monumenti     → 2600 monumenti
GET /api/spiagge       → 126 spiagge
GET /api/panorami      → 544 panorami
GET /api/parchi        → 19 parchi
GET /api/eventi        → 8 eventi
GET /api/all           → 3615 POI
GET /api/search?q=...  → ricerca full-text
GET /api/health        → status
```

---

## Contributing

[Invia una PR](CONTRIBUTING.md) — solo dati verificabili, GPS obbligatorio, link a fonti ufficiali.

---

## License

[![CC0](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/)
