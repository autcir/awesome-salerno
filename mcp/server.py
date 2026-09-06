#!/usr/bin/env python3
"""MCP server over the awesome-salerno dataset (stdio, JSON-RPC 2.0).

Stdlib only, no SDK: the protocol surface we need is four methods.
Search and filtering are reused from api/server.py.

Config for Claude Desktop / Claude Code:

    {"mcpServers": {"awesome-salerno":
        {"command": "python3", "args": ["/path/to/awesome-salerno/mcp/server.py"]}}}

    python3 mcp/server.py --demo    # self-check, no stdio loop
"""
import json
import math
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
from server import load_json, search_data, filter_items  # noqa: E402

CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]
MAX_RESULTS = 50

TOOLS = [
    {
        "name": "search_poi",
        "description": "Cerca POI (sentieri, monumenti, spiagge, panorami, parchi, "
                       "eventi) di Salerno, Costiera Amalfitana e Cilento per nome, "
                       "descrizione, citta o quartiere.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "testo da cercare"},
                "categoria": {"type": "string", "enum": CATEGORIES},
                "zona": {"type": "string", "enum": ["salerno", "costiera", "cilento"]},
                "tipo": {"type": "string", "description": "chiesa, castello, museo, spiaggia..."},
                "citta": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_poi",
        "description": "Restituisce un POI completo dato il suo id.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    {
        "name": "nearby_poi",
        "description": "POI entro un raggio in km da una coordinata GPS, dal piu vicino.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lng": {"type": "number"},
                "radius_km": {"type": "number", "default": 5},
                "categoria": {"type": "string", "enum": CATEGORIES},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["lat", "lng"],
        },
    },
    {
        "name": "list_events",
        "description": "Eventi in programma, opzionalmente entro una finestra di date "
                       "(YYYY-MM-DD). Senza argomenti: eventi attivi oggi o futuri.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from": {"type": "string"},
                "to": {"type": "string"},
                "citta": {"type": "string"},
            },
        },
    },
]


def all_data():
    return {c: load_json(f"{c}.json") for c in CATEGORIES}


def haversine_km(lat1, lng1, lat2, lng2):
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def slim(item):
    """Trim to what an LLM needs; full record is one get_poi away."""
    keys = ["id", "nome", "descrizione", "categoria", "tipo", "zona", "citta",
            "quartiere", "lat", "lng", "link", "data_inizio", "data_fine",
            "last_verified", "distanza_km"]
    return {k: item[k] for k in keys if item.get(k) is not None}


def tool_search(args):
    data = all_data()
    if args.get("categoria"):
        data = {args["categoria"]: data[args["categoria"]]}
    results = search_data(args["query"], data)
    params = {k: [args[k]] for k in ("zona", "tipo", "citta") if args.get(k)}
    if params:
        results = filter_items(results, params)
    limit = min(args.get("limit", 20), MAX_RESULTS)
    return {"total": len(results), "results": [slim(i) for i in results[:limit]]}


def tool_get(args):
    for cat, items in all_data().items():
        for it in items:
            if it.get("id") == args["id"]:
                return {**it, "categoria": cat}
    return {"error": f"POI '{args['id']}' non trovato"}


def tool_nearby(args):
    radius = args.get("radius_km", 5)
    data = all_data()
    if args.get("categoria"):
        data = {args["categoria"]: data[args["categoria"]]}
    out = []
    for cat, items in data.items():
        for it in items:
            if not (it.get("lat") and it.get("lng")):
                continue
            d = haversine_km(args["lat"], args["lng"], it["lat"], it["lng"])
            if d <= radius:
                out.append({**it, "categoria": cat, "distanza_km": round(d, 2)})
    out.sort(key=lambda i: i["distanza_km"])
    limit = min(args.get("limit", 20), MAX_RESULTS)
    return {"total": len(out), "results": [slim(i) for i in out[:limit]]}


def tool_events(args):
    start = args.get("from") or date.today().isoformat()
    end = args.get("to") or "9999-12-31"
    out = []
    for ev in load_json("eventi.json"):
        ev_start = ev.get("data_inizio", "")
        ev_end = ev.get("data_fine") or ev_start
        if ev_end and ev_end < start:
            continue
        if ev_start and ev_start > end:
            continue
        if args.get("citta") and args["citta"].lower() not in ev.get("citta", "").lower():
            continue
        out.append({**ev, "categoria": "eventi"})
    out.sort(key=lambda e: e.get("data_inizio") or "")
    return {"total": len(out), "results": [slim(e) for e in out]}


HANDLERS = {"search_poi": tool_search, "get_poi": tool_get,
            "nearby_poi": tool_nearby, "list_events": tool_events}


def handle(req):
    """Return a JSON-RPC response dict, or None for notifications."""
    method, rid = req.get("method"), req.get("id")

    def ok(result):
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    if method == "initialize":
        return ok({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "awesome-salerno", "version": "1.0.0"},
        })
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        params = req.get("params", {})
        fn = HANDLERS.get(params.get("name"))
        if not fn:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32601, "message": f"unknown tool {params.get('name')}"}}
        try:
            result = fn(params.get("arguments") or {})
            is_error = isinstance(result, dict) and "error" in result
        except Exception as e:
            result, is_error = {"error": f"{type(e).__name__}: {e}"}, True
        return ok({"content": [{"type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                   "isError": is_error})
    if rid is None:
        return None  # notification (e.g. notifications/initialized)
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"unknown method {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            resp = handle(json.loads(line))
        except json.JSONDecodeError:
            resp = {"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700, "message": "parse error"}}
        if resp is not None:
            print(json.dumps(resp, ensure_ascii=False), flush=True)


def demo():
    assert handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})["result"]["serverInfo"]["name"] == "awesome-salerno"
    assert len(handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]) == 4
    assert handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None

    def call(name, args):
        r = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": name, "arguments": args}})
        return json.loads(r["result"]["content"][0]["text"]), r["result"]["isError"]

    res, err = call("search_poi", {"query": "paestum"})
    assert not err and res["total"] > 0, res
    res, err = call("search_poi", {"query": "chiesa", "zona": "cilento", "limit": 5})
    assert not err and len(res["results"]) <= 5
    res, _ = call("nearby_poi", {"lat": 40.678, "lng": 14.768, "radius_km": 1})
    assert res["total"] > 0 and res["results"][0]["distanza_km"] <= 1
    assert res["results"] == sorted(res["results"], key=lambda i: i["distanza_km"])
    res, _ = call("list_events", {"from": "2025-01-01", "to": "2026-12-31"})
    assert res["total"] > 0
    res, err = call("get_poi", {"id": "non-esiste"})
    assert err and "error" in res
    res, err = call("get_poi", {"id": "luci-dartista-2025"})
    assert not err and res["nome"].startswith("Luci")
    _, err = call("search_poi", {})  # missing required arg -> error, not crash
    assert err
    print("ok")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()
