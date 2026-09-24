#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_PATH="${VENV_PATH:-$PROJECT_ROOT/.venv}"
ENV_FILE="$PROJECT_ROOT/.env"

die() { echo "ERROR: $*" >&2; exit 1; }
on_error() { echo "ERROR: instalación fallida en línea $1." >&2; }
trap 'on_error $LINENO' ERR

[[ "$(id -u)" -eq 0 || "$(command -v sudo || true)" ]] || die "Ejecutá como root o instalá sudo."
[[ -f "$PROJECT_ROOT/.env.example" ]] || die "Falta .env.example."
[[ -f "$PROJECT_ROOT/requirements.txt" ]] || die "Falta requirements.txt."
[[ -f "$PROJECT_ROOT/server.sh" ]] || die "Falta server.sh."

cd "$PROJECT_ROOT"
if [[ ! -f "$ENV_FILE" ]]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "Se creó $ENV_FILE desde .env.example. Revisá URLs y secretos."
fi

if [[ "$(id -u)" -eq 0 ]]; then
    APT=(apt-get)
    SUDO=()
else
    command -v sudo >/dev/null 2>&1 || die "Ejecutá como root o instalá sudo."
    APT=(sudo apt-get)
    SUDO=(sudo)
fi

OS_RELEASE_FILE="${OS_RELEASE_FILE:-/etc/os-release}"
[[ -r "$OS_RELEASE_FILE" ]] || die "Este instalador requiere Debian o Ubuntu."
# shellcheck disable=SC1091
source "$OS_RELEASE_FILE"
case "${ID:-}" in
    debian|ubuntu|linuxmint) ;;
    *) die "Distribución no soportada: ${ID:-desconocida}." ;;
esac

ARCH="${INSTALL_ARCH:-$(dpkg --print-architecture 2>/dev/null || true)}"
case "$ARCH" in
    amd64) BROWSER_KIND="google-chrome"; BROWSER_BINARY="/usr/bin/google-chrome" ;;
    arm64) BROWSER_KIND="chromium"; BROWSER_BINARY="/usr/bin/chromium" ;;
    *) die "Arquitectura no soportada para Chrome/Chromium: ${ARCH:-desconocida}." ;;
esac

"${APT[@]}" update
"${APT[@]}" install -y python3 python3-pip python3-venv git curl wget xvfb ffmpeg unzip ca-certificates cron file

if [[ "$BROWSER_KIND" == "google-chrome" ]]; then
    CHROME_DEB="$(mktemp "$PROJECT_ROOT/google-chrome.XXXXXX.deb")"
    trap 'rm -f "$CHROME_DEB"' EXIT
    curl --fail --location --retry 3 --output "$CHROME_DEB" "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    "${APT[@]}" install -y "$CHROME_DEB"
    rm -f "$CHROME_DEB"
    trap - EXIT
else
    "${APT[@]}" install -y chromium chromium-driver
fi

command -v "$BROWSER_KIND" >/dev/null 2>&1 || die "No se encontró $BROWSER_KIND después de instalarlo."
BROWSER_VERSION="$($BROWSER_KIND --version)"
BROWSER_MAJOR="$(printf '%s\n' "$BROWSER_VERSION" | sed -nE 's/[^0-9]*([0-9]+).*/\1/p')"
[[ -n "$BROWSER_MAJOR" ]] || die "No se pudo leer la versión de $BROWSER_KIND: $BROWSER_VERSION"

if [[ "$BROWSER_KIND" == "google-chrome" ]]; then
    DRIVER_VERSION="$(curl --fail --location --retry 3 "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${BROWSER_MAJOR}")"
    DRIVER_ZIP="$(mktemp "$PROJECT_ROOT/chromedriver.XXXXXX.zip")"
    trap 'rm -f "$DRIVER_ZIP"' EXIT
    curl --fail --location --retry 3 --output "$DRIVER_ZIP" "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip"
    DRIVER_TMP="$(mktemp -d)"
    trap 'rm -f "$DRIVER_ZIP"; rm -rf "$DRIVER_TMP"' EXIT
    unzip -q "$DRIVER_ZIP" -d "$DRIVER_TMP"
    "${SUDO[@]}" install -m 0755 "$DRIVER_TMP/chromedriver-linux64/chromedriver" /usr/local/bin/chromedriver
    rm -f "$DRIVER_ZIP"
    rm -rf "$DRIVER_TMP"
    trap - EXIT
else
    command -v chromedriver >/dev/null 2>&1 || die "No se encontró chromedriver para Chromium."
fi

DRIVER_BINARY="$(command -v chromedriver)"
DRIVER_VERSION="$($DRIVER_BINARY --version)"
DRIVER_MAJOR="$(printf '%s\n' "$DRIVER_VERSION" | sed -nE 's/[^0-9]*([0-9]+).*/\1/p')"
[[ "$BROWSER_MAJOR" == "$DRIVER_MAJOR" ]] || die "Versiones incompatibles: browser=$BROWSER_VERSION driver=$DRIVER_VERSION"
MACHINE="$(uname -m)"
case "$ARCH:$MACHINE" in
    amd64:x86_64|arm64:aarch64|arm64:arm64) ;;
    *) die "La arquitectura del sistema ($MACHINE) no coincide con dpkg ($ARCH)." ;;
esac
EXPECTED_ARCH="x86-64"
[[ "$ARCH" == "arm64" ]] && EXPECTED_ARCH="aarch64"
BROWSER_FILE="$(readlink -f "$BROWSER_BINARY")"
DRIVER_FILE="$(readlink -f "$DRIVER_BINARY")"
file "$BROWSER_FILE" | grep -q "$EXPECTED_ARCH" \
    || die "El browser no corresponde a la arquitectura $ARCH."
file "$DRIVER_FILE" | grep -q "$EXPECTED_ARCH" \
    || die "ChromeDriver no corresponde a la arquitectura $ARCH."
echo "Browser verificado: $BROWSER_VERSION"
echo "Driver verificado: $DRIVER_VERSION"
echo "Arquitectura verificada: $ARCH ($MACHINE)"

if [[ ! -x "$VENV_PATH/bin/python" ]]; then
    rm -rf "$VENV_PATH"
    python3 -m venv "$VENV_PATH"
fi
[[ -x "$VENV_PATH/bin/python" ]] || die "No se pudo crear el venv en $VENV_PATH."
"$VENV_PATH/bin/python" -m pip install --upgrade pip
"$VENV_PATH/bin/python" -m pip install -r "$PROJECT_ROOT/requirements.txt"
"$VENV_PATH/bin/python" -c 'import flask, requests, selenium, dotenv, zeroconf; print("Dependencias Python verificadas")'

set_env_value() {
    local key="$1" value="$2"
    if grep -qE "^${key}=" "$ENV_FILE"; then
        sed -i "s|^${key}=.*|${key}=\"${value}\"|" "$ENV_FILE"
    else
        printf '%s\n' "${key}=\"${value}\"" >> "$ENV_FILE"
    fi
}
set_env_value "VENV_PATH" "$VENV_PATH"
set_env_value "CHROME_BINARY" "$BROWSER_BINARY"
set_env_value "CHROMEDRIVER_PATH" "$DRIVER_BINARY"

source "$PROJECT_ROOT/config/config.sh"
chmod +x "$PROJECT_ROOT/server.sh" "$PROJECT_ROOT/update-futbollibre.sh" "$PROJECT_ROOT/update-futbol-libre-sites.sh" "$PROJECT_ROOT/update-future-agenda.sh" "$PROJECT_ROOT/agenda.sh"

ask_yes_no() {
    local prompt="$1" answer=""
    read -r -p "$prompt [s/N] " answer || answer=""
    [[ "$answer" =~ ^[sS]([iI]|í|Í)?$ ]]
}

install_crons() {
    local cron_file current
    command -v crontab >/dev/null 2>&1 || die "crontab no está disponible."
    cron_file="$(mktemp)"
    current="$(crontab -l 2>/dev/null || true)"
    if [[ -n "$current" ]]; then
        printf '%s\n' "$current" \
            | grep -Fv "$PROJECT_ROOT/update-futbollibre.sh" \
            | grep -Fv "$PROJECT_ROOT/update-futbol-libre-sites.sh" \
            | grep -Fv "$PROJECT_ROOT/update-future-agenda.sh" \
            > "$cron_file" || true
    fi
    printf '30 7 * * * /bin/bash %s > %s 2>&1\n' "$PROJECT_ROOT/update-futbol-libre-sites.sh" "$LOG_FILE" >> "$cron_file"
    printf '45 7 * * * /bin/bash %s >> %s 2>&1\n' "$PROJECT_ROOT/update-future-agenda.sh" "$LOG_FILE" >> "$cron_file"
    printf '0 8 * * * /bin/bash %s >> %s 2>&1\n' "$PROJECT_ROOT/update-futbollibre.sh" "$LOG_FILE" >> "$cron_file"
    crontab "$cron_file"
    rm -f "$cron_file"
    echo "Cron instalado."
}

install_service() {
    local service_file service_user
    command -v systemctl >/dev/null 2>&1 || die "systemctl no está disponible en este sistema."
    service_user="${SUDO_USER:-$(id -un)}"
    service_file="/etc/systemd/system/futbol-server.service"
    cat <<EOF | "${SUDO[@]}" tee "$service_file" >/dev/null
[Unit]
Description=Futbol Libre server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$service_user
WorkingDirectory=$PROJECT_ROOT
ExecStart=$PROJECT_ROOT/server.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    "${SUDO[@]}" systemctl daemon-reload
    "${SUDO[@]}" systemctl enable futbol-server.service
    echo "Servicio creado y habilitado, pero no iniciado."
}

if ask_yes_no "¿Deseás instalar los crones?"; then install_crons; else echo "Cron omitido."; fi
if ask_yes_no "¿Deseás crear un servicio persistente para el servidor?"; then install_service; else echo "Servicio persistente omitido."; fi

echo
echo "Instalación completada."
echo "Venv: $VENV_PATH"
echo "Para iniciar el servidor manualmente:"
echo "  cd $PROJECT_ROOT && ./server.sh"
echo "Salud: http://IP_DEL_SERVIDOR:8080/api/v1/health"
echo "Si creaste el servicio, para iniciarlo: sudo systemctl start futbol-server.service"
