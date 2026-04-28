#!/usr/bin/env python3
"""Bundle index.html with embedded JSON data into a single shareable file.

Usage: python3 scripts/build_standalone.py
  Reads:  index.html, data/trips.json, data/harbors.json, data/navily.json
  Writes: sailing-log.html (single-file, openable directly without a server)
"""
import json, os, re, sys

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))


def main():
    src = os.path.join(ROOT, "index.html")
    out = os.path.join(ROOT, "sailing-log.html")
    data = os.path.join(ROOT, "data")
    if not os.path.exists(src):
        print(f"ERROR: {src} not found")
        sys.exit(1)

    with open(src) as f:
        html = f.read()
    with open(os.path.join(data, "trips.json")) as f:
        trips = f.read()
    with open(os.path.join(data, "harbors.json")) as f:
        harbors = f.read()
    navily_path = os.path.join(data, "navily.json")
    navily = open(navily_path).read() if os.path.exists(navily_path) else "{}"

    inline = (
        "Promise.resolve([\n"
        f"      {trips},\n"
        f"      {harbors},\n"
        f"      {navily}\n"
        "    ])"
    )
    new_html, n = re.subn(r"Promise\.all\(\[[^\]]+\]\)", lambda _: inline, html, count=1, flags=re.S)
    if n != 1:
        print("ERROR: could not find Promise.all data-fetch block in index.html")
        sys.exit(1)

    with open(out, "w") as f:
        f.write(new_html)
    print(f"wrote {out} ({os.path.getsize(out)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
