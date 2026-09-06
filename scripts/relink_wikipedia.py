#!/usr/bin/env python3
"""Propose a Wikipedia (IT) link for every POI that fell back to OpenStreetMap.

A dead official site is a worse source than a live encyclopaedia entry, and
Wikipedia has an article for most of these monuments. A name match alone is
not enough - "Tempio di Apollo" also names a temple in Syracuse - so a
candidate is only accepted when the article's own coordinates land near the
POI. Articles without coordinates need the titles to match both ways.

    python3 scripts/relink_wikipedia.py           # print proposals
    python3 scripts/relink_wikipedia.py --apply   # write them into data/
"""
import json
import math
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]
API = "https://it.wikipedia.org/w/api.php"
UA = "awesome-salerno-relink/1.0 (+https://github.com/autcir/awesome-salerno)"
# only articles and prepositions: dropping "tempio" or "casa" would let
# "Tempio di Apollo" match the bare article "Apollo"
STOP = {"di", "del", "della", "dello", "dei", "degli", "delle", "da", "dal",
        "d", "il", "lo", "la", "i", "gli", "le", "e", "ed", "a", "al", "allo",
        "alla", "ai", "agli", "alle", "in", "nel", "nella", "su", "sul", "con"}


def norm(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", text)) - STOP


MAX_KM = 30  # a nearby article is the same monument; a far one is a namesake


def haversine_km(lat1, lng1, lat2, lng2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def api(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception:
        return None


def coords(title):
    """(lat, lng) of the article, or None if it carries no coordinates."""
    res = api({"action": "query", "prop": "coordinates", "titles": title})
    if not res:
        return None
    for page in res.get("query", {}).get("pages", {}).values():
        for c in page.get("coordinates", []):
            return c["lat"], c["lon"]
    return None


def search(name, lat=None, lng=None):
    """Best Wikipedia IT article for a POI, or None if nothing is convincing."""
    query = re.sub(r"\s*\([^)]*\)", "", name).strip()  # drop "(VII.9.1)" etc.
    res = api({"action": "query", "list": "search", "srsearch": query,
               "srlimit": 5})
    if not res:
        return None
    hits = res["query"]["search"]

    wanted = norm(query)
    if not wanted:
        return None
    for hit in hits:
        title = hit["title"]
        got = norm(title)
        # every significant word of the POI name must appear in the article title
        if not wanted <= got:
            continue
        where = coords(title) if lat and lng else None
        if where:
            if haversine_km(lat, lng, *where) <= MAX_KM:
                return title
            continue  # same name, wrong place
        if got <= wanted:  # no coordinates: demand a two-way title match
            return title
    return None


def main():
    apply = "--apply" in sys.argv
    data = {c: json.loads((DATA / f"{c}.json").read_text()) for c in CATEGORIES}
    # events are skipped: names like "Musica & Parole" match unrelated articles
    todo = [(c, it) for c in CATEGORIES if c != "eventi"
            for it in data[c] if it.get("link_rotto")]
    print(f"{len(todo)} POI sul fallback OSM, cerco su Wikipedia IT\n")

    with ThreadPoolExecutor(max_workers=8) as pool:
        titles = list(pool.map(
            lambda p: search(p[1]["nome"], p[1].get("lat"), p[1].get("lng")), todo))

    found = 0
    for (cat, it), title in zip(todo, titles):
        if not title:
            continue
        link = "https://it.wikipedia.org/wiki/" + urllib.parse.quote(
            title.replace(" ", "_"))
        print(f"{it['nome']}\n  -> {title}")
        found += 1
        if apply:
            it["link"] = link
            it["last_verified"] = date.today().isoformat()

    print(f"\n{found}/{len(todo)} risolti"
          + (" e scritti" if apply else " (dry run, usa --apply)"))
    if apply:
        for cat in CATEGORIES:
            (DATA / f"{cat}.json").write_text(
                json.dumps(data[cat], ensure_ascii=False, indent=2) + "\n")
        (DATA / "all.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def demo():
    assert norm("Casa di Sallustio (VI.2.4)") == {"casa", "sallustio", "vi", "2", "4"}
    assert search("Duomo di Amalfi", 40.634, 14.603) == "Duomo di Amalfi"
    assert search("Castello di Arechi", 40.687, 14.762) == "Castello di Arechi"
    assert search("qwertyuiop asdfghjkl zxcvbnm") is None
    # right name, wrong province: the Syracuse temple must be rejected
    assert search("Tempio di Apollo", 40.749, 14.484) is None
    assert coords("Duomo di Amalfi") is not None
    print("ok")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()
