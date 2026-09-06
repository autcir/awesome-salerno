# Data

This directory contains structured data about POIs (Points of Interest) in Salerno, the Amalfi Coast and the Cilento.

## Files

| File | Description | Entries |
|---|---|---|
| `mangiare.json` | Food & drink businesses | 32 |
| `luoghi.json` | Attractions, services, churches | 122 |
| `dormire.json` | Accommodation (hotels, B&B, agriturismi) | 47 |
| `spiagge.json` | Beaches | 23 |
| `all-pois.json` | Combined flat list of all POIs | 224 |
| `all-pois.csv` | CSV export for spreadsheet use | 224 |

## Data Format

Each POI in the JSON files follows this schema:

```json
{
  "id": "string - unique identifier",
  "slug": "string - URL-friendly name",
  "title": "string - display name",
  "section": "string - mangiare|luoghi|hotel",
  "subsection": "string|null - sub-section",
  "category": "string - food|shopping|accommodation|attraction|...",
  "subcategory": "string - specific type",
  "description": "string - brief description",
  "address": "string - street address",
  "district": "string - neighborhood or town",
  "lat": "number|null - latitude",
  "lng": "number|null - longitude",
  "rating": {
    "score": "number|null - average rating",
    "count": "number - number of reviews"
  },
  "placeId": "string|null - Google Places ID (if available)",
  "image": "string|null - photo URL",
  "hasPhoto": "boolean - whether a photo is available",
  "source": "string - osm|scraped|curated",
  "curated": "boolean - whether manually verified"
}
```

## Sources

- **OpenStreetMap** (`source: osm`) - Via Overpass API
- **Scraped** (`source: scraped`) - Manual and automated scraping
- **Curated** (`source: curated`) - Manually verified entries

## License

This data is released under [CC0 1.0 Universal](../LICENSE).
