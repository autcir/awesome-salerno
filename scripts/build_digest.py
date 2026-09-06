#!/usr/bin/env python3
"""Generate the monthly digest: what is coming up and what changed.

    python3 scripts/build_digest.py [YYYY-MM]

Writes docs/digest/YYYY-MM.md and refreshes docs/digest/index.md. The "what
changed" half is read from git, so the digest never disagrees with the repo.
"""
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "docs" / "digest"
CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]
MONTHS = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
          "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def month_bounds(ym):
    first = date(int(ym[:4]), int(ym[5:]), 1)
    nxt = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    return first, nxt - timedelta(days=1)


def git(*args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args],
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return ""


def fmt(d):
    if not d:
        return ""
    y, m, dd = d.split("-")
    return f"{int(dd)} {MONTHS[int(m) - 1]} {y}"


def upcoming(first, last):
    """Events overlapping the digest month, earliest first."""
    out = []
    for ev in json.loads((DATA / "eventi.json").read_text()):
        start = ev.get("data_inizio", "")
        end = ev.get("data_fine") or start
        if start and end and start <= last.isoformat() and end >= first.isoformat():
            out.append(ev)
    return sorted(out, key=lambda e: e.get("data_inizio") or "")


def changes(since):
    """Commits and POI count delta since a date."""
    log = git("log", f"--since={since}", "--pretty=- %s").strip()
    commits = [l for l in log.splitlines() if not l.startswith("- chore:")]
    now = sum(len(json.loads((DATA / f"{c}.json").read_text())) for c in CATEGORIES)
    old = git("show", f"HEAD@{{{since}}}:data/all.json")
    try:
        before = sum(len(v) for v in json.loads(old).values())
    except Exception:
        before = None
    return commits, now, before


def build(ym):
    first, last = month_bounds(ym)
    events = upcoming(first, last)
    commits, total, before = changes(first.isoformat())
    broken = json.loads((DATA / "broken_links.json").read_text())

    lines = [f"# Awesome Salerno - {MONTHS[first.month - 1]} {first.year}", "",
             f"> Digest del {fmt(date.today().isoformat())}. "
             f"{total} POI in lista.", "", "## In programma", ""]
    if events:
        for ev in events:
            when = fmt(ev.get("data_inizio"))
            if ev.get("data_fine") and ev["data_fine"] != ev.get("data_inizio"):
                when += " - " + fmt(ev["data_fine"])
            link = ev.get("link", "")
            name = f"[{ev['nome']}]({link})" if link else ev["nome"]
            lines.append(f"- **{when}** - {name}, {ev.get('citta', '')}. "
                         f"{ev.get('descrizione', '')}")
    else:
        lines.append("Nessun evento in calendario per questo mese.")

    lines += ["", "## Cosa e' cambiato", ""]
    if before is not None and before != total:
        delta = total - before
        lines.append(f"- POI: {before} -> {total} ({delta:+d})")
    lines += commits or ["- Nessuna modifica al dataset in questo periodo."]

    lines += ["", "## Stato dei link", "",
              f"- Ultimo controllo: {broken['checked_at'][:10]}",
              f"- Link esterni controllati: {broken['checked']}",
              f"- Rotti: {len(broken['broken'])}"]
    if broken.get("fixed"):
        lines.append(f"- Riparati automaticamente: {broken['fixed']}")

    lines += ["", "---", "",
              "Dati CC0 - [awesome-salerno](https://github.com/autcir/awesome-salerno)",
              ""]
    return "\n".join(lines)


def main():
    ym = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1][0].isdigit() \
        else date.today().strftime("%Y-%m")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{ym}.md"
    path.write_text(build(ym))

    issues = sorted((p.stem for p in OUT.glob("20*.md")), reverse=True)
    index = ["# Digest mensile", "",
             "Eventi in programma, novita' del dataset e stato dei link, mese per mese.",
             ""]
    for ym_ in issues:
        y, m = ym_.split("-")
        index.append(f"- [{MONTHS[int(m) - 1].capitalize()} {y}]({ym_}.md)")
    (OUT / "index.md").write_text("\n".join(index) + "\n")
    print(f"{path.relative_to(ROOT)} ({len(path.read_text().splitlines())} righe), "
          f"{len(issues)} numeri in indice")


def demo():
    assert month_bounds("2026-02") == (date(2026, 2, 1), date(2026, 2, 28))
    assert month_bounds("2026-12") == (date(2026, 12, 1), date(2026, 12, 31))
    assert fmt("2026-01-09") == "9 gennaio 2026"
    # Luci d'Artista runs Nov 2025 -> Feb 2026, so it must show up in January
    names = [e["nome"] for e in upcoming(*month_bounds("2026-01"))]
    assert any("Luci d'Artista" in n for n in names), names
    assert "# Awesome Salerno - gennaio 2026" in build("2026-01")
    print("ok")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()
