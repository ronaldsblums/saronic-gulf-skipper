#!/usr/bin/env bash
# Scaffold a new voyage folder. Optionally import GPX files from a source folder.
#
# Usage:
#   scripts/new_voyage.sh <voyage-name> [gpx-source-folder]
#
# Examples:
#   scripts/new_voyage.sh spain-2022 ~/Downloads
#   scripts/new_voyage.sh sicily-2026
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <voyage-name> [gpx-source-folder]"
  exit 1
fi

NAME="$1"
SRC="${2:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/voyages/$NAME"

if [ -d "$DEST" ]; then
  echo "ERROR: voyages/$NAME already exists"
  exit 1
fi

mkdir -p "$DEST/gpx" "$DEST/data"

cat > "$DEST/navily_urls.txt" <<EOF
# Navily URLs for voyage: $NAME
# One URL per line. Find URLs by searching "site:navily.com <place-name>".
# Lines starting with # are ignored.
# After adding URLs, run:
#   python3 scripts/fetch_navily.py $NAME
EOF

if [ -n "$SRC" ]; then
  if [ ! -d "$SRC" ]; then
    echo "ERROR: source folder $SRC does not exist"
    exit 1
  fi
  cnt=$(find "$SRC" -maxdepth 1 -name 'activity_*.gpx' -o -name '*.gpx' | wc -l | tr -d ' ')
  if [ "$cnt" -eq 0 ]; then
    echo "Warning: no .gpx files found in $SRC"
  else
    find "$SRC" -maxdepth 1 \( -name 'activity_*.gpx' -o -name '*.gpx' \) -exec mv {} "$DEST/gpx/" \;
    echo "Moved $cnt GPX file(s) from $SRC to $DEST/gpx/"
  fi
fi

echo ""
echo "Created voyages/$NAME/"
echo ""
echo "Next steps:"
echo "  1. Ensure GPX files are in voyages/$NAME/gpx/"
echo "  2. Build:  scripts/build_voyage.sh $NAME"
echo "  3. Optional: edit voyages/$NAME/navily_urls.txt, then rerun build"
