"""Catálogo y reglas de dominio de eventos."""

import json
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from domain.time import EventClock
from server.services.channel_service import ChannelService


class EventCatalog:
    """Dueño de normalización, tiempo, claves y fusiones del catálogo."""

    def __init__(self, m3u_file=None, xml_file=None, sintel_url=None):
        self.m3u_file = m3u_file
        self.xml_file = xml_file
        self.sintel_url = sintel_url
        self.clock = EventClock()

    @staticmethod
    def nearest_time(value, now=None):
        return EventClock().nearest(value, now)

    def sanitize_name(self, texto):
        if not texto:
            return ""
        texto = unicodedata.normalize("NFKC", texto)
        texto = re.sub(r"[\r\n\t]+", " ", texto)
        return re.sub(r"\s+", " ", texto).strip()

    def is_upcoming(self, hora_str, ahora=None):
        try:
            ahora = ahora or datetime.now()
            hora_obj = self.clock.nearest(hora_str, ahora)
            return (ahora + timedelta(minutes=30)) <= hora_obj or hora_str == "23:59"
        except (TypeError, ValueError):
            return False

    def is_active(self, hora_str, ahora=None):
        try:
            ahora = ahora or datetime.now()
            hora_obj = self.clock.nearest(hora_str, ahora)
            return ahora - timedelta(hours=2, minutes=30) <= hora_obj <= ahora + timedelta(minutes=30)
        except (TypeError, ValueError):
            return False

    def output_key(self, nombre, hora):
        nombre = re.sub(r"^PROXIMAMENTE:\s*", "", nombre or "", flags=re.IGNORECASE)
        nombre = re.sub(r"^\[\d{2}:\d{2}\]\s*", "", nombre)
        nombre = nombre.split(";", 1)[0].strip()
        nombre = unicodedata.normalize("NFKD", nombre)
        nombre = "".join(caracter for caracter in nombre if not unicodedata.combining(caracter))
        return re.sub(r"[^a-zA-Z0-9]+", " ", nombre).strip().lower(), hora

    def _existing_channels(self, m3u_file, xml_file, ahora=None):
        if not m3u_file or not Path(m3u_file).exists():
            return []
        xml_path = xml_file or str(m3u_file).replace(".m3u", ".xml")
        if not Path(xml_path).exists():
            return []
        try:
            return ChannelService(xml_path, m3u_file, now=ahora).list_channels()
        except (OSError, ValueError):
            return []

    def merge_extra_site(self, en_vivo, proximos, m3u_file=None, xml_file=None, sintel_url=None, ahora=None):
        existentes = self._existing_channels(m3u_file or self.m3u_file, xml_file or self.xml_file, ahora)
        if not existentes:
            return en_vivo, proximos
        nuevas_activas = {self.output_key(i.get("nombre"), i.get("hora")) for i in en_vivo}
        en_vivo_nuevo, en_vivo = list(en_vivo), []
        claves_activas, urls_activas = set(), set()
        conservados = 0
        for canal in existentes:
            clave = self.output_key(canal.nombre, canal.hora)
            if canal.proximamente:
                if self.is_active(canal.hora, ahora) or self.is_upcoming(canal.hora, ahora):
                    if clave not in nuevas_activas:
                        proximos.append({"nombre": canal.nombre, "hora": canal.hora, "logo": canal.logo, "opciones": []})
                continue
            if not self.is_active(canal.hora, ahora) or not canal.link or canal.link == (sintel_url or self.sintel_url) or canal.link in urls_activas or clave in nuevas_activas:
                continue
            en_vivo.append({"nombre": f"{canal.torneo}: {canal.match}" if canal.torneo else canal.match, "hora": canal.hora, "canal": canal.canal, "logo": canal.logo, "url": canal.link, "_stream_result": (canal.link, "persistido")})
            urls_activas.add(canal.link)
            claves_activas.add(clave)
            conservados += 1
        for item in en_vivo_nuevo:
            if item.get("url") not in urls_activas:
                en_vivo.append(item)
                urls_activas.add(item.get("url"))
                claves_activas.add(self.output_key(item.get("nombre"), item.get("hora")))
        unicos = []
        claves_proximas = set()
        for evento in proximos:
            clave = self.output_key(evento.get("nombre"), evento.get("hora"))
            if clave not in claves_activas and clave not in claves_proximas:
                claves_proximas.add(clave)
                unicos.append(evento)
        if conservados:
            print(f"Upsert extra: {conservados} canales existentes conservados.")
        return en_vivo, unicos

    def merge_tv_events(self, eventos_tv, events_path, ahora=None):
        if not events_path or not Path(events_path).exists():
            return eventos_tv
        try:
            with open(events_path, encoding="utf-8") as source:
                anteriores = json.load(source).get("events", [])
        except (OSError, json.JSONDecodeError, AttributeError):
            return eventos_tv
        nuevos = {self.output_key(e.get("title"), e.get("starts_at", "")[:16]): e for e in eventos_tv}
        fusionados, claves = [], set()
        for evento in anteriores:
            match = re.search(r"\[(\d{2}:\d{2})\]", evento.get("title", "") or "") or re.search(r"T(\d{2}:\d{2})", evento.get("starts_at", "") or "")
            if not match or not (self.is_active(match.group(1), ahora) or self.is_upcoming(match.group(1), ahora)):
                continue
            clave = self.output_key(evento.get("title"), evento.get("starts_at", "")[:16])
            elegido = nuevos.pop(clave, evento)
            if clave not in claves:
                fusionados.append(elegido)
                claves.add(clave)
        for evento in nuevos.values():
            clave = self.output_key(evento.get("title"), evento.get("starts_at", "")[:16])
            if clave not in claves:
                fusionados.append(evento)
                claves.add(clave)
        return fusionados
