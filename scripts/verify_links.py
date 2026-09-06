#!/usr/bin/env python3
"""Verify external links and stamp `last_verified` on each POI.

OSM links are generated from coordinates and always resolve, so they are
stamped without a network call. Everything else gets a HEAD (GET fallback).
Broken links land in data/broken_links.json for the weekly workflow to report.

Usage: python3 scripts/verify_links.py [--stale-days N]
"""
import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]
UA = "awesome-salerno-linkcheck/1.0 (+https://github.com/autcir/awesome-salerno)"
TIMEOUT = 15
TODAY = date.today().isoformat()


def encode(url):
    """Percent-encode the non-ASCII parts; http.client only speaks latin-1."""
    u = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((
        u.scheme, u.netloc.encode("idna").decode("ascii"),
        urllib.parse.quote(u.path), urllib.parse.quote(u.query, safe="=&"),
        urllib.parse.quote(u.fragment)))


def check(url):
    """Return None if the URL is reachable, else a short error string."""
    err = "unchecked"
    try:
        url = encode(url)
    except Exception as e:
        return f"invalid URL ({type(e).__name__})"
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                if r.status < 400:
                    return None
                err = f"HTTP {r.status}"
        except urllib.error.HTTPError as e:
            if e.code in (403, 405, 501) and method == "HEAD":
                continue  # some servers reject HEAD, retry with GET
            err = f"HTTP {e.code}"
        except Exception as e:  # timeout, DNS, TLS, redirect loop
            err = type(e).__name__
        if method == "GET":
            return err
    return err


def main():
    stale_days = 30
    if "--stale-days" in sys.argv:
        stale_days = int(sys.argv[sys.argv.index("--stale-days") + 1])
    cutoff = (date.today() - timedelta(days=stale_days)).isoformat()

    data = {c: json.loads((DATA / f"{c}.json").read_text()) for c in CATEGORIES}

    todo = {}  # url -> items sharing it
    for items in data.values():
        for it in items:
            url = it.get("link", "")
            if not url:
                continue
            if "openstreetmap.org" in url:
                it["last_verified"] = TODAY  # derived from coordinates, no fetch
            elif it.get("last_verified", "") < cutoff:
                todo.setdefault(url, []).append(it)

    print(f"checking {len(todo)} external links (stale before {cutoff})")
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(check, todo))

    broken = []
    for (url, items), err in zip(todo.items(), results):
        if err:
            broken.append({"url": url, "error": err,
                           "pois": [i.get("id") for i in items]})
            print(f"BROKEN {err}: {url}")
        else:
            for it in items:
                it["last_verified"] = TODAY

    for cat, items in data.items():
        (DATA / f"{cat}.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    (DATA / "all.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (DATA / "broken_links.json").write_text(json.dumps(
        {"checked_at": datetime.now().isoformat(timespec="seconds"),
         "checked": len(todo), "broken": broken},
        ensure_ascii=False, indent=2) + "\n")

    print(f"{len(broken)} broken / {len(todo)} checked")


def demo():
    assert check("https://example.com") is None
    assert check("https://example.com/nope-404-xyz") is not None
    assert check("https://this-domain-does-not-exist-xyzq.invalid") is not None
    assert encode("https://it.wikipedia.org/wiki/Città") == \
        "https://it.wikipedia.org/wiki/Citt%C3%A0"
    assert check("https://it.wikipedia.org/wiki/Città") is None
    print("ok")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()
