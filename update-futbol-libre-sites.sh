#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"
cleanup_runtime() { "$PROJECT_ROOT/cleanup-runtime.sh" >/dev/null 2>&1 || true; }
trap cleanup_runtime EXIT
source "$(pwd)/config/config.sh"

exec "$PYTHON_VENV" src/search_sites.py
