#!/usr/bin/env python3
"""Parse GPX files in a voyage folder, extract trips + harbors to JSON.

Usage: python3 scripts/build_trips.py <voyage-name>
  Reads:  voyages/<voyage-name>/gpx/*.gpx
  Writes: voyages/<voyage-name>/data/trips.json, harbors.json
"""
import xml.etree.ElementTree as ET
import os, glob, json, math, sys
from datetime import datetime

NS = {'g': 'http://www.topografix.com/GPX/1/1'}

HARBOR_CLUSTER_KM = 1.5
STOP_MIN_MINUTES = 30
SIMPLIFY_EPSILON = 0.00015


def haversine_km(a, b):
    R = 6371.0
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    x = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def perp_dist(p, a, b):
    if a == b:
        return haversine_km(p, a) * 1000
    dx, dy = b[1] - a[1], b[0] - a[0]
    t = ((p[1] - a[1]) * dx + (p[0] - a[0]) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj = (a[0] + t * dy, a[1] + t * dx)
    return haversine_km(p, proj) * 1000


def douglas_peucker(points, eps_deg):
    if len(points) < 3:
        return points[:]
    def _dp(pts):
        if len(pts) < 3:
            return pts
        a, b = pts[0], pts[-1]
        dmax, idx = 0, 0
        for i in range(1, len(pts) - 1):
            d = perp_dist(pts[i], a, b)
            if d > dmax:
                dmax, idx = d, i
        if dmax > eps_deg * 111000:
            left = _dp(pts[:idx + 1])
            right = _dp(pts[idx:])
            return left[:-1] + right
        return [a, b]
    return _dp(points)


def parse_gpx(path):
    tree = ET.parse(path)
    root = tree.getroot()
    name_el = root.find('.//g:trk/g:name', NS)
    name = name_el.text if name_el is not None else os.path.basename(path)
    pts = []
    for p in root.findall('.//g:trkpt', NS):
        lat = float(p.get('lat'))
        lon = float(p.get('lon'))
        t_el = p.find('g:time', NS)
        t = t_el.text if t_el is not None else None
        pts.append((lat, lon, t))
    return name, pts


def detect_stops(points):
    stops = []
    if len(points) < 2:
        return stops
    i = 0
    n = len(points)
    while i < n - 1:
        anchor = points[i]
        j = i + 1
        while j < n and haversine_km((anchor[0], anchor[1]), (points[j][0], points[j][1])) < 0.12:
            j += 1
        t_start = datetime.fromisoformat(points[i][2].replace('Z', '+00:00'))
        t_end = datetime.fromisoformat(points[j - 1][2].replace('Z', '+00:00'))
        dur_min = (t_end - t_start).total_seconds() / 60
        if dur_min >= STOP_MIN_MINUTES:
            lats = [points[k][0] for k in range(i, j)]
            lons = [points[k][1] for k in range(i, j)]
            stops.append({
                "lat": sum(lats) / len(lats),
                "lon": sum(lons) / len(lons),
                "start": points[i][2],
                "end": points[j - 1][2],
                "duration_min": round(dur_min),
            })
        i = max(j, i + 1)
    return stops


def cluster_harbors(all_stops):
    harbors = []
    for stop in all_stops:
        placed = False
        for h in harbors:
            if haversine_km((stop["lat"], stop["lon"]), (h["lat"], h["lon"])) < HARBOR_CLUSTER_KM:
                h["visits"].append(stop)
                n = len(h["visits"])
                h["lat"] = (h["lat"] * (n - 1) + stop["lat"]) / n
                h["lon"] = (h["lon"] * (n - 1) + stop["lon"]) / n
                placed = True
                break
        if not placed:
            harbors.append({"lat": stop["lat"], "lon": stop["lon"], "visits": [stop]})
    return harbors


def main():
    if len(sys.argv) < 2:
        print("Usage: build_trips.py <voyage-name>")
        sys.exit(1)
    voyage = sys.argv[1]
    root = os.path.join(os.path.dirname(__file__), "..", "voyages", voyage)
    gpx_dir = os.path.join(root, "gpx")
    out_dir = os.path.join(root, "data")
    if not os.path.isdir(gpx_dir):
        print(f"ERROR: {gpx_dir} not found")
        sys.exit(1)
    os.makedirs(out_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(gpx_dir, '*.gpx')))
    trips = []
    all_stops = []

    for f in files:
        name, pts = parse_gpx(f)
        if not pts:
            continue
        date = pts[0][2][:10]
        simplified = douglas_peucker([(p[0], p[1]) for p in pts], SIMPLIFY_EPSILON)
        simplified = [[round(la, 5), round(lo, 5)] for la, lo in simplified]
        dist = 0.0
        for k in range(1, len(pts)):
            dist += haversine_km((pts[k-1][0], pts[k-1][1]), (pts[k][0], pts[k][1]))
        stops = detect_stops(pts)
        for s in stops:
            s["trip_id"] = os.path.basename(f).replace('.gpx', '')
        all_stops.extend(stops)
        for t, label in [(pts[0], 'start'), (pts[-1], 'end')]:
            all_stops.append({
                "lat": t[0], "lon": t[1], "start": t[2], "end": t[2],
                "duration_min": 0, "kind": label,
                "trip_id": os.path.basename(f).replace('.gpx', ''),
            })
        trips.append({
            "id": os.path.basename(f).replace('.gpx', ''),
            "name": name, "date": date,
            "t_start": pts[0][2], "t_end": pts[-1][2],
            "distance_km": round(dist, 2),
            "distance_nm": round(dist / 1.852, 2),
            "point_count": len(pts),
            "track": simplified,
        })

    harbors = cluster_harbors(all_stops)
    for i, h in enumerate(harbors):
        h["id"] = f"h{i+1:02d}"
        h["lat"] = round(h["lat"], 5)
        h["lon"] = round(h["lon"], 5)
        h["visits"].sort(key=lambda x: x.get("start") or "")

    with open(os.path.join(out_dir, "trips.json"), "w") as fh:
        json.dump(trips, fh, indent=2)
    with open(os.path.join(out_dir, "harbors.json"), "w") as fh:
        json.dump(harbors, fh, indent=2)

    print(f"[{voyage}] {len(trips)} trips, {len(harbors)} harbors")


if __name__ == "__main__":
    main()
