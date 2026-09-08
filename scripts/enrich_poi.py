#!/usr/bin/env python3
"""
Perfezionamento POI: provincia, ambito, quartiere, descrizioni.
Copre p1-p4 di perfezionamento.md. Tutto offline, zero rete.

    python3 scripts/enrich_poi.py --self-check   # verifica la logica
    python3 scripts/enrich_poi.py                # riscrive i data/*.json

Non cancella nulla: marca. Se 1.773 POI sono fuori ambito, lo dicono loro
stessi con un campo, e la decisione di potarli resta umana.
"""
import json
import sys
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
FILES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]

# L'ambito dichiarato: Salerno, Costiera Amalfitana, Cilento.
# La Costiera sconfina in provincia di Napoli (Agerola) e il Cilento
# arriva a Maratea: l'ambito e' territoriale, non amministrativo.
FUORI_PROVINCIA_IN_AMBITO = {"Agerola", "Maratea"}

# Quartieri di Salerno citta' (p2). Riquadri larghi ma disgiunti: un POI
# fuori da tutti resta senza quartiere, che e' meglio di un quartiere finto.
QUARTIERI_SALERNO = [
    ("Centro Storico", 40.6740, 40.6830, 14.7480, 14.7620),
    ("Lungomare",      40.6700, 40.6790, 14.7480, 14.7700),
    ("Carmine",        40.6720, 40.6800, 14.7620, 14.7720),
    ("Mercato",        40.6690, 40.6780, 14.7720, 14.7900),
    ("Pastena",        40.6620, 40.6720, 14.7900, 14.8100),
    ("Mariconda",      40.6580, 40.6680, 14.8100, 14.8300),
    ("Fuorni",         40.6450, 40.6600, 14.8300, 14.8700),
    ("Torrione",       40.6740, 40.6820, 14.7900, 14.8050),
    ("Fratte",         40.6900, 40.7050, 14.7550, 14.7800),
    ("Ogliara",        40.7000, 40.7200, 14.7200, 14.7550),
    ("Arechi",         40.6650, 40.6740, 14.8050, 14.8250),
]

# p3: le descrizioni generate da tag OSM, riscritte in italiano leggibile.
TIPI = {
    "archaeological_site": "sito archeologico",
    "ruins": "area di ruderi",
    "castle": "castello",
    "church": "chiesa",
    "chapel": "cappella",
    "monastery": "monastero",
    "museum": "museo",
    "memorial": "monumento commemorativo",
    "tower": "torre",
    "city_gate": "porta cittadina",
    "aqueduct": "acquedotto",
    "bridge": "ponte storico",
}
CULTI = {
    "roman_catholic": "cattolico di rito romano",
    "catholic": "cattolico",
    "christian": "cristiano",
    "evangelical": "evangelico",
    "orthodox": "ortodosso",
}


def quartiere_di(lat, lng):
    for nome, la0, la1, ln0, ln1 in QUARTIERI_SALERNO:
        if la0 <= lat <= la1 and ln0 <= lng <= ln1:
            return nome
    return None


def descrizione_generica(testo):
    """Riconosce i dump di tag OSM, non le descrizioni scritte da qualcuno."""
    t = (testo or "").strip()
    return (not t) or t.startswith("Tipo: ") or t.startswith("Religione: ") \
        or t.startswith("Punto di interesse nel territorio")


def riscrivi(item):
    """
    Descrizione specifica dai campi che gia' esistono. Non inventa nulla:
    se non c'e' materiale, torna None e la vecchia resta.
    """
    nome = (item.get("nome") or "").strip()
    citta = (item.get("citta") or "").strip()
    quart = (item.get("quartiere") or "").strip()
    vecchia = (item.get("descrizione") or "").strip()

    dove = f"a {citta}" if citta else ""
    if quart and citta:
        dove = f"nel quartiere {quart} di {citta}"

    cosa = None
    if vecchia.startswith("Tipo: "):
        cosa = TIPI.get(vecchia[6:].strip())
    elif vecchia.startswith("Religione: "):
        culto = None
        for k, v in CULTI.items():
            if k in vecchia.lower():
                culto = v
                break
        tipo = TIPI.get((item.get("tipo") or "").strip())
        if culto:
            # "luogo di culto" + "di culto X" faceva "luogo di culto di culto X"
            cosa = f"{tipo} di culto {culto}" if tipo else f"luogo di culto {culto}"
        else:
            cosa = tipo or "luogo di culto"
    else:
        cosa = TIPI.get((item.get("tipo") or "").strip())

    if not cosa or not nome:
        return None
    testo = f"{nome}: {cosa}"
    if dove:
        testo += f" {dove}"
    return testo + "."


def arricchisci(items, comuni):
    st = {"provincia": 0, "fuori_ambito": 0, "quartiere": 0, "descrizione": 0,
          "fuorni_corretti": 0}
    for i in items:
        # Fuorni non e' un comune: e' un quartiere di Salerno.
        if (i.get("citta") or "").strip() == "Fuorni":
            i["citta"] = "Salerno"
            i["quartiere"] = "Fuorni"
            st["fuorni_corretti"] += 1

        citta = (i.get("citta") or "").strip()
        c = comuni.get(citta)
        if c:
            i["provincia"] = c["provincia"]
            i["sigla_provincia"] = c["sigla"]
            i["regione"] = c["regione"]
            st["provincia"] += 1
            dentro = c["sigla"] == "SA" or citta in FUORI_PROVINCIA_IN_AMBITO
            i["in_ambito"] = dentro
            if not dentro:
                st["fuori_ambito"] += 1

        if citta == "Salerno" and i.get("lat") and i.get("lng") and not i.get("quartiere"):
            q = quartiere_di(i["lat"], i["lng"])
            if q:
                i["quartiere"] = q
                st["quartiere"] += 1

        if descrizione_generica(i.get("descrizione")):
            nuova = riscrivi(i)
            if nuova:
                i["descrizione"] = nuova
                st["descrizione"] += 1
    return st


def self_check():
    assert quartiere_di(40.6790, 14.7550) == "Centro Storico"
    assert quartiere_di(40.6500, 14.8500) == "Fuorni"
    assert quartiere_di(41.9, 12.5) is None, "Roma non e' un quartiere di Salerno"

    assert descrizione_generica("Tipo: archaeological_site")
    assert descrizione_generica("Religione: christian. Denominazione: catholic")
    assert descrizione_generica("")
    assert not descrizione_generica("Chiesa romanica del XII secolo con portale in tufo")

    a = {"nome": "Villa Comunale", "citta": "Salerno", "quartiere": "Centro Storico",
         "descrizione": "Tipo: archaeological_site", "tipo": "archaeological_site"}
    assert riscrivi(a) == "Villa Comunale: sito archeologico nel quartiere Centro Storico di Salerno."
    b = {"nome": "San Pietro", "citta": "Amalfi", "tipo": "church",
         "descrizione": "Religione: christian. Denominazione: roman_catholic"}
    assert riscrivi(b) == "San Pietro: chiesa di culto cattolico di rito romano a Amalfi."
    # senza un tipo noto non si ripete "di culto": era "luogo di culto di culto X"
    c = {"nome": "Santuario", "citta": "Piaggine", "tipo": "",
         "descrizione": "Religione: christian. Denominazione: catholic"}
    assert riscrivi(c) == "Santuario: luogo di culto cattolico a Piaggine.", riscrivi(c)
    # senza materiale non si inventa
    assert riscrivi({"nome": "X", "citta": "Y", "descrizione": "Tipo: bohboh"}) is None

    comuni = {"Salerno": {"provincia": "Salerno", "sigla": "SA", "regione": "Campania"},
              "Pompei": {"provincia": "Napoli", "sigla": "NA", "regione": "Campania"},
              "Agerola": {"provincia": "Napoli", "sigla": "NA", "regione": "Campania"}}
    it = [{"citta": "Fuorni", "lat": 40.65, "lng": 14.85, "nome": "N", "descrizione": ""},
          {"citta": "Pompei", "nome": "P", "descrizione": "x"},
          {"citta": "Agerola", "nome": "A", "descrizione": "x"}]
    st = arricchisci(it, comuni)
    assert it[0]["citta"] == "Salerno" and it[0]["quartiere"] == "Fuorni"
    assert it[1]["in_ambito"] is False, "Pompei e' fuori ambito"
    assert it[2]["in_ambito"] is True, "Agerola e' Costiera, dentro l'ambito"
    assert st["fuorni_corretti"] == 1 and st["fuori_ambito"] == 1
    print("self-check: tutto verde")


def main():
    if "--self-check" in sys.argv:
        return self_check()
    comuni = json.load(open(DATA / "comuni_provincia.json"))
    totale = {"provincia": 0, "fuori_ambito": 0, "quartiere": 0, "descrizione": 0,
              "fuorni_corretti": 0}
    for f in FILES:
        p = DATA / f"{f}.json"
        items = json.load(open(p))
        st = arricchisci(items, comuni)
        json.dump(items, open(p, "w"), ensure_ascii=False, indent=2)
        for k in totale:
            totale[k] += st[k]
        print(f"  {f}.json: {len(items)} POI")
    print(f"\nprovincia assegnata : {totale['provincia']}")
    print(f"fuori ambito marcati: {totale['fuori_ambito']}")
    print(f"quartieri assegnati : {totale['quartiere']}")
    print(f"descrizioni riscritte: {totale['descrizione']}")
    print(f"Fuorni corretti     : {totale['fuorni_corretti']}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
