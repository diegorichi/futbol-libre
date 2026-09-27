#!/bin/bash
cd "$(dirname "$0")"

PROJECT_ROOT="$(pwd)"
cleanup_runtime() { "$PROJECT_ROOT/cleanup-runtime.sh" >/dev/null 2>&1 || true; }
trap cleanup_runtime EXIT
source "$PROJECT_ROOT/config/config.sh"

echo "--- Actualizando agenda futura $(date) ---"
PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_VENV" -m application.update_future_agenda
