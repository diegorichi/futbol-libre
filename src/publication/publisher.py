"""Publicadores de los catálogos generados."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.sax.saxutils import escape
from publication.catalog_store import CatalogStore
from domain.time import EventClock
from scraping.event_matching import normalizar_nombre


class OutputPublisher:
    """Serializa cada salida pública; no contiene scraping ni reglas de negocio."""

    def __init__(self, max_channels=100):
        self.max_channels = max_channels
        self.clock = EventClock()

    @staticmethod
    def _atomic_write(path, content):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)

    def publish_catalog(self, events, json_path, xml_path, m3u_path, user_agent, placeholder_url):
        """Persiste el JSON y deriva XML/M3U exclusivamente desde ese JSON."""
        CatalogStore(json_path).write({"api_version": "v1", "events": events})
        document = CatalogStore(json_path).read()
        playlist, guide = self._legacy_projections(document, user_agent, placeholder_url)
        self._atomic_write(xml_path, self._xml_text(guide))
        self._atomic_write(m3u_path, playlist)

    def publish_agenda_from_catalog(self, json_path, path, now=None, preserve_path=None):
        """Deriva la agenda web del mismo documento canónico que XML/M3U."""
        document = CatalogStore(json_path).read()
        events = [
            {
                "hora": self._visible_time(event),
                "nombre": event.title,
                "opciones": [{"canal": source.name} for source in event.sources],
            }
            for event in document.events
        ]
        self.publish_agenda(events, path, now=now, preserve_path=preserve_path)

    def publish_agenda_from_events(self, events, path, now=None, preserve_path=None):
        """Publica la agenda desde todos los eventos detectados del día.

        No usa el catálogo de TV porque ese catálogo está limitado a la
        ventana de reproducción de la grilla.
        """
        agenda_events = [
            {
                "hora": event.get("hora"),
                "nombre": event.get("nombre"),
                "opciones": event.get("opciones", []),
            }
            for event in events
        ]
        self.publish_agenda(agenda_events, path, now=now, preserve_path=preserve_path)

    def _legacy_projections(self, document, user_agent, placeholder_url):
        playlist, guide = "#EXTM3U\n", []
        slot = 0
        for event in document.events:
            sources = event.sources if event.status == "available" else ()
            if not sources:
                sources = (None,)
            for source in sources:
                if slot >= self.max_channels:
                    break
                slot += 1
                channel_id = f"E{slot:02d}"
                if source is None:
                    title = f"PROXIMAMENTE: [{self._visible_time(event)}] {event.title}" if event.status == "upcoming" else "Slot Libre - Sin Eventos"
                    link = placeholder_url
                    source_logo = event.logo
                    source_agent = user_agent
                else:
                    title = f"[{self._visible_time(event)}] {event.title} ; {source.name}"
                    link = source.url
                    source_logo = event.logo
                    source_agent = source.user_agent or user_agent
                escaped_logo = escape(source_logo, {'"': "&quot;"})
                escaped_agent = escape(source_agent, {'"': "&quot;"})
                playlist += (
                    f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="Deporte {slot}" '
                    f'tvg-logo="{escaped_logo}" group-title="Futbol Libre",Deporte {slot:02d}\n'
                    f'#EXTVLCOPT:http-user-agent="{escaped_agent}"\n{link}\n'
                )
                guide.append({"slot": channel_id, "nombre_guia": title, "logo": source_logo, "hora_real": self._visible_time(event)})
            if slot >= self.max_channels:
                break
        while slot < self.max_channels:
            slot += 1
            channel_id = f"E{slot:02d}"
            playlist += (
                f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="Deporte {slot}" group-title="Futbol Libre",Deporte {slot:02d}\n'
                f'#EXTVLCOPT:http-user-agent="{user_agent}"\n{placeholder_url}\n'
            )
            guide.append({"slot": channel_id, "nombre_guia": "Slot Libre - Sin Eventos", "logo": "", "hora_real": (datetime.now() - timedelta(minutes=5)).strftime("%H:%M")})
        return playlist, guide

    @staticmethod
    def _visible_time(event):
        try:
            return datetime.fromisoformat(event.starts_at).strftime("%H:%M")
        except (TypeError, ValueError):
            return "23:59"

    def _xml_text(self, guide):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<tv>"]
        for index in range(1, self.max_channels + 1):
            lines += [f'  <channel id="E{index:02d}">', f"    <display-name>Evento {index}</display-name>", "  </channel>"]
        now = datetime.now()
        for event in guide:
            try:
                start = self.clock.nearest(event["hora_real"], now)
            except (TypeError, ValueError):
                start = now
            start_xml = start.strftime("%Y%m%d%H%M%S") + " -0300"
            stop_xml = (start + timedelta(hours=3)).strftime("%Y%m%d%H%M%S") + " -0300"
            title = escape(str(event["nombre_guia"]))
            logo = escape(str(event.get("logo", "")), {"\"": "&quot;"})
            lines += [f'  <programme start="{start_xml}" stop="{stop_xml}" channel="{event["slot"]}">', f'    <title lang="es">{title}</title>', f'    <desc lang="es">{title}</desc>']
            if logo:
                lines.append(f'    <icon src="{logo}" />')
            lines.append("  </programme>")
        lines.append("</tv>")
        return "\n".join(lines)

    def publish_agenda(self, events, path, now=None, preserve_path=None):
        now = now or datetime.now(); grouped = {}
        for event in events:
            try: start = self.clock.nearest(event["hora"], now)
            except (KeyError, TypeError, ValueError): continue
            if start <= now or start.date() != now.date(): continue
            name = (event.get("nombre") or "Evento").strip(); tournament, separator, match = name.partition(":")
            if not separator: tournament, match = "", name
            channels = []
            for option in event.get("opciones", []):
                channel = (option.get("canal") or "").strip()
                if channel and channel not in channels: channels.append(channel)
            grouped[(start.isoformat(), normalizar_nombre(name))] = {"starts_at": start.isoformat(), "date": start.date().isoformat(), "time": start.strftime("%H:%M"), "tournament": tournament.strip(), "match": match.strip(), "channel": ", ".join(channels[:1]) + (", ..." if len(channels) > 1 else "")}
        if preserve_path and Path(preserve_path).exists():
            try:
                for event in json.loads(Path(preserve_path).read_text(encoding="utf-8")).get("events", []):
                    starts_at = event.get("starts_at", "")
                    if starts_at > now.isoformat() and starts_at[:10] == now.date().isoformat():
                        grouped.setdefault((starts_at, normalizar_nombre(event.get("match", ""))), event)
            except (OSError, json.JSONDecodeError): pass
        self._atomic_write(path, json.dumps({"api_version": "v1", "events": sorted(grouped.values(), key=lambda item: item["starts_at"])}, ensure_ascii=False, indent=2) + "\n")
