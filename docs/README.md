# Saronic Gulf Skipper Decision Tool

**Boat:** Jeanneau Sun Odyssey 440, 4-cabin, 2019 (draft 2.20m)
**Base:** Piraeus Marina
**Trip:** 6-day sailing (Sun check-in, Mon departure, Sat return)

## What Was Built

An interactive skipper decision-support tool for real-time sailing decisions in the Saronic Gulf. Two versions:

- **`index.html`** — Primary version. Loads location data from `data/locations.json` at runtime. Requires an HTTP server (run `bash serve.sh` then open `http://localhost:8080`).
- **`saronic-gulf-skipper-tool.html`** — Self-contained version with all locations embedded. Open directly in any browser, no server needed. Good for sharing with co-travelers.

Both versions fetch live weather forecasts from the Open-Meteo API.

### Features

**Dashboard** — Live wind conditions (current, +12h, +24h, +48h trends), best stops ranked by real-time suitability, quick stats.

**Route Planner** — 6-day itinerary builder (Mon–Sat) with Plan A / Plan B support. Each stop shows leg distance (nm), ETA at 5.5kt and 6.5kt, suitability status, depth/draft warnings, and route warnings (long legs, exposed destinations, settled-weather-only stops, nearest fallback). Route selections sync with the Map view.

**Map View** — Leaflet interactive map with CartoDB Voyager base tiles and OpenSeaMap seamark overlay. Markers color-coded by suitability. Click any marker for full details. Active route drawn as dashed polylines.

**Locations** — Filterable directory of all stops with expandable detail cards. Filters: island, type, wind protection direction, overnight safe, settled weather, fuel, water, electricity, safe depth, fallback value, suitability (now/tomorrow).

**Compare** — Select 2–4 locations for side-by-side comparison.

### Decision Engine

The suitability engine evaluates each location against clustered live forecasts:

- Locations are grouped into forecast clusters by geographic proximity (≤3nm radius). Each cluster gets its own API call using its centroid coordinates. With the current locations this produces clusters per island group.
- Fetches wind speed, direction, gusts from Open-Meteo `/v1/forecast` (knots), and marine data (wave height, swell) from `/v1/marine`, per cluster.
- Score-based system (0–100) with penalties for: wind exposure, high gusts (>25kt, >30kt), wave height (>1.5m, >2.5m), settled-weather-only conditions, non-overnight locations, difficult approaches, ferry wake, and draft/depth clearance.
- Draft awareness: 2.20m draft + 0.50m safety margin = 2.70m minimum safe depth. Locations with shallow spots are flagged with guidance.
- Status thresholds: Good (70+), Caution (45–69), Poor (20–44), Avoid (<20).

### Forecast Failure Handling

A status banner below the header shows:
- **Live forecast** — all clusters fetched successfully
- **Partial forecast** — some clusters failed (affected locations show "No forecast")
- **Forecast unavailable** — all calls failed (suitability is not live)

The banner shows the last successful refresh timestamp and a retry button.

### Schema Validation

On startup, `locations.json` is validated before use:
- Required fields and types