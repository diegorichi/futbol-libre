#!/bin/bash
cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"
cleanup_runtime() { "$PROJECT_ROOT/cleanup-runtime.sh" >/dev/null 2>&1 || true; }
trap cleanup_runtime EXIT

source "$(pwd)/config/config.sh"

echo "--- Iniciando proceso de agenda diario $(date) ---"

PYTHONPATH=src $PYTHON_VENV src/agenda.py

echo "--- Proceso finalizado ---"
