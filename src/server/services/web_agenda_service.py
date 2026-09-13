import json
from datetime import datetime
from pathlib import Path


class WebAgendaService:
    def __init__(self, path, now=None):
        self.path = Path(path)
        self.now = now or datetime.now()

    def events(self):
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        result = []
        for event in payload.get("events", []):
            try:
                starts_at = datetime.fromisoformat(event["starts_at"])
            except (KeyError, TypeError, ValueError):
                continue
            if starts_at > self.now:
                result.append(event)
        return sorted(result, key=lambda event: event["starts_at"])
