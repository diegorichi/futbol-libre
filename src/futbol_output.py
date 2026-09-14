"""Publicadores de los catálogos generados."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape
from event_time import EventClock
from scraping.event_matching import normalizar_nombre


class OutputPublisher:
    """Serializa cada salida pública; no contiene scraping ni reglas de negocio."""

    def __init__(self, max_channels=100):
        self.max_channels = max_channels
        self.clock = EventClock()

    def publish_xml(self, events, path):
        now = datetime.now()
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<tv>"]
        for index in range(1, self.max_channels + 1):
            lines += [f'  <channel id="E{index:02d}">', f"    <display-name>Evento {index}</display-name>", "  </channel>"]
        for event in events:
            try: start = self.clock.nearest(event["hora_real"], now)
            except (TypeError, ValueError): start = now
            start_xml = start.strftime("%Y%m%d%H%M%S") + " -0300"
            stop_xml = (start + timedelta(hours=3)).strftime("%Y%m%d%H%M%S") + " -0300"
            title = escape(str(event["nombre_guia"]))
            logo = escape(str(event.get("logo", "")), {"\"": "&quot;"})
            lines += [f'  <programme start="{start_xml}" stop="{stop_xml}" channel="{event["slot"]}">', f'    <title lang="es">{title}</title>', f'    <desc lang="es">{title}</desc>']
            if logo: lines.append(f'    <icon src="{logo}" />')
            lines.append("  </programme>")
        lines.append("</tv>")
        Path(path).write_text("\n".join(lines), encoding="utf-8")

    def publish_tv_events(self, events, path):
        Path(path).write_text(json.dumps({"api_version": "v1", "events": events}, ensure_ascii=False, indent=2), encoding="utf-8")

    def publish_agenda(self, events, path, now=None, preserve_path=None):
        now = now or datetime.now(); grouped = {}
        for event in events:
            try: start = self.clock.nearest(event["hora"], now)
            except (KeyError, TypeError, ValueError): continue
            if start <= now: continue
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
                    if event.get("starts_at", "") > now.isoformat(): grouped.setdefault((event.get("starts_at"), normalizar_nombre(event.get("match", ""))), event)
            except (OSError, json.JSONDecodeError): pass
        Path(path).write_text(json.dumps({"api_version": "v1", "events": sorted(grouped.values(), key=lambda item: item["starts_at"])}, ensure_ascii=False, indent=2), encoding="utf-8")

    def build_playlist(self, active, upcoming, stream_pool, user_agent, placeholder_url):
        playlist, guide = "#EXTM3U\n", []
        for index in range(1, self.max_channels + 1):
            slot = f"E{index:02d}"
            if active:
                item = active.pop(0)
                try: link, _ = item.get("_stream_result") or stream_pool.result(item["url"])
                except Exception: link = None
                if link: name, hour, logo = f'[{item["hora"]}] {item["nombre"]} ; {item.get("canal", "")}', item["hora"], item.get("logo", "")
                else: name, hour, logo, link = "Slot Libre - Sin Eventos", (datetime.now() - timedelta(minutes=5)).strftime("%H:%M"), "", placeholder_url
            elif upcoming:
                item = upcoming.pop(0); name, hour, logo, link = f'PROXIMAMENTE: [{item["hora"]}] {item["nombre"]}', (datetime.now() - timedelta(minutes=5)).strftime("%H:%M"), item.get("logo", ""), placeholder_url
            else: name, hour, logo, link = "Slot Libre - Sin Eventos", (datetime.now() - timedelta(minutes=5)).strftime("%H:%M"), "", placeholder_url
            guide.append({"slot": slot, "nombre_guia": name, "logo": logo, "hora_real": hour})
            fixed_logo = "https://play-lh.googleusercontent.com/zRe9-Loct_wdUL8uuWMFqElFPhlsLDWYNemkyYNLWdQZhIWQPoWSQ_6o7wzBWB2Y6A=w600-h300-pc0xffffff-pd"
            playlist += f'#EXTINF:-1 tvg-id="{slot}" tvg-name="Deporte {index}" tvg-logo="{fixed_logo}" group-title="Futbol Libre",Deporte {index:02d}\n#EXTVLCOPT:http-user-agent="{user_agent}"\n{link}\n'
        return playlist, guide
