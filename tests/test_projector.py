from datetime import datetime

from domain.catalog import EventCatalog
from domain.projector import EventProjector


def test_upcoming_event_does_not_reuse_active_event_stream():
    projector = EventProjector(EventCatalog())
    shared_url = "https://source.test/shared-event"
    events = [
        {
            "nombre": "Liga: Activo",
            "hora": "22:30",
            "logo": "",
            "opciones": [{"canal": "Canal", "url": shared_url}],
        },
        {
            "nombre": "Liga: Futuro",
            "hora": "23:00",
            "logo": "",
            "opciones": [{"canal": "Canal", "url": shared_url}],
        },
    ]
    results = {shared_url: ("https://stream.test/live.m3u8", "runtime")}

    published = projector.tv_events(events, results, datetime(2026, 9, 26, 22, 0))

    assert published[0]["status"] == "available"
    assert published[0]["sources"]
    assert published[1]["status"] == "upcoming"
    assert published[1]["sources"] == []
