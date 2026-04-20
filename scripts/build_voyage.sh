#!/usr/bin/env bash
# Full pipeline for a voyage: GPX → trips/harbors → geocode → Navily → standalone HTML.
#
# Usage: scripts/build_voyage.sh <voyage-name> [--skip-navily] [--skip-geocode]
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <voyage-name> [--skip-navily] [--skip-geocode]"
  exit 1
fi

NAME="$1"; shift
SKIP_NAVILY=0
SKIP_GEOCODE=0
for arg in "$@"; do
  case "$arg" in
    --skip-navily)  SKIP_NAVILY=1 ;;
    --skip-geocode) SKIP_GEOCODE=1 ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ ! -d "$ROOT/voyages/$NAME" ]; then
  echo "ERROR: voyages/$NAME not found. Run scripts/new_voyage.sh $NAME first."
  exit 1
fi

cd "$ROOT"
echo "==> build_trips"
python3 scripts/build_trips.py "$NAME"

if [ "$SKIP_GEOCODE" -eq 0 ]; then
  echo "==> geocode_harbors"
  python3 scripts/geocode_harbors.py "$NAME"
fi

if [ "$SKIP_NAVILY" -eq 0 ]; then
  echo "==> fetch_navily"
  python3 scripts/fetch_navily.py "$NAME"
fi

echo "==> build_standalone"
python3 scripts/build_standalone.py "$NAME"

echo ""
echo "Done. Open: voyages/$NAME/sailing-log-$NAME.html"
