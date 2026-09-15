import json
import tempfile
from pathlib import Path

from publication.publisher import OutputPublisher
from server.services.channel_service import ChannelService


def test_json_is_source_of_truth_for_legacy_projections_and_api():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        json_path = root / "events.json"
        xml_path = root / "events.xml"
        m3u_path = root / "events.m3u"
        payload = {"api_version": "v1", "events": [{
            "id": "match-1",
            "title": "Liga: Equipo A vs Equipo B",
            "starts_at": "2026-09-15T20:00:00-03:00",
            "status": "available",
            "logo": "",
            "sources": [{"id": "s1", "name": "ESPN", "url": "https://stream.test/live.m3u8", "user_agent": "UA"}],
        }]}

        OutputPublisher().publish_catalog(payload["events"], json_path, xml_path, m3u_path, "fallback", "https://placeholder.test/live.m3u8")

        events = ChannelService(xml_path, m3u_path, json_path).list_events()
        assert events[0].title == "Liga: Equipo A vs Equipo B"
        assert events[0].sources[0].url == "https://stream.test/live.m3u8"
        assert "https://stream.test/live.m3u8" in m3u_path.read_text(encoding="utf-8")
        assert "Equipo A vs Equipo B" in xml_path.read_text(encoding="utf-8")
        assert json.loads(json_path.read_text(encoding="utf-8"))["events"][0]["sources"][0]["name"] == "ESPN"
