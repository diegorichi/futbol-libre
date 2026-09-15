PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Cada entorno puede sobrescribir estas variables antes de ejecutar el script.
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env}"
ENV_VENV_PATH=""
if [ -f "$ENV_FILE" ]; then
    ENV_VENV_PATH="$(sed -n 's/^[[:space:]]*VENV_PATH[[:space:]]*=[[:space:]]*//p' "$ENV_FILE" | tail -n 1)"
    ENV_VENV_PATH="${ENV_VENV_PATH#\"}"
    ENV_VENV_PATH="${ENV_VENV_PATH%\"}"
fi
VENV_PATH="${VENV_PATH:-${ENV_VENV_PATH:-$PROJECT_ROOT/.venv}}"
if [ -x "${VENV_PATH:-}/bin/python3" ]; then
    PYTHON_VENV="${VENV_PATH}/bin/python3"
    SERVER_ENVIRONMENT=1
elif [ -x "$PROJECT_ROOT/.venv/bin/python3" ]; then
    PYTHON_VENV="$PROJECT_ROOT/.venv/bin/python3"
    SERVER_ENVIRONMENT=0
else
    PYTHON_VENV="$(command -v python3)"
    SERVER_ENVIRONMENT=0
fi

if [ "$SERVER_ENVIRONMENT" -eq 1 ]; then
    DEFAULT_LOG_LOCATION="/var/log"
else
    DEFAULT_LOG_LOCATION="$PROJECT_ROOT/logs"
fi

ENV_LOG_LOCATION=""
if [ -f "$ENV_FILE" ]; then
    ENV_LOG_LOCATION="$(sed -n 's/^[[:space:]]*LOG_LOCATION[[:space:]]*=[[:space:]]*//p' "$ENV_FILE" | tail -n 1)"
    ENV_LOG_LOCATION="${ENV_LOG_LOCATION#\"}"
    ENV_LOG_LOCATION="${ENV_LOG_LOCATION%\"}"
fi
LOG_LOCATION="${LOG_LOCATION:-${ENV_LOG_LOCATION:-$DEFAULT_LOG_LOCATION}}"
mkdir -p "$PROJECT_ROOT/data" "$LOG_LOCATION"

export ENV_FILE PYTHON_VENV PROJECT_ROOT LOG_LOCATION

CHROME_FILENAME=google-chrome-stable_current_amd64.deb
CHROME_PACKAGE_URL=https://dl.google.com/linux/direct/$CHROME_FILENAME

LOG_FILE="$LOG_LOCATION/log_scrap.log"
LOG_AGENDA="$LOG_LOCATION/agenda.log"
