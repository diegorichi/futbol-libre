#!/bin/bash
cd "$(dirname "$0")"

PROJECT_ROOT="$(pwd)"
if command -v flock >/dev/null 2>&1; then
    exec 9>"$PROJECT_ROOT/data/.update-futbollibre.lock"
    if ! flock -n 9; then
        echo "Ya hay otra actualización de Fútbol Libre en curso."
        exit 2
    fi
fi

source "$(pwd)/config/config.sh"

echo "--- Iniciando proceso diario $(date) ---"

PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_VENV" -m application.update_catalog "$@"
return_code=$?

if [ "$return_code" -eq 0 ]; then
    echo "--- Proceso finalizado ---"
else
    echo "--- Proceso finalizado con error (Código $return_code) ---"
fi
exit "$return_code"
