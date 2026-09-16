"""Estado de la salida VPN/proxy usada para streams bajo demanda."""

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import requests
from dotenv import dotenv_values


class VpnService:
    """Inspecciona una configuración WireGuard y un proxy HTTP local.

    Levanta el túnel solo cuando una operación VPN lo necesita. La
    configuración de WireGuard debe tener ruteo selectivo para el usuario de
    Tinyproxy; este servicio no instala una ruta por defecto global.
    """

    def __init__(self, env_path=None):
        env_path = Path(env_path or os.getenv("ENV_FILE", ".env"))
        if not env_path.is_absolute():
            env_path = Path.cwd() / env_path
        values = dotenv_values(env_path)

        def setting(name, default=""):
            return os.getenv(name) or values.get(name) or default

        self.enabled = setting("STREAM_VPN_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
        self.interface = setting("STREAM_VPN_INTERFACE", "vpn0").strip()
        self.config_path = Path(setting("STREAM_VPN_CONFIG", f"/etc/wireguard/{self.interface}.conf"))
        self.proxy_host = setting("STREAM_VPN_PROXY_HOST", "192.168.0.149").strip()
        self.proxy_port = int(setting("STREAM_VPN_PROXY_PORT", "8888"))
        self.ttl_hours = float(setting("STREAM_VPN_TTL_HOURS", "4"))
        self.handshake_max_age = int(setting("STREAM_VPN_HANDSHAKE_MAX_AGE_SECONDS", "300"))
        self.health_url = setting("STREAM_VPN_HEALTH_URL", "https://api.ipify.org").strip()
        self.values = values

    @property
    def proxy_url(self):
        return f"http://{self.proxy_host}:{self.proxy_port}"

    def status(self):
        if not self.enabled:
            return self._result(False, "disabled")

        if not self.config_path.is_file():
            return self._result(False, "missing_wireguard_config")
        if shutil.which("wg") is None:
            return self._result(False, "wireguard_command_missing")
        if not self._interface_exists():
            return self._result(False, "interface_down")
        if not self._recent_handshake():
            return self._result(False, "stale_handshake")
        if not self._proxy_accepts_connections():
            return self._result(False, "proxy_unreachable")
        if not self._proxy_has_vpn_egress():
            return self._result(False, "proxy_egress_unverified")
        return self._result(True, "ready")

    def capability(self):
        """Indica si la feature puede intentarse aunque el túnel esté abajo."""
        if not self.enabled:
            return self._result(False, "disabled")
        if not self.config_path.is_file():
            return self._result(False, "missing_wireguard_config")
        if shutil.which("wg-quick") is None:
            return self._result(False, "wg_quick_command_missing")
        if not self._proxy_accepts_connections():
            return self._result(False, "proxy_unreachable")
        return self._result(True, "ready_to_activate")

    def activate(self):
        """Levanta el túnel que administra esta feature y valida su salida."""
        if not self.enabled:
            return self._result(False, "disabled")
        if not self._interface_exists():
            command = shutil.which("wg-quick")
            if command is None:
                return self._result(False, "wg_quick_command_missing")
            try:
                result = subprocess.run(
                    [command, "up", str(self.config_path)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError):
                return self._result(False, "activation_failed")
            if result.returncode != 0 and not self._interface_exists():
                return self._result(False, "activation_failed")
        return self.status()

    def deactivate(self):
        """Baja el túnel administrado por esta feature si está levantado."""
        if not self._interface_exists():
            return self._result(False, "interface_down")
        command = shutil.which("wg-quick")
        if command is None:
            return self._result(False, "wg_quick_command_missing")
        try:
            result = subprocess.run(
                [command, "down", str(self.config_path)],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return self._result(False, "deactivation_failed")
        if result.returncode != 0 and self._interface_exists():
            return self._result(False, "deactivation_failed")
        return self._result(False, "interface_down")

    def _result(self, available, reason):
        return {
            "enabled": self.enabled,
            "available": available,
            "reason": reason,
            "interface": self.interface,
            "proxy_url": self.proxy_url if self.enabled else None,
            "ttl_hours": self.ttl_hours,
        }

    def _interface_exists(self):
        return Path("/sys/class/net", self.interface).exists()

    def _recent_handshake(self):
        try:
            result = subprocess.run(
                ["wg", "show", self.interface, "latest-handshakes"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        if result.returncode != 0:
            return False
        now = time.time()
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) == 2 and fields[1].isdigit() and int(fields[1]) > 0:
                if now - int(fields[1]) <= self.handshake_max_age:
                    return True
        return False

    def _proxy_accepts_connections(self):
        try:
            with socket.create_connection((self.proxy_host, self.proxy_port), timeout=2):
                return True
        except OSError:
            return False

    def _proxy_has_vpn_egress(self):
        proxies = {"http": self.proxy_url, "https": self.proxy_url}
        try:
            response = requests.get(self.health_url, proxies=proxies, timeout=5)
            return response.ok and bool(response.text.strip())
        except requests.RequestException:
            return False
