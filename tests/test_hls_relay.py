import unittest
import time
from unittest.mock import Mock
from server.services.hls_relay import HlsRelay


class HlsRelayTest(unittest.TestCase):
    def setUp(self):

        self.service = Mock(proxy_url="http://vpn-proxy:8888")
        self.session = Mock()
        self.relay = HlsRelay(self.service, session=self.session)

    def test_playlist_urls_are_rewritten_and_fetched_through_proxy(self):
        response = Mock(
            content=b'#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="keys/key.bin"\n#EXTINF:4,\nsegments/one.ts?token=x\n',
            text='#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="keys/key.bin"\n#EXTINF:4,\nsegments/one.ts?token=x\n',
            headers={"Content-Type": "application/vnd.apple.mpegurl"},
        )
        response.raise_for_status.return_value = None
        self.session.get.return_value = response

        body, content_type = self.relay.fetch(
            "event-1", "source-1", "https://cdn.test/live/index.m3u8?session=abc"
        )

        self.assertEqual(content_type, "application/vnd.apple.mpegurl")
        self.assertIn(b"/api/v1/stream-relay/event-1/source-1/", body)
        self.assertNotIn(b"segments/one.ts?token=x", body)
        self.session.get.assert_called_once_with(
            "https://cdn.test/live/index.m3u8?session=abc",
            proxies={"http": "http://vpn-proxy:8888", "https": "http://vpn-proxy:8888"},
            headers={"User-Agent": "Mozilla/5.0 FútbolLibre HLS relay"},
            timeout=(5, 15),
        )

    def test_unknown_resource_is_rejected(self):
        with self.assertRaises(ValueError):
            self.relay.fetch("event-1", "source-1", "https://cdn.test/live/index.m3u8", "missing")

    def test_resources_expire_and_are_deduplicated(self):
        relay = HlsRelay(self.service, session=self.session, resource_ttl_seconds=1, max_resources=2)
        first = relay.register("event-1", "source-1", "https://cdn.test/segment.ts")
        self.assertEqual(first, relay.register("event-1", "source-1", "https://cdn.test/segment.ts"))
        relay.register("event-1", "source-1", "https://cdn.test/other.ts")
        relay.register("event-1", "source-1", "https://cdn.test/third.ts")
        with self.assertRaises(ValueError):
            relay.fetch("event-1", "source-1", "https://cdn.test/segment.ts", first)
        time.sleep(1.01)
        relay.register("event-1", "source-1", "https://cdn.test/fresh.ts")
        self.assertLessEqual(len(relay._resources), 2)
