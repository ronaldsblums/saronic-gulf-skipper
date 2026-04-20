#!/usr/bin/env python3
"""Reverse-geocode each harbor cluster using Nominatim (OpenStreetMap).

Usage: python3 scripts/geocode_harbors.py <voyage-name>
"""
import json, os, time, sys, urllib.request, urllib.parse


def reverse(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode({
        "lat": lat, "lon": lon, "format": "json", "zoom": 14,
        "addressdetails": 1,
    })
    req = urllib.request.Request(url, headers={"User-Agent": "sailing-log/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def main():
    if len(sys.argv) < 2:
        print("Usage: geocode_harbors.py <voyage-name>")
        sys.exit(1)
    voyage = sys.argv[1]
    harbors_path = os.path.join(os.path.dirname(__file__), "..", "voyages", voyage, "data", "harbors.json")
    with open(harbors_path) as fh:
        harbors = json.load(fh)
    for h in harbors:
        try:
            r = reverse(h["lat"], h["lon"])
            h["osm"] = {
                "display_name": r.get("display_name"),
                "address": r.get("address"),
                "name": r.get("name"),
            }
            print(f"[{voyage}] {h['id']} → {r.get('display_name', '?')[:80]}")
        except Exception as e:
            print(f"[{voyage}] {h['id']} ERROR: {e}")
            h["osm"] = None
        time.sleep(1.1)
    with open(harbors_path, "w") as fh:
        json.dump(harbors, fh, indent=2)


if __name__ == "__main__":
    main()
