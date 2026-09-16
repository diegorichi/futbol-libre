"""Relay HTTP de playlists HLS y segmentos por el proxy VPN."""

import time
from threading import Lock
from uuid import uuid4
from urllib.parse import urljoin

import requests


class HlsRelay:
    def __init__(self, vpn_service, session=None, resource_ttl_seconds=600, max_resources=4096):
        self.vpn_service = vpn_service
        self.session = session or requests.Session()
        self._resources = {}
        self._lock = Lock()
        self.resource_ttl_seconds = resource_ttl_seconds
        self.max_resources = max_resources

    def register(self, event_id, source_id, url):
        now = time.monotonic()
        key_prefix = (event_id, source_id)
        resource_id = uuid4().hex[:12]
        with self._lock:
            self._cleanup(now)
            for (saved_event, saved_source, saved_id), (saved_url, expires_at) in self._resources.items():
                if (saved_event, saved_source) == key_prefix and saved_url == url and expires_at > now:
                    return saved_id
            self._resources[(event_id, source_id, resource_id)] = (
                url, now + self.resource_ttl_seconds
            )
            while len(self._resources) > self.max_resources:
                del self._resources[next(iter(self._resources))]
        return resource_id

    def fetch(self, event_id, source_id, url, resource_id=None):
        if resource_id:
            with self._lock:
                resource = self._resources.get((event_id, source_id, resource_id))
            if not resource or resource[1] <= time.monotonic():
                raise ValueError("Recurso HLS no encontrado o servidor reiniciado")
            url = resource[0]

        response = self.session.get(
            url,
            proxies={"http": self.vpn_service.proxy_url, "https": self.vpn_service.proxy_url},
            headers={"User-Agent": "Mozilla/5.0 FútbolLibre HLS relay"},
            timeout=(5, 15),
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        base_url = response.url if isinstance(response.url, str) and response.url else url
        if self._is_playlist(base_url, content_type, response.content):
            body = self._rewrite_playlist(response.text, base_url, event_id, source_id)
            return body.encode("utf-8"), "application/vnd.apple.mpegurl"
        return response.content, content_type or "application/octet-stream"

    def _cleanup(self, now):
        expired = [key for key, (_, expires_at) in self._resources.items() if expires_at <= now]
        for key in expired:
            del self._resources[key]

    def _rewrite_playlist(self, playlist, base_url, event_id, source_id):
        rewritten = []
        for line in playlist.splitlines():
            if line.startswith("#"):
                rewritten.append(self._rewrite_uri_attribute(line, base_url, event_id, source_id))
            elif line.strip():
                rewritten.append(self._local_url(event_id, source_id, urljoin(base_url, line.strip())))
            else:
                rewritten.append(line)
        return "\n".join(rewritten) + ("\n" if playlist.endswith("\n") else "")

    def _rewrite_uri_attribute(self, line, base_url, event_id, source_id):
        marker = 'URI="'
        result = line
        start = 0
        while True:
            index = result.find(marker, start)
            if index < 0:
                return result
            value_start = index + len(marker)
            value_end = result.find('"', value_start)
            if value_end < 0:
                return result
            target = urljoin(base_url, result[value_start:value_end])
            replacement = self._local_url(event_id, source_id, target)
            result = result[:value_start] + replacement + result[value_end:]
            start = value_start + len(replacement)

    def _local_url(self, event_id, source_id, upstream_url):
        resource_id = self.register(event_id, source_id, upstream_url)
        return f"/api/v1/stream-relay/{event_id}/{source_id}/{resource_id}"

    @staticmethod
    def _is_playlist(url, content_type, body):
        return (
            "mpegurl" in content_type.lower()
            or url.lower().split("?", 1)[0].endswith((".m3u8", ".m3u"))
            or body.lstrip().startswith(b"#EXTM3U")
        )
