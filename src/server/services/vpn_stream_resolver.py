"""Resuelve y cachea URLs HLS generadas desde la salida VPN."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock

from scraping.browser_driver import BrowserDriverFactory, close_browser
from scraping.stream_extractor import StreamExtractionPool


class VpnStreamResolver:
    def __init__(self, channel_service, vpn_service, env_path=None):
        env_path = Path(env_path or os.getenv("ENV_FILE", ".env"))
        if not env_path.is_absolute():
            env_path = Path.cwd() / env_path
        values = vpn_service.values if hasattr(vpn_service, "values") else {}
        cache_path = os.getenv("STREAM_VPN_CACHE_FILE") or values.get("STREAM_VPN_CACHE_FILE")
        self.cache_path = Path(cache_path or env_path.parent / "data/.vpn-stream-cache.json")
        if not self.cache_path.is_absolute():
            self.cache_path = env_path.parent / self.cache_path
        self.channel_service = channel_service
        self.vpn_service = vpn_service
        self._lock = Lock()

    def resolve(self, event_id, source_id, force=False):
        with self._lock:
            if not force:
                cached = self._read().get(self._key(event_id, source_id))
                if cached and self._not_expired(cached):
                    return cached

            status = self.vpn_service.activate()
            if not status["available"]:
                raise RuntimeError(f"VPN no disponible: {status['reason']}")
            source = self._find_source(event_id, source_id)
            if source is None:
                raise LookupError("Evento o fuente no encontrados")
            if not source.page_url:
                raise RuntimeError("La fuente no tiene URL de página para regenerar el stream")

            driver = BrowserDriverFactory(headless=True, proxy_url=status["proxy_url"]).create()
            try:
                extractor = StreamExtractionPool(driver, espera=8)
                url, origin = extractor.extract_from_link(driver, source.page_url)
            finally:
                close_browser(driver)
            if not url:
                raise RuntimeError("No se encontró un stream HLS por VPN")

            now = datetime.now(timezone.utc)
            entry = {
                "event_id": event_id,
                "source_id": source_id,
                "url": url,
                "origin": origin,
                "fetched_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=self.vpn_service.ttl_hours)).isoformat(),
            }
            cache = self._read()
            cache[self._key(event_id, source_id)] = entry
            self._write(cache)
            return entry

    @staticmethod
    def _key(event_id, source_id):
        return f"{event_id}:{source_id}"

    @staticmethod
    def _not_expired(entry):
        try:
            return datetime.fromisoformat(entry["expires_at"]) > datetime.now(timezone.utc)
        except (KeyError, TypeError, ValueError):
            return False

    def _find_source(self, event_id, source_id):
        for event in self.channel_service.events():
            if event.id != event_id:
                continue
            return next((source for source in event.sources if source.id == source_id), None)
        return None

    def _read(self):
        try:
            with self.cache_path.open(encoding="utf-8") as source:
                payload = json.load(source)
            return payload if isinstance(payload, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write(self, payload):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.cache_path)

    @staticmethod
    def invalidate_cache(cache_path):
        path = Path(cache_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text("{}\n", encoding="utf-8")
        temporary.replace(path)
