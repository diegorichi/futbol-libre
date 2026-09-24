#!/bin/bash
cd "$(dirname "$0")"

PROJECT_ROOT="$(pwd)"
source "$PROJECT_ROOT/config/config.sh"

echo "--- Actualizando agenda futura $(date) ---"
PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_VENV" -m application.update_future_agenda
