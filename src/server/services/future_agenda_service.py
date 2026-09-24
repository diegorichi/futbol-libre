import json
from datetime import datetime
from pathlib import Path


class FutureAgendaService:
    def __init__(self, path, now=None):
        self.path = Path(path)
        self.now = now or datetime.now()

    def events(self):
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        events = []
        for event in payload.get("events", []):
            try:
                starts_at = datetime.fromisoformat(event["starts_at"])
            except (KeyError, TypeError, ValueError):
                continue
            if event.get("date") == starts_at.date().isoformat() and starts_at.date() > self.now.date():
                events.append(event)
        return sorted(events, key=lambda event: event["starts_at"])
