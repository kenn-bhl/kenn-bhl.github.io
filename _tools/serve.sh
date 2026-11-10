#!/bin/sh
# Serve the site locally like GitHub Pages: http://localhost:8000
# Usage: sh _tools/serve.sh [port]
PORT="${1:-8000}"
cd "$(dirname "$0")/.." || exit 1
echo "Serving $(pwd) at http://localhost:$PORT (Ctrl+C to stop)"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
