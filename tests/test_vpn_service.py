import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from pathlib import Path


class VpnServiceTest(unittest.TestCase):
    def test_disabled_does_not_require_wireguard_or_proxy(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from server.services.vpn_service import VpnService

        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            env.write_text("STREAM_VPN_ENABLED=0\n", encoding="utf-8")
            service = VpnService(env)

        self.assertEqual(service.status()["enabled"], False)
        self.assertEqual(service.status()["available"], False)
        self.assertEqual(service.status()["reason"], "disabled")

    def test_proxy_url_and_ttl_are_read_from_env(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from server.services.vpn_service import VpnService

        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            env.write_text(
                "STREAM_VPN_ENABLED=true\n"
                "STREAM_VPN_PROXY_HOST=192.168.0.149\n"
                "STREAM_VPN_PROXY_PORT=8888\n"
                "STREAM_VPN_TTL_HOURS=6\n",
                encoding="utf-8",
            )
            service = VpnService(env)

        self.assertEqual(service.proxy_url, "http://192.168.0.149:8888")
        self.assertEqual(service.ttl_hours, 6.0)

    def test_resolver_caches_with_expiration_from_fetch(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from server.models.channel import Event, EventSource
        from server.services.vpn_stream_resolver import VpnStreamResolver

        class Channels:
            def events(self):
                return [Event("event-1", "Partido", "", "available", [
                    EventSource("source-1", "ESPN", "https://old.test/live.m3u8", page_url="https://page.test/espn")
                ])]

        vpn = Mock()
        vpn.values = {}
        vpn.ttl_hours = 2
        vpn.status.return_value = {"available": True, "reason": "ready"}

        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            cache = Path(directory) / "vpn-cache.json"
            env.write_text(f"STREAM_VPN_CACHE_FILE={cache}\n", encoding="utf-8")
            resolver = VpnStreamResolver(Channels(), vpn, env)
            resolver._write({"event-1:source-1": {
                "event_id": "event-1", "source_id": "source-1", "url": "https://vpn.test/live.m3u8",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": "2099-01-01T00:00:00+00:00",
            }})
            result = resolver.resolve("event-1", "source-1")

        self.assertEqual(result["url"], "https://vpn.test/live.m3u8")
        vpn.status.assert_not_called()

    def test_activate_runs_wg_quick_before_validation(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from server.services.vpn_service import VpnService

        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            config = Path(directory) / "vpn0.conf"
            config.write_text("[Interface]\n", encoding="utf-8")
            env.write_text(
                f"STREAM_VPN_ENABLED=true\nSTREAM_VPN_CONFIG={config}\n",
                encoding="utf-8",
            )
            service = VpnService(env)
            with patch("server.services.vpn_service.shutil.which", return_value="/usr/bin/wg-quick"), \
                    patch.object(service, "_interface_exists", side_effect=[False, True]), \
                    patch.object(service, "status", return_value={"available": True, "reason": "ready"}) as status, \
                    patch("server.services.vpn_service.subprocess.run") as run:
                run.return_value.returncode = 0
                result = service.activate()

        run.assert_called_once_with(
            ["/usr/bin/wg-quick", "up", str(config)],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        status.assert_called_once()
        self.assertTrue(result["available"])

    def test_capability_is_available_before_tunnel_is_up(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from server.services.vpn_service import VpnService

        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            config = Path(directory) / "vpn0.conf"
            config.write_text("[Interface]\n", encoding="utf-8")
            env.write_text(f"STREAM_VPN_ENABLED=true\nSTREAM_VPN_CONFIG={config}\n", encoding="utf-8")
            service = VpnService(env)
            with patch("server.services.vpn_service.shutil.which", return_value="/usr/bin/wg-quick"), \
                    patch.object(service, "_proxy_accepts_connections", return_value=True), \
                    patch.object(service, "_interface_exists", return_value=False):
                result = service.capability()

        self.assertTrue(result["available"])
        self.assertEqual(result["reason"], "ready_to_activate")
