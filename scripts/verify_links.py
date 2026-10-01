#!/usr/bin/env python3
"""Check the external links of the dataset and record what was actually observed.

Three different things used to be one stamp, `last_verified`. They are now kept apart:

  last_verified   a real HTTP request succeeded on the external link (2xx/3xx) on that date.
                  Never set for links generated from coordinates, never set on a failure.
  last_checked    the date of the last real request, whatever its outcome.
  last_status     what that request returned: "200", "404", "timeout", "dns", "tls", ...
  link_type       "osm_generated" for the OpenStreetMap link built from lat/lng (it always
                  resolves, so it is neither requested nor stamped), "external" otherwise.

A server that answers 401/403/429/999 is alive but refuses bots: it is recorded in
last_status, counted as `blocked`, and NOT stamped as verified (the page was not seen).

Requests: HEAD first, GET if HEAD is refused or fails, a declared User-Agent, a timeout,
retries with exponential backoff (Retry-After honoured, capped) and a minimum delay
between two requests to the same host. A link that fails is tried a second time after a
pause before being called broken. Items already carrying `link_rotto` have the original
URL re-examined; with --restore a link that answers again is put back.

Broken links land in data/broken_links.json for the weekly workflow to report.

Usage:
    python3 scripts/verify_links.py [--stale-days N] [--fix] [--restore]
                                    [--limit N] [--host-delay S] [--data-dir DIR] [--dry-run]
    python3 scripts/verify_links.py --selftest    # offline test against a local server

--fix      replace a dead link with the OpenStreetMap link built from the POI's own
           coordinates (the original goes to `link_rotto`).
--restore  put back the original URL of an item whose `link_rotto` answers again.
--limit N  check at most N URLs, and re-examine at most N link_rotto, spread evenly
           over the list (a sample, not a crawl).
--dry-run  do the requests and report, write nothing.
"""
import argparse
import json
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]
UA = "awesome-salerno-linkcheck/2.0 (+https://github.com/autcir/awesome-salerno; link checker, 1 req/s per host)"
TIMEOUT = 15
RETRIES = 2  # attempts after the first, for transient failures
BACKOFF = 2.0  # seconds, doubled at each retry
RETRY_AFTER_CAP = 30.0
SECOND_TRY_PAUSE = 5.0  # before a failed link is called broken
HOST_DELAY = 1.0
# a server that answers with these is alive, it just does not let a bot in
BLOCKED_CODES = {401, 403, 429, 999}
HEAD_REFUSED = {405, 501}
TODAY = date.today().isoformat()


def encode(url):
    """Percent-encode the non-ASCII parts; http.client only speaks latin-1."""
    u = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((
        u.scheme, u.netloc.encode("idna").decode("ascii"),
        urllib.parse.quote(u.path, safe="/%:@!$&'()*+,;=~-._"),
        urllib.parse.quote(u.query, safe="=&%:@/?+,;~-._"),
        urllib.parse.quote(u.fragment, safe="%")))


def is_osm(url):
    host = urllib.parse.urlsplit(url).netloc.lower()
    return host == "openstreetmap.org" or host.endswith(".openstreetmap.org")


class HostLimiter:
    """At most one request per `delay` seconds to the same host, across threads."""

    def __init__(self, delay):
        self.delay = delay
        self._next = {}
        self._lock = threading.Lock()

    def wait(self, host):
        with self._lock:
            now = time.monotonic()
            at = max(now, self._next.get(host, 0.0))
            self._next[host] = at + self.delay
        if at > now:
            time.sleep(at - now)


def classify_exc(e):
    reason = getattr(e, "reason", e)
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return "timeout"
    if isinstance(reason, socket.gaierror):
        return "dns"
    if isinstance(reason, ssl.SSLError):
        return "tls"
    if isinstance(reason, ConnectionError):
        return "connection"
    return f"error:{type(reason).__name__}"


def one_request(url, method):
    """Returns (status_code|None, error|None, retry_after_seconds|None)."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, None, None
    except urllib.error.HTTPError as e:
        ra = e.headers.get("Retry-After") if e.headers else None
        try:
            ra = float(ra) if ra is not None else None
        except ValueError:
            ra = None  # an HTTP-date: not worth parsing, plain backoff applies
        return e.code, None, ra
    except Exception as e:  # timeout, DNS, TLS, reset, redirect loop
        return None, classify_exc(e), None


def attempt(url, limiter):
    """One HEAD-then-GET pass. Returns (code|None, error|None, retry_after|None)."""
    host = urllib.parse.urlsplit(url).netloc.lower()
    limiter.wait(host)
    code, err, ra = one_request(url, "HEAD")
    if code is not None and code < 400:
        return code, None, None
    limiter.wait(host)  # a HEAD that fails or is refused is retried as a GET
    return one_request(url, "GET")


def outcome(code, err):
    if code is not None and code < 400:
        return "ok"
    if code in BLOCKED_CODES:
        return "blocked"
    return "broken"


def transient(code, err):
    return code is None or code == 429 or code >= 500


def check(url, limiter, sleep=time.sleep):
    """Returns {"outcome": ok|blocked|broken, "status": str}.

    Transient failures (timeout, reset, 5xx, 429) are retried with backoff; a 4xx
    other than 429 is a final answer and is not.
    """
    try:
        url = encode(url)
    except Exception as e:
        return {"outcome": "broken", "status": f"invalid-url:{type(e).__name__}"}
    code = err = None
    for i in range(RETRIES + 1):
        code, err, ra = attempt(url, limiter)
        if outcome(code, err) == "ok" or not transient(code, err):
            break
        if i < RETRIES:
            sleep(min(ra if ra is not None else BACKOFF * (2 ** i), RETRY_AFTER_CAP))
    return {"outcome": outcome(code, err), "status": str(code) if code is not None else err}


def check_twice(url, limiter, pause=SECOND_TRY_PAUSE):
    """A failing link gets a second, independent try after a pause before it is called broken."""
    res = check(url, limiter)
    if res["outcome"] == "broken":
        time.sleep(pause)
        second = check(url, limiter)
        if second["outcome"] != "broken":
            return second
        res["status"] = second["status"]
    return res


def osm_link(it):
    lat, lng = it["lat"], it["lng"]
    return (f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}"
            f"#map=16/{lat}/{lng}")


def sample(d, n):
    """n entries spread evenly over the dict, so a small sample is not all one host."""
    keys = list(d)
    if len(keys) <= n:
        return d
    step = len(keys) / n
    return {keys[int(i * step)]: d[keys[int(i * step)]] for i in range(n)}


def select(data, cutoff, limit):
    """Collect what to request. url -> items sharing it; rotto: link_rotto url -> items."""
    todo, rotto = {}, {}
    for items in data.values():
        for it in items:
            url = it.get("link") or ""
            if url and is_osm(url):
                it["link_type"] = "osm_generated"  # derived from coordinates: no request, no stamp
            elif url:
                seen = it.get("last_checked") or it.get("last_verified") or ""
                if seen < cutoff:
                    todo.setdefault(url, []).append(it)
            old = it.get("link_rotto")
            if old and not is_osm(old) and (it.get("link_rotto_checked") or "") < cutoff:
                rotto.setdefault(old, []).append(it)
    if limit is not None:
        todo, rotto = sample(todo, limit), sample(rotto, limit)
    return todo, rotto


def run_checks(urls, limiter, workers, pause):
    urls = list(urls)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(zip(urls, pool.map(lambda u: check_twice(u, limiter, pause), urls)))


def apply_results(todo, rotto, res_todo, res_rotto, fix, restore):
    stats = {"ok": 0, "blocked": 0, "broken": 0, "fixed": 0, "restored": 0}
    broken, blocked, restorable = [], [], []
    for url, items in todo.items():
        res = res_todo[url]
        stats[res["outcome"]] += 1
        for it in items:
            it["link_type"] = "external"
            it["last_checked"] = TODAY
            it["last_status"] = res["status"]
            if res["outcome"] == "ok":
                it["last_verified"] = TODAY
        if res["outcome"] == "blocked":
            blocked.append({"url": url, "status": res["status"], "pois": [i.get("id") for i in items]})
        elif res["outcome"] == "broken":
            entry = {"url": url, "error": res["status"], "pois": [i.get("id") for i in items]}
            if fix:
                for it in items:
                    if it.get("lat") and it.get("lng"):
                        it["link_rotto"] = url
                        it["link"] = osm_link(it)
                        it["link_type"] = "osm_generated"
                        stats["fixed"] += 1
                entry["fixed_with"] = "openstreetmap"
            broken.append(entry)
    for url, items in rotto.items():
        res = res_rotto[url]
        for it in items:
            it["link_rotto_checked"] = TODAY
            it["link_rotto_status"] = res["status"]
            if res["outcome"] == "ok":
                restorable.append({"url": url, "pois": [it.get("id")]})
                if restore and it.get("link_type") == "osm_generated":
                    it["link"] = url
                    it["link_type"] = "external"
                    it["last_verified"] = it["last_checked"] = TODAY
                    it["last_status"] = res["status"]
                    for k in ("link_rotto", "link_rotto_checked", "link_rotto_status"):
                        it.pop(k, None)
                    stats["restored"] += 1
    return stats, broken, blocked, restorable


def write_if_changed(path, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--stale-days", type=int, default=30)
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--host-delay", type=float, default=HOST_DELAY)
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--pause", type=float, default=SECOND_TRY_PAUSE, help="seconds before the second try")
    args = ap.parse_args(argv)

    cutoff = (date.today() - timedelta(days=args.stale_days)).isoformat()
    data = {c: json.loads((args.data_dir / f"{c}.json").read_text(encoding="utf-8")) for c in CATEGORIES}
    todo, rotto = select(data, cutoff, args.limit)
    print(f"requesting {len(todo)} external links and re-examining {len(rotto)} link_rotto "
          f"(older than {cutoff}), 1 request per {args.host_delay:g}s per host")

    limiter = HostLimiter(args.host_delay)
    res_todo = run_checks(todo, limiter, args.workers, args.pause)
    res_rotto = run_checks(rotto, limiter, args.workers, args.pause)
    stats, broken, blocked, restorable = apply_results(
        todo, rotto, res_todo, res_rotto, args.fix, args.restore)

    for b in broken:
        print(f"BROKEN {b['error']}: {b['url']}")
    for b in blocked:
        print(f"BLOCKED {b['status']} (alive, not verified): {b['url']}")
    for r in restorable:
        print(f"ALIVE AGAIN (link_rotto): {r['url']}")

    if not args.dry_run:
        for cat, items in data.items():
            write_if_changed(args.data_dir / f"{cat}.json", items)
        write_if_changed(args.data_dir / "all.json", data)
        write_if_changed(args.data_dir / "broken_links.json", {
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "checked": len(todo), "fixed": stats["fixed"],
            "blocked": len(blocked), "alive_again": len(restorable),
            "broken": broken})

    print(f"{stats['ok']} ok, {stats['blocked']} blocked, {stats['broken']} broken "
          f"/ {len(todo)} checked; {len(restorable)}/{len(rotto)} link_rotto answer again"
          + (f"; {stats['fixed']} switched to the OSM fallback" if args.fix else "")
          + (f"; {stats['restored']} restored" if args.restore else "")
          + ("  [dry-run, nothing written]" if args.dry_run else ""))
    return 0


def selftest():
    """Offline: a local HTTP server stands in for the web. No external network."""
    import http.server

    hits = []

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _do(self):
            hits.append((self.command, self.path, time.monotonic()))
            p = self.path
            if p == "/ok":
                self.send_response(200)
            elif p == "/nohead":
                self.send_response(405 if self.command == "HEAD" else 200)
            elif p == "/gone":
                self.send_response(404)
            elif p == "/forbidden":
                self.send_response(403)
            elif p == "/flaky":  # fails once, then answers: the retry must save it
                n = sum(1 for h in hits if h[1] == "/flaky" and h[0] == "GET")
                self.send_response(503 if n <= 1 else 200)
                if n <= 1:
                    self.send_header("Retry-After", "0")
            else:
                self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

        do_HEAD = do_GET = _do

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    lim = HostLimiter(0.0)
    nosleep = lambda s: None  # noqa: E731
    try:
        assert check(base + "/ok", lim)["outcome"] == "ok"
        assert [h[0] for h in hits[:1]] == ["HEAD"], "HEAD must come first"
        r = check(base + "/nohead", lim)
        assert r == {"outcome": "ok", "status": "200"}, r  # HEAD refused -> GET
        assert check(base + "/gone", lim) == {"outcome": "broken", "status": "404"}
        n404 = sum(1 for h in hits if h[1] == "/gone")
        assert n404 == 2, f"a 404 is final: HEAD+GET only, got {n404}"
        assert check(base + "/forbidden", lim) == {"outcome": "blocked", "status": "403"}
        assert check(base + "/flaky", lim, sleep=nosleep)["outcome"] == "ok", "5xx must be retried"
        dead = check("http://127.0.0.1:1/x", lim, sleep=nosleep)
        assert dead["outcome"] == "broken" and dead["status"] in ("connection", "timeout"), dead
        assert check_twice(base + "/gone", lim, pause=0)["outcome"] == "broken"
    finally:
        srv.shutdown()
    # per-host rate limit: 3 waits at 0.2s spacing take >= 0.4s
    rl = HostLimiter(0.2)
    t0 = time.monotonic()
    for _ in range(3):
        rl.wait("h")
    assert time.monotonic() - t0 >= 0.39, "host limiter did not space the requests"
    # osm links are recognised and never requested; others are
    assert is_osm("https://www.openstreetmap.org/?mlat=1&mlon=2#map=16/1/2")
    assert not is_osm("https://it.wikipedia.org/wiki/Salerno")
    assert not is_osm("https://notopenstreetmap.org/x")
    data = {"monumenti": [
        {"id": "a", "lat": 1, "lng": 2, "link": "https://www.openstreetmap.org/?mlat=1&mlon=2",
         "last_verified": "2026-01-01"},
        {"id": "b", "lat": 1, "lng": 2, "link": "https://example.org/x", "last_verified": "2026-01-01"}]}
    todo, rotto = select(data, "2026-06-01", None)
    assert list(todo) == ["https://example.org/x"] and not rotto
    a = data["monumenti"][0]
    assert a["link_type"] == "osm_generated" and a["last_verified"] == "2026-01-01", "osm must not be stamped"
    stats, broken, blocked, _ = apply_results(
        todo, {}, {"https://example.org/x": {"outcome": "broken", "status": "404"}}, {}, True, False)
    b = data["monumenti"][1]
    assert b["last_verified"] == "2026-01-01", "a failure must not move last_verified"
    assert b["last_checked"] == TODAY and b["link_rotto"] == "https://example.org/x" and is_osm(b["link"])
    assert encode("https://it.wikipedia.org/wiki/Città") == "https://it.wikipedia.org/wiki/Citt%C3%A0"
    assert osm_link({"lat": 40.5, "lng": 14.9}) == \
        "https://www.openstreetmap.org/?mlat=40.5&mlon=14.9#map=16/40.5/14.9"
    print("selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
