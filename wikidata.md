# Wikidata enrichment — future work

Wikidata enrichment is **not yet merged** into the published dataset.
This note tracks what exists and what is missing.

## Current state (measured)

- Scraper: `scripts/wikidata_scrape.py` — SPARQL queries against
  `https://query.wikidata.org/sparql` for the Salerno province
  (Q132653): churches (Q16970), castles (Q23413), museums (Q33506),
  archaeological sites (Q83620), monuments (Q5107), each requiring
  coordinates (P625).
- Results cache: `wikidata_results.json` at the repo root, with one key
  per query (`chiese_wikidata`, `castelli_wikidata`, `musei_wikidata`,
  `archeologico_wikidata`, `monumenti_wikidata`).
- Last measured run returned **0 rows in all 5 categories**, so there is
  nothing to merge yet — the `monumenti.json` entries (3479) currently
  carry `source: osm|scraped|curated` only, with no `wikidata` field.

## Future work

1. Re-run the scraper with a working endpoint / pagination and verify
   non-empty results before merging.
2. Match Wikidata QIDs to existing `monumenti.json` entries by
   name + coordinates (dedupe on QID, keep existing `id` stable).
3. Enrich matched entries with `wikidata` (QID), Italian description,
   and image (P18) where the license allows it.
4. Keep every new `link` verifiable (Wikipedia or wikidata.org URL);
   never invent coordinates — GPS stays required.

## Known limitation: trails as LineString

- `sentieri.json` (1676 trails) stores **one Point per trail**
  (`lat`/`lng`, e.g. trailhead or village centroid).
- Consequently `data/awesome-salerno.geojson` (5547 features) is
  **all `Point` geometries**, and `data/awesome-salerno.kml` /
  `.kmz` use Point placemarks.
- True trail polylines (GeoJSON `LineString`, KML `LineString`)
  **need GPS tracks** (GPX files or OSM route relations with full
  geometry), which the current Overpass extracts do not provide.
- Until tracks are sourced per trail, trails stay Points by design;
  a future `track` / `coordinates[]` field can carry the polyline
  without breaking the existing `lat`/`lng` schema.
