#!/bin/bash
# Serve the Saronic Gulf Sailing Log locally.
# Usage: bash serve.sh
# Then open http://localhost:8080 in your browser.
cd "$(dirname "$0")"
echo "Serving Saronic Gulf Sailing Log at http://localhost:8080"
echo "Press Ctrl+C to stop"
python3 -m http.server 8080
