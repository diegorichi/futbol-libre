import json
from pathlib import Path

import requests


class AgendaService:
    def __init__(self, env):
        self.events_file = env.get("TV_EVENTS_FILE") or str(Path(env.get("XML_FILE", "data/eventos.xml")).with_suffix(".json"))
        self.ntfy_url = env.get("NTFY_URL")
        self.keys = [key.strip().lower() for key in env.get("KEYS", "").split(",") if key.strip()]

    def events(self):
        events = []
        try:
            payload = json.loads(Path(self.events_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        for event in payload.get("events", []):
            title = event.get("title", "")
            hora = event.get("starts_at", "")
            try:
                hora = hora[11:16]
            except TypeError:
                continue
            if self.keys and not any(key in title.lower() for key in self.keys):
                continue
            tournament, separator, match = title.partition(":")
            if not separator:
                tournament, match = "", title
            channels = ", ".join(source.get("name", "") for source in event.get("sources", []) if source.get("name"))
            events.append({"hora": hora, "torneo": tournament.strip(), "equipos": match.strip(), "canal": channels})
        unique = {f"{event['hora']}_{event['equipos']}": event for event in events}
        return sorted(unique.values(), key=lambda event: event["hora"])

    def update_ntfy(self):
        if not self.ntfy_url:
            return "NTFY no configurado; se omite el envío."
        events = self.events()
        if not events:
            return "No hay eventos para enviar a NTFY."
        message = "\n".join(f"{event['hora']} | {event['equipos']}" for event in events)
        response = requests.post(self.ntfy_url, data=message.encode("utf-8"), headers={"Title": "Grilla Deportiva"}, timeout=30)
        response.raise_for_status()
        return "Actualización enviada a NTFY."
