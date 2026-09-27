#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
if [[ -f "$PROJECT_ROOT/config/config.sh" ]]; then
    # Reutiliza LOG_LOCATION/VENV_PATH del despliegue nativo.
    source "$PROJECT_ROOT/config/config.sh"
fi
RUNTIME_TMPDIR="${FUTBOL_RUNTIME_TMPDIR:-/tmp/futbol-runtime}"
SELENIUM_CACHE="${SE_CACHE_PATH:-/tmp/futbol-selenium}"
LOG_LOCATION="${LOG_LOCATION:-$PROJECT_ROOT/logs}"
LOG_RETENTION_DAYS="${LOG_RETENTION_DAYS:-7}"
LOG_MAX_MB="${LOG_MAX_MB:-20}"

# Solo se tocan directorios y logs propios del proyecto.
find "$RUNTIME_TMPDIR" -mindepth 1 -maxdepth 1 -type d -name 'futbol-chrome-*' -mmin +60 -exec rm -rf -- {} + 2>/dev/null || true
find "$(dirname "$RUNTIME_TMPDIR")" -maxdepth 1 -type d -name 'futbol-chrome-*' -mmin +60 -exec rm -rf -- {} + 2>/dev/null || true
if [[ -d "$SELENIUM_CACHE" ]]; then
    find "$SELENIUM_CACHE" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + 2>/dev/null || true
fi

if [[ -d "$LOG_LOCATION" ]]; then
    find "$LOG_LOCATION" -maxdepth 1 -type f -name '*.log' -mtime +"$LOG_RETENTION_DAYS" -delete
    find "$LOG_LOCATION" -maxdepth 1 -type f -name '*.log' -size +"${LOG_MAX_MB}"M -exec truncate -s 0 {} \;
fi
