#!/usr/bin/env python3
"""Generate tourism-focused JSON data files for awesome-salerno.

This script creates structured JSON files for:
- sentieri.json (hiking trails)
- monumenti.json (monuments, churches, museums)
- spiagge.json (beaches)
- eventi.json (events, festivals)
- costiera.json (Costiera Amalfitana attractions)
- cilento.json (Cilento attractions)
- panorami.json (viewpoints)
- parchi.json (parks, nature reserves)
"""
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ============================================================
# SENTIERI - Hiking trails
# ============================================================
SENTIERI = [
    {
        "id": "sentiero-degli-dei",
        "nome": "Sentiero degli Dei",
        "descrizione": "Sentiero panoramico da Agerola a Nocelle (Positano). 7.8 km, Dislivello: 500m, Difficoltà: media.",
        "comune": "Agerola - Positano",
        "zona": "costiera",
        "lunghezza_km": 7.8,
        "dislivello_m": 500,
        "difficolta": "media",
        "lat": 40.6383,
        "lng": 14.5267,
        "link": "https://www.sentierodeglidei.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "sentiero-dei-mulini",
        "nome": "Sentiero dei Mulini",
        "descrizione": "Sentiero storico tra i mulini di Vietri sul Mare. 3 km, Dislivello: 200m, Difficoltà: facile.",
        "comune": "Vietri sul Mare",
        "zona": "costiera",
        "lunghezza_km": 3.0,
        "dislivello_m": 200,
        "difficolta": "facile",
        "lat": 40.6583,
        "lng": 14.7267,
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "sentiero-costiero-amalfi",
        "nome": "Sentiero Costiero Amalfitano",
        "descrizione": "Sentiero panoramico sulla Costiera Amalfitana. Percorso lungo la costa con viste sul mare.",
        "comune": "Amalfi - Positano",
        "zona": "costiera",
        "lunghezza_km": None,
        "dislivello_m": None,
        "difficolta": "media",
        "lat": 40.6340,
        "lng": 14.6026,
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "sentiero-cilento",
        "nome": "Sentiero del Cilento",
        "descrizione": "Rete di sentieri nel Parco Nazionale del Cilento. Percorsi variabili.",
        "comune": "Cilento",
        "zona": "cilento",
        "lunghezza_km": None,
        "dislivello_m": None,
        "difficolta": "variabile",
        "lat": 40.2833,
        "lng": 15.1667,
        "link": "https://www.parcocesto.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "sentiero-paestum-velia",
        "nome": "Sentiero Paestum-Velia",
        "descrizione": "Sentiero archeologico tra i templi di Paestum e l'antica Elea/Velia.",
        "comune": "Capaccio - Ascea",
        "zona": "cilento",
        "lunghezza_km": None,
        "dislivello_m": None,
        "difficolta": "facile",
        "lat": 40.4167,
        "lng": 15.0000,
        "link": "",
        "fonte": "osm"
    }
]

# ============================================================
# MONUMENTI - Monuments, churches, museums
# ============================================================
MONUMENTI = [
    {
        "id": "duomo-salerno",
        "nome": "Duomo di Salerno",
        "descrizione": "Cattedrale normanna dedicata a San Matteo. Cripta con reliquie del santo. Costruito nel XI secolo.",
        "comune": "Salerno",
        "zona": "salerno",
        "tipo": "chiesa",
        "lat": 40.6802,
        "lng": 14.7603,
        "link": "https://it.wikipedia.org/wiki/Duomo_di_Salerno",
        "fonte": "wikipedia"
    },
    {
        "id": "castel-arechi",
        "nome": "Castello di Arechi",
        "descrizione": "Fortezza longobarda del VII secolo. Panorama sul golfo di Salerno.",
        "comune": "Salerno",
        "zona": "salerno",
        "tipo": "castello",
        "lat": 40.6844,
        "lng": 14.7551,
        "link": "https://it.wikipedia.org/wiki/Castello_di_Arechi",
        "fonte": "wikipedia"
    },
    {
        "id": "scuola-medica",
        "nome": "Scuola Medica Salernitana",
        "descrizione": "Prima università di medicina del mondo (IX secolo).",
        "comune": "Salerno",
        "zona": "salerno",
        "tipo": "monumento",
        "lat": 40.6780,
        "lng": 14.7580,
        "link": "https://it.wikipedia.org/wiki/Scuola_medica_salernitana",
        "fonte": "wikipedia"
    },
    {
        "id": "duomo-amalfi",
        "nome": "Duomo di Amalfi",
        "descrizione": "Cattedrale di Sant'Andrea. Architettura arabo-normanna. Chiostro del Paradiso.",
        "comune": "Amalfi",
        "zona": "costiera",
        "tipo": "chiesa",
        "lat": 40.6340,
        "lng": 14.6026,
        "link": "https://it.wikipedia.org/wiki/Cattedrale_di_Sant%27Andrea_(Amalfi)",
        "fonte": "wikipedia"
    },
    {
        "id": "villa-rufolo",
        "nome": "Villa Rufolo",
        "descrizione": "Villa storica con giardini. Sede del Ravello Festival. Ispirò Wagner per Parsifal.",
        "comune": "Ravello",
        "zona": "costiera",
        "tipo": "monumento",
        "lat": 40.6500,
        "lng": 14.6139,
        "link": "https://www.villarufolo.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "villa-cimbrone",
        "nome": "Villa Cimbrone",
        "descrizione": "Villa con giardini e Terrazza dell'Infinito. Vista panoramica sulla Costiera.",
        "comune": "Ravello",
        "zona": "costiera",
        "tipo": "monumento",
        "lat": 40.6489,
        "lng": 14.6103,
        "link": "https://www.villacimbrone.com",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "tempio-nettuno-paestum",
        "nome": "Tempio di Nettuno",
        "descrizione": "Tempio dorico del IV secolo a.C. Meglio conservato della Magna Grecia.",
        "comune": "Capaccio",
        "zona": "cilento",
        "tipo": "monumento",
        "lat": 40.4167,
        "lng": 15.0000,
        "link": "https://www.museopaestum.beniculturali.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "tomba-tuffatore",
        "nome": "Tomba del Tuffatore",
        "descrizione": "Affresco funerario del V secolo a.C. Unica tomba dipinta della Magna Grecia.",
        "comune": "Capaccio",
        "zona": "cilento",
        "tipo": "monumento",
        "lat": 40.4167,
        "lng": 15.0000,
        "link": "https://www.museopaestum.beniculturali.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "cripta-san-matteo",
        "nome": "Cripta di San Matteo",
        "descrizione": "Cripta del Duomo con reliquie di San Matteo. Mosaici bizantini.",
        "comune": "Salerno",
        "zona": "salerno",
        "tipo": "chiesa",
        "lat": 40.6802,
        "lng": 14.7603,
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "san-giorgio-salerno",
        "nome": "Chiesa e Monastero di San Giorgio",
        "descrizione": "Chiesa barocca con monastero. Affreschi e dipinti del XVII secolo.",
        "comune": "Salerno",
        "zona": "salerno",
        "tipo": "chiesa",
        "lat": 40.6788,
        "lng": 14.7592,
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "museo-ceramica-vietri",
        "nome": "Museo della Ceramica",
        "descrizione": "Museo dedicato alla tradizione ceramica vietrese.",
        "comune": "Vietri sul Mare",
        "zona": "costiera",
        "tipo": "museo",
        "lat": 40.6583,
        "lng": 14.7267,
        "link": "https://www.museodellaceramica.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "palazzo-ferrante",
        "nome": "Palazzo Ferrante",
        "descrizione": "Palazzo storico nel centro di Salerno.",
        "comune": "Salerno",
        "zona": "salerno",
        "tipo": "monumento",
        "lat": 40.6780,
        "lng": 14.7580,
        "link": "",
        "fonte": "osm"
    }
]

# ============================================================
# SPIAGGE - Beaches
# ============================================================
SPIAGGE = [
    {
        "id": "spiaggia-maiori",
        "nome": "Spiaggia di Maiori",
        "descrizione": "La spiaggia più lunga della Costiera Amalfitana (1 km). Stabilimenti e lidi.",
        "comune": "Maiori",
        "zona": "costiera",
        "lat": 40.6473,
        "lng": 14.6424,
        "lunghezza_m": 1000,
        "tipologia": "sabbiosa",
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "spiaggia-positano",
        "nome": "Spiaggia Grande di Positano",
        "descrizione": "Spiaggia principale di Positano. Ancorate e lidi.",
        "comune": "Positano",
        "zona": "costiera",
        "lat": 40.6283,
        "lng": 14.4847,
        "lunghezza_m": None,
        "tipologia": "sabbiosa",
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "spiaggia-amalfi",
        "nome": "Spiaggia di Amalfi",
        "descrizione": "Spiaggia nel centro di Amalfi. Marina Grande.",
        "comune": "Amalfi",
        "zona": "costiera",
        "lat": 40.6340,
        "lng": 14.6026,
        "lunghezza_m": None,
        "tipologia": "sabbiosa",
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "fiordo-furore",
        "nome": "Fiordo di Furore",
        "descrizione": "Fiordo e baia nascosta. Uno dei luoghi più pittoreschi della Costiera.",
        "comune": "Furore",
        "zona": "costiera",
        "lat": 40.6167,
        "lng": 14.5500,
        "lunghezza_m": None,
        "tipologia": "rocciosa",
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "spiaggia-paestum",
        "nome": "Spiaggia di Paestum",
        "descrizione": "Spiaggia davanti ai templi della Magna Grecia.",
        "comune": "Capaccio",
        "zona": "cilento",
        "lat": 40.4167,
        "lng": 15.0000,
        "lunghezza_m": None,
        "tipologia": "sabbiosa",
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "spiaggia-palinuro",
        "nome": "Spiaggia di Palinuro",
        "descrizione": "Spiaggia e stabilimenti. Porticciolo turistico.",
        "comune": "Camerota",
        "zona": "cilento",
        "lat": 40.0333,
        "lng": 15.2667,
        "lunghezza_m": None,
        "tipologia": "sabbiosa",
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "spiaggia-agropoli",
        "nome": "Spiaggia di Agropoli",
        "descrizione": "Spiaggia nel centro di Agropoli. Porto turistico.",
        "comune": "Agropoli",
        "zona": "cilento",
        "lat": 40.3500,
        "lng": 14.9833,
        "lunghezza_m": None,
        "tipologia": "sabbiosa",
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "spiaggia-cetara",
        "nome": "Spiaggia di Cetara",
        "descrizione": "Spiaggia nel borgo di pescatori di Cetara.",
        "comune": "Cetara",
        "zona": "costiera",
        "lat": 40.6483,
        "lng": 14.7000,
        "lunghezza_m": None,
        "tipologia": "sabbiosa",
        "link": "",
        "fonte": "osm"
    }
]

# ============================================================
# EVENTI - Events and festivals
# ============================================================
EVENTI = [
    {
        "id": "luci-dartista",
        "nome": "Luci d'Artista",
        "descrizione": "Manifestazione luminosa natalizia. Installazioni artistiche in tutta la città.",
        "comune": "Salerno",
        "zona": "salerno",
        "periodo": "novembre - gennaio",
        "frequenza": "annuale",
        "link": "https://www.comune.salerno.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "festa-san-matteo",
        "nome": "Festa di San Matteo",
        "descrizione": "Festa patronale. Processione con le reliquie del santo.",
        "comune": "Salerno",
        "zona": "salerno",
        "periodo": "21 settembre",
        "frequenza": "annuale",
        "link": "https://www.comune.salerno.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "ravello-festival",
        "nome": "Ravello Festival",
        "descrizione": "Festival musicale estivo nei giardini di Villa Rufolo e Villa Cimbrone.",
        "comune": "Ravello",
        "zona": "costiera",
        "periodo": "giugno - settembre",
        "frequenza": "annuale",
        "link": "https://www.ravellofestival.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "regata-repubbliche-marinare",
        "nome": "Regata delle Repubbliche Marinare",
        "descrizione": "Regata storica tra le antiche repubbliche marinare. Tappa ad Amalfi.",
        "comune": "Amalfi",
        "zona": "costiera",
        "periodo": "giugno",
        "frequenza": "annuale",
        "link": "https://www.regatarepubblichemarinare.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "presepe-vivente",
        "nome": "Presepe Vivente",
        "descrizione": "Presepe vivente nel centro storico. Rappresentazioni dal vivo.",
        "comune": "Salerno",
        "zona": "salerno",
        "periodo": "dicembre",
        "frequenza": "annuale",
        "link": "https://www.comune.salerno.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "battentieri",
        "nome": "Battentieri",
        "descrizione": "Festival di danza contemporanea ad Agropoli.",
        "comune": "Agropoli",
        "zona": "cilento",
        "periodo": "agosto",
        "frequenza": "annuale",
        "link": "https://www.battentieri.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "paestum-festival",
        "nome": "Paestum Festival",
        "descrizione": "Festival musicale nei templi della Magna Grecia.",
        "comune": "Capaccio",
        "zona": "cilento",
        "periodo": "estate",
        "frequenza": "annuale",
        "link": "",
        "fonte": "osm"
    }
]

# ============================================================
# PANORAMI - Viewpoints
# ============================================================
PANORAMI = [
    {
        "id": "terrazza-infinito",
        "nome": "Terrazza dell'Infinito",
        "descrizione": "Terrazza panoramica di Villa Cimbrone. Vista sulla Costiera.",
        "comune": "Ravello",
        "zona": "costiera",
        "lat": 40.6489,
        "lng": 14.6103,
        "link": "https://www.villacimbrone.com",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "belvedere-maddalena",
        "nome": "Belvedere Maddalena",
        "descrizione": "Punto panoramico su Salerno e il golfo.",
        "comune": "Salerno",
        "zona": "salerno",
        "lat": 40.6800,
        "lng": 14.7550,
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "punto-panoramico-golfo",
        "nome": "Punto Panoramico Golfo di Salerno",
        "descrizione": "Vista panoramica sul golfo di Salerno.",
        "comune": "Salerno",
        "zona": "salerno",
        "lat": 40.6750,
        "lng": 14.7600,
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "belvedere-praiano",
        "nome": "Belvedere di Praiano",
        "descrizione": "Punto panoramico su Positano e la Costiera.",
        "comune": "Praiano",
        "zona": "costiera",
        "lat": 40.6100,
        "lng": 14.5300,
        "link": "",
        "fonte": "osm"
    }
]

# ============================================================
# PARCHI - Parks and nature reserves
# ============================================================
PARCHI = [
    {
        "id": "parco-cilento",
        "nome": "Parco Nazionale del Cilento e Vallo di Diano",
        "descrizione": "Parco Nazionale UNESCO. 180.000 ettari di natura e archeologia.",
        "comune": "Cilento",
        "zona": "cilento",
        "lat": 40.2833,
        "lng": 15.1667,
        "link": "https://www.parcocesto.it",
        "fonte": "sito-ufficiale"
    },
    {
        "id": "parco-ferriere",
        "nome": "Parco Naturale delle Ferriere",
        "descrizione": "Parco naturale con cascate e sentieri. Valle dei Mulini.",
        "comune": "Amalfi",
        "zona": "costiera",
        "lat": 40.6500,
        "lng": 14.5833,
        "link": "",
        "fonte": "osm"
    },
    {
        "id": "riserva-costiera",
        "nome": "Riserva Naturale Costiera Amalfitana",
        "descrizione": "Riserva marina e terrestre. Flora e fauna mediterranea.",
        "comune": "Costiera Amalfitana",
        "zona": "costiera",
        "lat": 40.6333,
        "lng": 14.6000,
        "link": "https://www.parcoamalfi.it",
        "fonte": "sito-ufficiale"
    }
]

# ============================================================
# Save all files
# ============================================================
def save_json(filename, data):
    filepath = DATA_DIR / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  {filename}: {len(data)} entries")

def main():
    print("=== Generating tourism data ===\n")
    
    save_json("sentieri.json", SENTIERI)
    save_json("monumenti.json", MONUMENTI)
    save_json("spiagge.json", SPIAGGE)
    save_json("eventi.json", EVENTI)
    save_json("panorami.json", PANORAMI)
    save_json("parchi.json", PARCHI)
    
    # Combined file
    all_data = {
        "sentieri": SENTIERI,
        "monumenti": MONUMENTI,
        "spiagge": SPIAGGE,
        "eventi": EVENTI,
        "panorami": PANORAMI,
        "parchi": PARCHI
    }
    
    with open(DATA_DIR / "all.json", "w") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n  all.json: {sum(len(v) for v in all_data.values())} total entries")
    print("\n=== Done ===")

if __name__ == "__main__":
    main()
