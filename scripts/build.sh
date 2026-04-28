#!/usr/bin/env bash
# Full pipeline: GPX -> trips/harbours -> reverse-geocode -> Navily -> standalone HTML.
#
# Usage: scripts/build.sh [--skip-geocode] [--skip-navily] [--skip-standalone]
set -euo pipefail

SKIP_GEOCODE=0
SKIP_NAVILY=0
SKIP_STANDALONE=0
for arg in "$@"; do
  case "$arg" in
    --skip-geocode)    SKIP_GEOCODE=1 ;;
    --skip-navily)     SKIP_NAVILY=1 ;;
    --skip-standalone) SKIP_STANDALONE=1 ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! ls gpx/*.gpx >/dev/null 2>&1; then
  echo "ERROR: no GPX files found in gpx/"
  exit 1
fi

echo "==> build_trips"
python3 scripts/build_trips.py

if [ "$SKIP_GEOCODE" -eq 0 ]; then
  echo "==> geocode_harbors"
  python3 scripts/geocode_harbors.py
fi

if [ "$SKIP_NAVILY" -eq 0 ]; then
  echo "==> fetch_navily"
  python3 scripts/fetch_navily.py
fi

if [ "$SKIP_STANDALONE" -eq 0 ]; then
  echo "==> build_standalone"
  python3 scripts/build_standalone.py
fi

echo ""
echo "Done. Open index.html via 'bash serve.sh' or share sailing-log.html directly."
