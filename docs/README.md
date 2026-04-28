# Saronic Gulf Sailing Log

A friend-facing visual log of the routes we've sailed in the Saronic Gulf —
assembled from GPX tracks into a single map app you can browse or share.

The app shows:

- **Voyages** — multi-day trips grouped by date, each with a colour on the map.
- **Day legs** — every GPX file as a clickable polyline, with date and distance.
- **Harbours** — clusters of stops, with visit counts and (where available)
  community references from Navily.
- **Totals** — sailing days, nautical miles, voyages, harbours.

This is a memory map, not a navigation tool. Harbour names are auto-resolved from
coordinates and shown with an "approx." badge where the match is loose. Anything
under "Anchorage / Marina reference" is community data (Navily reviews, services,
seabed) — useful context, not safety guidance.

## Run it

The app is a single `index.html` (React + Leaflet via CDN) that fetches three
JSON files from `data/`. Because browsers block `fetch()` on `file://`, you need a
tiny local server:

```bash
bash serve.sh        # serves http://localhost:8080
```

Then open http://localhost:8080 in your browser.

For a single-file version that works without a server (good for sharing via
Dropbox / e-mail), build the standalone:

```bash
python3 scripts/build_standalone.py
# -> sailing-log.html  (data inlined)
```

## Layout

```
gpx/                 GPX files from the GPS / chart plotter
data/
  trips.json         per-track summary + simplified polyline
  harbors.json       clustered stop locations + reverse-geocoded names
  navily.json        Navily anchorage/marina records (cached, optional)
navily_urls.txt      Navily URLs to scrape, one per line
index.html           the friend-facing app
serve.sh             local HTTP server helper
scripts/
  build_trips.py     GPX -> trips.json + harbors.json
  geocode_harbors.py harbours -> OSM names (Nominatim)
  fetch_navily.py    URLs -> navily.json + harbour matches
  build_standalone.py index.html + data -> sailing-log.html
  build.sh           runs the four steps in order
```

One repo = one voyage area. Drop more GPX files into `gpx/` and re-run the
pipeline; the app will pick them up.

## Rebuild from GPX

```bash
bash scripts/build.sh                 # full pipeline
bash scripts/build.sh --skip-navily   # skip the slow Wayback scrape
bash scripts/build.sh --skip-geocode  # skip Nominatim lookups (offline)
```

The pipeline is idempotent: re-running with the same GPX files produces the
same JSON. Navily and OSM responses are cached in `data/`.

### Adding Navily references

Edit `navily_urls.txt` (one Navily URL per line, `#` for comments), then:

```bash
python3 scripts/fetch_navily.py
```

URLs are fetched via the Wayback Machine (Navily's live site is behind
Cloudflare). Records within 3 km of a harbour cluster are attached to it.

## Data shape

`trips.json` — array of:
```jsonc
{
  "id": "activity_18948503194",
  "name": "Aegina Sailing",
  "date": "2025-04-27",
  "t_start": "...", "t_end": "...",
  "distance_km": 24.1, "distance_nm": 13.0,
  "track": [[lat,lon], ...]   // simplified, ~hundreds of points
}
```

`harbors.json` — array of:
```jsonc
{
  "id": "h01",
  "lat": 37.69099, "lon": 23.45162,
  "visits": [{ "trip_id": "...", "start": "...", "duration_min": 102, ... }],
  "osm": { "address": { "village": "...", ... } },
  "navily": [{ "id": 12345, "kind": "anchorage", "name": "...", "url": "..." }]
}
```

`navily.json` — keyed by Navily ID, each record has rating, reviews, seabed,
mooring, services, image, etc.

## Notes & caveats

- The map uses CartoDB dark tiles; needs internet on first load to fetch them.
- React, Babel, and Leaflet are loaded from CDN; no build step required.
- Times are stored and displayed in UTC.
- "Approx." harbour names are those where Nominatim returned only a region
  (municipality / county) rather than a specific village or town — common in
  open anchorages without a settlement nearby.
