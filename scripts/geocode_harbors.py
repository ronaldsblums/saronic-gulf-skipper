#!/usr/bin/env python3
"""Reverse-geocode each harbour cluster using Nominatim (OpenStreetMap).

Usage: python3 scripts/geocode_harbors.py
  Reads/writes data/harbors.json (in place).
"""
import json, os, time, sys, urllib.request, urllib.parse


def reverse(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode({
        "lat": lat, "lon": lon, "format": "json", "zoom": 14,
        "addressdetails": 1,
    })
    req = urllib.request.Request(url, headers={"User-Agent": "saronic-sailing-log/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    harbors_path = os.path.join(root, "data", "harbors.json")
    if not os.path.exists(harbors_path):
        print(f"ERROR: {harbors_path} not found — run build_trips.py first")
        sys.exit(1)
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
            print(f"{h['id']} -> {(r.get('display_name') or '?')[:80]}")
        except Exception as e:
            print(f"{h['id']} ERROR: {e}")
            h["osm"] = None
        time.sleep(1.1)
    with open(harbors_path, "w") as fh:
        json.dump(harbors, fh, indent=2)


if __name__ == "__main__":
    main()
