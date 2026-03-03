#!/usr/bin/env bash
# Run the background worker (for USE_BACKGROUND_JOBS=true deployments)
set -euo pipefail
cd "$(dirname "$0")/../backend"
echo "[worker] Starting background job worker..."
exec python worker.py
