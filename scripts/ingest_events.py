#!/usr/bin/env python3
"""
Ingest eventi del Salernitano: obscura -> record normalizzati con provenance.

Le fonti stanno in data/sources.json (semaforo misurato, non dedotto).
Lo scrapato NON tocca mai i curated: esce in data/eventi_scraped.json con
`curated: false`. Lezione INCIDENTE DATI 2026-09-06.

Uso:
    python3 scripts/ingest_events.py              # ingest reale
    python3 scripts/ingest_events.py --self-check # verifica i parser, zero rete
"""
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
OBSCURA = os.environ.get("ER0S_OBSCURA_COMMAND", "obscura")

MESI = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5,
    "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10,
    "novembre": 11, "dicembre": 12,
}


def obscura_eval(url, js, timeout=90):
    """Una pagina, un estrattore JS. Vuoto non e' successo: alza, non tace."""
    try:
        r = subprocess.run(
            [OBSCURA, "fetch", url, "--quiet", "--stealth", "--eval", js],
            capture_output=True, text=True, timeout=timeout,
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"binary '{OBSCURA}' non trovato; installa obscura o imposta "
            f"ER0S_OBSCURA_COMMAND=<percorso>"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"E_TIMEOUT: {url} oltre {timeout}s")
    if r.returncode != 0:
        raise RuntimeError(f"E_FETCH: {url}: {r.stderr.strip()[:200]}")
    out = r.stdout.strip()
    if not out:
        raise RuntimeError(f"E_EMPTY: {url} ha risposto senza contenuto")
    return json.loads(out)


def date_da_slug(slug):
    """
    '...-sagra-uva-11-12-13-14-settembre-2026' -> ('2026-09-11', '2026-09-14').
    Le date di SalernoToday stanno nello slug: niente schema.org/Event.
    """
    m = re.search(r"((?:\d{1,2}-)+)(" + "|".join(MESI) + r")-(\d{4})", slug)
    if not m:
        return None, None
    giorni = [int(g) for g in m.group(1).strip("-").split("-") if g.isdigit()]
    giorni = [g for g in giorni if 1 <= g <= 31]
    if not giorni:
        return None, None
    mese, anno = MESI[m.group(2)], int(m.group(3))
    try:
        inizio = date(anno, mese, min(giorni)).isoformat()
        fine = date(anno, mese, max(giorni)).isoformat()
    except ValueError:
        return None, None
    return inizio, fine


def slugify(testo):
    s = re.sub(r"[^a-z0-9]+", "-", testo.lower()).strip("-")
    return s[:60] or "evento"


def record(nome, link, inizio, fine, fonte, extra=None):
    """Ogni record porta la sua provenienza. Senza fonte non si scrive."""
    r = {
        "id": f"{fonte['id']}-{slugify(nome)}",
        "nome": nome.strip(),
        "link": link,
        "data_inizio": inizio,
        "data_fine": fine,
        "tipo": "evento",
        "curated": False,
        "source": {
            "name": fonte["nome"],
            "url": fonte["url"],
            "type": fonte["tipo"],
            "id": fonte["id"],
        },
        "license": fonte.get("licenza", "da verificare"),
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provenance": f"obscura fetch --stealth su {fonte['url']}",
    }
    if extra:
        r.update(extra)
    return r


JS_LINK_EVENTI = r"""
(function(){
  // Lo stesso evento compare piu' volte (titolo, immagine, "leggi tutto").
  // Si raggruppa per href tenendo il testo piu' lungo: filtrare sulla
  // lunghezza prima di raggruppare perdeva gli eventi linkati solo da una
  // foto (misurato 2026-09-08: "Pooh 60 - La nostra storia" spariva).
  var m = {};
  var links = document.querySelectorAll('a');
  for (var i = 0; i < links.length; i++) {
    var a = links[i];
    if (!/\/eventi\/[a-z0-9-]+\/[a-z0-9-]+\.html$/.test(a.href)) continue;
    var t = (a.textContent || '').trim().replace(/\s+/g, ' ');
    if (!m[a.href] || t.length > m[a.href].length) m[a.href] = t;
  }
  var out = [];
  for (var h in m) if (m[h].length > 8) out.push({href: h, t: m[h]});
  return JSON.stringify(out);
})()
"""

JS_RSS = r"""
JSON.stringify([...document.querySelectorAll('item')].slice(0, 40).map(function(i){
  var g = function(n){ var e = i.querySelector(n); return e ? e.textContent.trim() : null; };
  return {t: g('title'), d: g('pubDate'), l: g('link') || g('guid')};
}))
"""

# Solo eventi: un feed di cronaca non e' un calendario.
PAROLE_EVENTO = re.compile(
    r"sagra|festival|concerto|mostra|rassegna|fiera|spettacolo|festa|"
    r"processione|premio|torneo|degustazione|presentazione|stagione",
    re.I,
)
# Misurati come falsi positivi: "Rassegna stampa" contiene "rassegna" ma e'
# cronaca quotidiana, non un evento.
NON_EVENTO = re.compile(r"rassegna stampa|prime pagine|necrolog|meteo|oroscopo", re.I)


def da_salernotoday(fonte, giorni=30):
    """
    Il sito espone un calendario per data: /eventi/dal/<da>/al/<a>/.
    Interrogandolo giorno per giorno la data non va indovinata dallo slug —
    la conosce l'URL che chiediamo noi. Lo slug resta come conferma quando
    c'e' (eventi su piu' giorni).
    """
    base = fonte["url"].rstrip("/")
    oggi = date.today()
    out, visti = [], {}

    for n in range(giorni):
        giorno = date.fromordinal(oggi.toordinal() + n)
        u = f"{base}/dal/{giorno.isoformat()}/al/{giorno.isoformat()}/"
        try:
            hits = obscura_eval(u, JS_LINK_EVENTI)
        except RuntimeError as e:
            print(f"    ({giorno}: saltato — {e})")
            continue
        for h in hits:
            href, titolo = h["href"], h["t"]
            # lo slug vince se porta un intervallo: e' piu' preciso del giorno
            s_ini, s_fin = date_da_slug(href)
            ini = s_ini or giorno.isoformat()
            fin = s_fin or giorno.isoformat()
            if href in visti:
                # gia' visto in un altro giorno: allarga la finestra
                r = visti[href]
                r["data_inizio"] = min(r["data_inizio"], ini)
                r["data_fine"] = max(r["data_fine"], fin)
                continue
            r = record(titolo, href, ini, fin, fonte)
            visti[href] = r
            out.append(r)
    return out


def da_rss(fonte):
    items = obscura_eval(fonte["url"], JS_RSS)
    out = []
    for i in items:
        titolo = i.get("t") or ""
        if not PAROLE_EVENTO.search(titolo) or NON_EVENTO.search(titolo):
            continue
        giorno = None
        if i.get("d"):
            try:
                giorno = datetime.strptime(
                    i["d"][:25].strip(), "%a, %d %b %Y %H:%M:%S"
                ).date().isoformat()
            except ValueError:
                pass
        out.append(record(titolo, i.get("l") or fonte["url"], giorno, giorno, fonte))
    return out


def _iso(stamp):
    return f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}" if stamp else None


def fine_attendibile(fine_iso, adesso=None):
    """
    Misurato 2026-09-08: per gli eventi senza fine il sito del Comune mette
    come fine *l'ora di render della pagina* (Teatrando chiudeva a oggi,
    Limen invece aveva una fine vera). Una fine che cade oggi non e' una
    fine: e' un timestamp. Si scarta, non si pubblica.
    """
    if not fine_iso:
        return None
    oggi = (adesso or date.today()).isoformat()
    return None if fine_iso >= oggi else fine_iso


JS_PA_INDEX = r"""
(function(){
  // Ogni comune ha il suo schema di URL (/eventi/<id>/<slug>,
  // /it/eventi/<slug>, /vivere-il-comune/eventi/<slug>...). Quel che hanno
  // in comune e' la forma: dall'indice pendono i dettagli, tutti con
  // "event" nel percorso e piu' profondi dell'indice stesso.
  var host = location.host, base = location.pathname.replace(/\/+$/, '');
  var m = {};
  var links = document.querySelectorAll('a');
  for (var i = 0; i < links.length; i++) {
    var a = links[i];
    if (a.host !== host) continue;
    var p = a.pathname.replace(/\/+$/, '');
    if (!/event/i.test(p)) continue;
    if (p === base || p.length <= base.length) continue;
    // le pagine di categoria non sono eventi
    if (/\/tipi?[-_]di[-_]evento\/|\/tipi?[_-]evento\//i.test(p)) continue;
    var t = (a.textContent || '').trim().replace(/\s+/g, ' ');
    if (/^categoria\s*:/i.test(t)) continue;
    if (!m[a.href] || t.length > m[a.href].length) m[a.href] = t;
  }
  var o = [];
  for (var k in m) if (m[k].length > 10) o.push({href: k, t: m[k]});
  return JSON.stringify(o);
})()
"""

JS_PA_DATE = r"""
(function(){
  // In ordine di affidabilita': il link "Aggiungi al calendario" (Google
  // Calendar, misurato su Salerno e Agropoli), poi <time datetime>
  // (Ravello). Il testo libero NON si usa: "15/05/2025" su Praiano puo'
  // essere la data dell'evento o quella di pubblicazione, e indovinare
  // significa inventare.
  var links = document.querySelectorAll('a');
  for (var i = 0; i < links.length; i++) {
    var h = links[i].href || '';
    var g = h.match(/[?&]dates=(\d{8})T?\d*Z?\/(\d{8})T?\d*Z?/);
    if (g) return JSON.stringify({inizio: g[1], fine: g[2], via: 'calendario'});
  }
  var ts = document.querySelectorAll('time[datetime]');
  if (ts.length) {
    var a = ts[0].getAttribute('datetime').slice(0, 10).replace(/-/g, '');
    var b = ts.length > 1 ? ts[ts.length - 1].getAttribute('datetime').slice(0, 10).replace(/-/g, '') : a;
    if (/^\d{8}$/.test(a)) return JSON.stringify({inizio: a, fine: /^\d{8}$/.test(b) ? b : a, via: 'time'});
  }
  return JSON.stringify({inizio: null, fine: null, via: null});
})()
"""


def da_pa(fonte, max_eventi=30):
    """
    Estrattore per i siti della PA. Il comune porta i suoi indici nel
    registro (`indici`); lo schema degli URL cambia da comune a comune, la
    forma no. Senza una data leggibile a macchina l'evento si scarta.
    """
    visti = {}
    for u in fonte.get("indici", [fonte["url"]]):
        try:
            for h in obscura_eval(u, JS_PA_INDEX):
                visti.setdefault(h["href"], h["t"])
        except RuntimeError as e:
            print(f"    (indice saltato {u.rsplit('/', 1)[-1]}: {e})")

    out = []
    for href, titolo in list(visti.items())[:max_eventi]:
        try:
            d = obscura_eval(href, JS_PA_DATE)
        except RuntimeError as e:
            print(f"    ({href.rsplit('/', 1)[-1][:40]}: {e})")
            continue
        inizio = _iso(d.get("inizio"))
        if not inizio:
            continue
        fine = fine_attendibile(_iso(d.get("fine"))) or inizio
        out.append(record(titolo, href, inizio, max(fine, inizio), fonte,
                          {"tipo": "evento", "ufficiale": fonte["tipo"] == "official",
                           "data_via": d.get("via")}))
    return out


ESTRATTORI = {
    "salernotoday-eventi": da_salernotoday,
    "salernonotizie-rss": da_rss,
}


GIORNI_SCADENZA = 21


def riconferma(nuovi, precedenti, oggi=None, giorni=GIORNI_SCADENZA):
    """
    t5 — un evento non riconfermato scade, ma non sparisce subito.

    Le fonti PA tolgono e rimettono le pagine, e una fonte giu' per un
    giorno non deve cancellare mezzo calendario. Quindi: chi torna
    nell'ingest di oggi si riconferma; chi non torna resta, con
    `visto_ultima_volta`, finche' non supera la finestra. Gli eventi gia'
    finiti restano nell'archivio ma non si riconfermano da soli.
    """
    from datetime import date as _d, timedelta
    oggi = oggi or _d.today()
    limite = (oggi - timedelta(days=giorni)).isoformat()
    oggi_s = oggi.isoformat()

    per_id = {}
    for e in precedenti:
        per_id[e.get("id")] = e

    vivi, scaduti = [], 0
    visti_ora = set()
    for e in nuovi:
        e["visto_ultima_volta"] = oggi_s
        prima = per_id.get(e["id"])
        if prima and prima.get("visto_prima_volta"):
            e["visto_prima_volta"] = prima["visto_prima_volta"]
        else:
            e["visto_prima_volta"] = oggi_s
        visti_ora.add(e["id"])
        vivi.append(e)

    for e in precedenti:
        if e.get("id") in visti_ora:
            continue
        ultimo = e.get("visto_ultima_volta", "")
        if ultimo and ultimo >= limite:
            vivi.append(e)          # non riconfermato, ma dentro la finestra
        else:
            scaduti += 1            # fuori finestra: esce
    return vivi, scaduti


def dedup(nuovi, curati):
    """
    I curated vincono sempre. `ricorrenza: annuale` (San Matteo, Luci
    d'Artista) tornerebbe ogni anno: si confronta il nome normalizzato.
    """
    noti = {slugify(c.get("nome", "")) for c in curati}
    fuori, dentro = [], set()
    for r in nuovi:
        chiave = slugify(r["nome"])
        if chiave in noti or chiave in dentro:
            continue
        dentro.add(chiave)
        fuori.append(r)
    return fuori


def self_check():
    assert date_da_slug("sagra-uva-san-cipriano-filetta-11-12-13-14-settembre-2026.html") == (
        "2026-09-11", "2026-09-14"), "slug multi-giorno"
    assert date_da_slug("concerto-4-ottobre-2026.html") == ("2026-10-04", "2026-10-04")
    assert date_da_slug("pagina-senza-data.html") == (None, None)
    assert date_da_slug("evento-99-settembre-2026.html") == (None, None), "giorno impossibile"
    assert date_da_slug("evento-30-febbraio-2026.html") == (None, None), "data inesistente"

    fonte = {"id": "f", "nome": "F", "url": "https://e.it", "tipo": "external"}
    r = record("Sagra Test", "https://e.it/x", "2026-09-11", "2026-09-14", fonte)
    assert r["curated"] is False and r["source"]["url"] == "https://e.it"
    assert r["retrieved_at"] and r["provenance"]

    curati = [{"nome": "Festa di San Matteo", "ricorrenza": "annuale"}]
    doppi = [record("Festa di San Matteo", "u", None, None, fonte),
             record("Sagra Nuova", "u", None, None, fonte),
             record("Sagra Nuova", "u2", None, None, fonte)]
    assert len(dedup(doppi, curati)) == 1, "dedup: ricorrente + doppione interno"

    # fine = oggi significa "il sito ha stampato l'ora di render", non una fine
    assert fine_attendibile("2026-06-27", date(2026, 9, 8)) == "2026-06-27"
    assert fine_attendibile("2026-09-08", date(2026, 9, 8)) is None
    assert fine_attendibile(None, date(2026, 9, 8)) is None
    assert _iso("20260801T190000Z") == "2026-08-01" and _iso(None) is None

    from datetime import date as _d
    oggi = _d(2026, 9, 8)
    fonte2 = {"id": "f", "nome": "F", "url": "https://e.it", "tipo": "external"}
    a = record("A", "u", "2026-10-01", "2026-10-01", fonte2)
    prima = [dict(a, visto_ultima_volta="2026-09-07", visto_prima_volta="2026-08-01"),
             {"id": "vecchio", "nome": "V", "visto_ultima_volta": "2026-08-01"},
             {"id": "recente", "nome": "R", "visto_ultima_volta": "2026-09-01"}]
    vivi, scaduti = riconferma([a], prima, oggi=oggi)
    ids = {e["id"] for e in vivi}
    assert a["id"] in ids, "riconfermato oggi"
    assert "recente" in ids, "non riconfermato ma dentro i 21 giorni: resta"
    assert "vecchio" not in ids and scaduti == 1, "fuori finestra: esce"
    rec = next(e for e in vivi if e["id"] == a["id"])
    assert rec["visto_prima_volta"] == "2026-08-01", "la prima volta non si riscrive"
    assert rec["visto_ultima_volta"] == "2026-09-08"

    assert PAROLE_EVENTO.search("Torna la Sagra del Vino")
    assert not PAROLE_EVENTO.search("Lavori hub Pompei, modifiche circolazione")
    # falso positivo misurato il 2026-09-08: "rassegna" dentro "rassegna stampa"
    assert NON_EVENTO.search("Rassegna stampa di lunedi 7 settembre 2026")
    assert NON_EVENTO.search("Le prime pagine dei giornali salernitani")
    assert not NON_EVENTO.search("Rassegna teatrale di Velia")
    print("self-check: tutto verde")


def main():
    if "--self-check" in sys.argv:
        return self_check()

    fonti = json.load(open(DATA / "sources.json"))["fonti"]
    curati = json.load(open(DATA / "eventi.json"))
    raccolti, esiti = [], []

    for f in fonti:
        fn = ESTRATTORI.get(f["id"]) or (da_pa if f.get("indici") else None)
        if not fn or f["semaforo"] in ("rosso", "arancio"):
            continue
        try:
            trovati = fn(f)
            raccolti += trovati
            esiti.append(f"  {f['id']}: {len(trovati)} eventi")
        except Exception as e:  # una fonte giu' non ferma le altre
            esiti.append(f"  {f['id']}: FALLITA — {e}")

    finali = dedup(raccolti, curati)
    precedenti = []
    if (DATA / "eventi_scraped.json").exists():
        precedenti = json.load(open(DATA / "eventi_scraped.json"))
    finali, scaduti = riconferma(finali, precedenti)
    print("\n".join(esiti))
    print(f"raccolti {len(raccolti)} -> {len(finali)} vivi, {scaduti} scaduti "
          f"(non riconfermati da oltre {GIORNI_SCADENZA} giorni)")

    if not finali:
        print("ZERO eventi: non sovrascrivo. Vuoto non e' un successo.")
        return 1

    out = DATA / "eventi_scraped.json"
    json.dump(finali, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"scritto {out}")

    # Lo stesso contenuto dove lo cerca plugin-salernos-events (from_disk).
    # Gli alias serde del plugin mappano nome/data_inizio/citta/tipo, quindi
    # non serve un secondo formato: serve solo il file al posto giusto.
    plugin_out = DATA / "events.json"
    json.dump(finali, open(plugin_out, "w"), ensure_ascii=False, indent=2)
    print(f"scritto {plugin_out} (per plugin-salernos-events)")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
