#!/usr/bin/env python3
"""Fetch Navily anchorage/marina data via Wayback Machine (bypasses Cloudflare).

Usage: python3 scripts/fetch_navily.py
  Reads URLs from navily_urls.txt at the repo root (one per line, # for comments).
  Writes data/navily.json (cached) and updates data/harbors.json with matches.
"""
import os, re, json, time, math, sys, urllib.request, urllib.parse

WAYBACK_SNAPSHOTS = [
    "https://web.archive.org/web/2024/",
    "https://web.archive.org/web/2023/",
    "https://web.archive.org/web/2022/",
    "https://web.archive.org/web/2021/",
]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
SEABED_TERMS = ["Sand", "Mud", "Rock", "Seagrass", "Weed", "Coral", "Gravel",
                "Pebbles", "Shingle", "Clay", "Posidonia", "Stones"]


def haversine_km(a, b):
    R = 6371.0
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    x = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def fetch_wayback(url, retries=3):
    for snapshot in WAYBACK_SNAPSHOTS:
        delay = 2.0
        for attempt in range(retries):
            try:
                req = urllib.request.Request(snapshot + url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=40) as r:
                    return r.read().decode("utf-8", errors="ignore")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break
                print(f"  HTTP {e.code} {url} @ {snapshot.split('/')[-2]}")
            except Exception as e:
                print(f"  ERR {url} @ {snapshot.split('/')[-2]}: {e}")
            time.sleep(delay)
            delay *= 1.8
    return None


def clean_wb(h):
    h = re.sub(r'<!-- BEGIN WAYBACK TOOLBAR INSERT -->.*?<!-- END WAYBACK TOOLBAR INSERT -->', '', h, flags=re.S)
    h = re.sub(r'https://web\.archive\.org/web/\d+(?:im_|js_|cs_)?/', '', h)
    return h


def parse_page(url, html):
    html = clean_wb(html)
    data = {"url": url}

    m = re.search(r'/(mouillage|port)/([^/]+)/(\d+)', url)
    if m:
        data["kind"] = "anchorage" if m.group(1) == "mouillage" else "marina"
        data["slug"] = m.group(2)
        data["navily_id"] = int(m.group(3))

    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        try:
            jd = json.loads(m.group(1).strip())
        except Exception:
            continue
        if not isinstance(jd, dict):
            continue
        if jd.get("name") and "name" not in data:
            data["name"] = jd["name"]
        geo = jd.get("geo", {}) or {}
        if geo.get("latitude") and "lat" not in data:
            data["lat"] = float(geo["latitude"])
            data["lon"] = float(geo["longitude"])
        agg = jd.get("aggregateRating", {}) or {}
        if agg.get("ratingValue") and "rating" not in data:
            data["rating"] = float(agg.get("ratingValue", 0) or 0)
            data["review_count"] = int(agg.get("reviewCount", 0) or 0)
        if jd.get("review") and "reviews" not in data:
            reviews = []
            for rv in jd["review"] or []:
                author = rv.get("author")
                if not isinstance(author, str):
                    author = (author or {}).get("name") if isinstance(author, dict) else None
                reviews.append({
                    "author": author,
                    "date": rv.get("datePublished"),
                    "body": (rv.get("reviewBody") or "").strip(),
                    "rating": float((rv.get("reviewRating", {}) or {}).get("ratingValue", 0) or 0),
                })
            data["reviews"] = reviews
        img = jd.get("image")
        if img and isinstance(img, str) and "navily" in img and "image" not in data:
            data["image"] = img
        phone = jd.get("telephone")
        if phone and "phone" not in data:
            data["phone"] = phone

    og_img = re.search(r'<meta property="og:image"\s+content="([^"]+)"', html)
    if og_img and "navily" in og_img.group(1):
        data.setdefault("image", og_img.group(1))

    if "name" not in data:
        og_t = re.search(r'<meta property="og:title"\s+content="([^"]+)"', html)
        if og_t:
            t = re.sub(r'^(Anchorage|Marina|Port)\s+', '', og_t.group(1))
            t = re.sub(r'\s+(on|sur)\s+Navily\s*$', '', t)
            data["name"] = t.strip()
        elif data.get("slug"):
            data["name"] = data["slug"].replace('-', ' ').title()

    if "lat" not in data:
        dms = re.search(r"(\d+)°\s*([0-9.]+)(?:&#039;|'|&apos;)?\s*([NS])\s*,?\s*(\d+)°\s*([0-9.]+)(?:&#039;|'|&apos;)?\s*([EW])", html)
        if dms:
            lat = int(dms.group(1)) + float(dms.group(2)) / 60
            if dms.group(3) == "S": lat = -lat
            lon = int(dms.group(4)) + float(dms.group(5)) / 60
            if dms.group(6) == "W": lon = -lon
            data["lat"] = round(lat, 5)
            data["lon"] = round(lon, 5)

    body_html = re.sub(r'<script.*?</script>', '', html, flags=re.S)
    body_html = re.sub(r'<style.*?</style>', '', body_html, flags=re.S)
    body_m = re.search(r'<body[^>]*>(.*)</body>', body_html, re.S)
    body = body_m.group(1) if body_m else body_html
    text = re.sub(r'<[^>]+>', ' ', body)
    text = text.replace('&#039;', "'").replace('&amp;', '&').replace('&nbsp;', ' ')
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    sm = re.search(r"types of seabed at.{0,400}", text)
    if sm:
        chunk = sm.group(0)
        found = [t for t in SEABED_TERMS if re.search(r'(?<![A-Za-z])'+t+r'(?![A-Za-z])', chunk)]
        if found:
            data["seabed"] = found

    svc_terms = ["Reachable by dinghy", "Snack", "Beach", "Water", "Dock", "Fuel", "Wifi", "Restaurant",
                 "Shower", "Toilet", "Electricity", "Shop", "Supermarket", "Crane", "Chandlery", "Laundry",
                 "Pumpout", "Waste", "Marine mechanic", "Customs", "Taxi", "ATM"]
    services_found = [t for t in svc_terms if re.search(r'(?<![A-Za-z])'+re.escape(t)+r'(?![A-Za-z])', text)]
    if services_found:
        data["services"] = services_found

    rm = re.search(r'N°\s*(\d+)\s+in\s+([A-Za-z ]+)', text)
    if rm:
        data["rank"] = {"position": int(rm.group(1)), "area": rm.group(2).strip()}

    return data


def load_urls(path):
    urls = []
    if not os.path.exists(path):
        return urls
    for line in open(path):
        line = line.strip()
        if line and not line.startswith('#'):
            urls.append(line)
    return urls


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    urls_path = os.path.join(root, "navily_urls.txt")
    data_dir = os.path.join(root, "data")
    cache_path = os.path.join(data_dir, "navily.json")
    harbors_path = os.path.join(data_dir, "harbors.json")

    candidates = load_urls(urls_path)
    if not candidates:
        print(f"no URLs in {urls_path} — skipping Navily fetch")
        if os.path.exists(harbors_path):
            with open(harbors_path) as fh:
                hs = json.load(fh)
            for h in hs:
                h["navily"] = []
            with open(harbors_path, "w") as fh:
                json.dump(hs, fh, indent=2)
        return

    navily = {}
    if os.path.exists(cache_path):
        try:
            navily = {int(k): v for k, v in json.load(open(cache_path)).items()}
        except Exception:
            navily = {}

    for url in candidates:
        m = re.search(r'/(\d+)(?:$|\?)', url)
        if m and int(m.group(1)) in navily:
            continue
        html = fetch_wayback(url)
        if not html:
            continue
        parsed = parse_page(url, html)
        if "lat" in parsed and "name" in parsed:
            navily[parsed["navily_id"]] = parsed
            print(f"  OK #{parsed['navily_id']:<6} {parsed['name']} ({parsed['lat']:.4f},{parsed['lon']:.4f})")
            with open(cache_path, "w") as fh:
                json.dump(navily, fh, indent=2)
        else:
            print(f"  SKIP {url}")
        time.sleep(3.0)

    # Match harbors
    with open(harbors_path) as fh:
        harbors = json.load(fh)
    for h in harbors:
        h["navily"] = []
    for nid, nv in navily.items():
        for h in harbors:
            d = haversine_km((nv["lat"], nv["lon"]), (h["lat"], h["lon"]))
            if d < 3.0:
                h["navily"].append({
                    "id": nid,
                    "kind": nv["kind"],
                    "name": nv["name"],
                    "distance_km": round(d, 2),
                    "url": nv["url"],
                })

    with open(cache_path, "w") as fh:
        json.dump(navily, fh, indent=2)
    with open(harbors_path, "w") as fh:
        json.dump(harbors, fh, indent=2)

    matched = sum(1 for h in harbors if h["navily"])
    print(f"{len(navily)} Navily records, {matched}/{len(harbors)} harbours matched")


if __name__ == "__main__":
    main()
