#!/usr/bin/env python3
"""Bundle log template with embedded JSON data → sailing-log-<voyage>.html.

Usage: python3 scripts/build_standalone.py <voyage-name>
"""
import json, os, re, sys

HERE = os.path.dirname(__file__)
TEMPLATE = os.path.join(HERE, "log_template.html")


def main():
    if len(sys.argv) < 2:
        print("Usage: build_standalone.py <voyage-name>")
        sys.exit(1)
    voyage = sys.argv[1]
    root = os.path.join(HERE, "..", "voyages", voyage)
    data = os.path.join(root, "data")
    out = os.path.join(root, f"sailing-log-{voyage}.html")

    with open(TEMPLATE) as f:
        html = f.read()
    with open(os.path.join(data, "trips.json")) as f: trips = f.read()
    with open(os.path.join(data, "harbors.json")) as f: harbors = f.read()
    navily_path = os.path.join(data, "navily.json")
    navily = open(navily_path).read() if os.path.exists(navily_path) else "{}"

    inline = f"Promise.resolve([\n      {trips},\n      {harbors},\n      {navily}\n    ])"
    html = re.sub(r"Promise\.all\(\[[^\]]+\]\)", lambda _: inline, html, count=1, flags=re.S)
    html = html.replace("Sailing Log — Greek Islands", f"Sailing Log — {voyage}")

    with open(out, "w") as f:
        f.write(html)
    print(f"[{voyage}] wrote {out} ({os.path.getsize(out)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
