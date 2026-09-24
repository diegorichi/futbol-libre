"""Extracción de agenda deportiva futura desde JSON estructurado."""

import json
from datetime import date as calendar_date, datetime
from html.parser import HTMLParser

import requests


DEFAULT_AGENDA_URL = "https://www.clarin.com/deportes/agenda-deportiva"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"


class _NextDataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._capturing = False
        self._parts = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and attributes.get("id") == "__NEXT_DATA__":
            self._capturing = True

    def handle_data(self, data):
        if self._capturing:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._capturing:
            self._capturing = False

    def payload(self):
        if not self._parts:
            raise ValueError("La fuente no contiene __NEXT_DATA__.")
        return json.loads("".join(self._parts))


class FutureAgendaScraper:
    """Lee fechas explícitas; nunca infiere el día a partir de una hora."""

    def __init__(self, url=DEFAULT_AGENDA_URL, timeout=25, session=None):
        self.url = url
        self.timeout = timeout
        self.session = session or requests

    def fetch(self, today=None):
        response = self.session.get(
            self.url,
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return self.parse(response.text, today=today)

    @staticmethod
    def parse(html, today=None):
        parser = _NextDataParser()
        parser.feed(html)
        document = parser.payload()
        try:
            data = document["props"]["pageProps"]["matchConfig"]["properties"]["service"]["data"]
            dates = data["dates"]
        except (KeyError, TypeError) as error:
            raise ValueError("Cambió el contrato de la agenda futura.") from error

        today = today or calendar_date.today()
        events = []
        for day in dates:
            date = day.get("fecha")
            if not date:
                continue
            try:
                day_date = calendar_date.fromisoformat(date)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Fecha de agenda inválida: {date!r}.") from error
            if day_date <= today:
                continue
            for tournament in day.get("torneos", []):
                tournament_name = (tournament.get("nombre") or "").strip()
                tournament_sport = (tournament.get("deporte") or {}).get("nombre") or ""
                for event in tournament.get("eventos", []):
                    starts_at = FutureAgendaScraper._starts_at(event, date)
                    if starts_at.date().isoformat() != date:
                        continue
                    sport = ((event.get("deporte") or {}).get("nombre") or tournament_sport).strip()
                    channels = []
                    for channel in event.get("canales", []):
                        name = (channel.get("nombre") or "").strip()
                        if name and name not in channels:
                            channels.append(name)
                    events.append({
                        "starts_at": starts_at.isoformat(),
                        "date": date,
                        "time": starts_at.strftime("%H:%M"),
                        "sport": sport,
                        "tournament": tournament_name,
                        "match": (event.get("nombre") or "Evento").strip(),
                        "channel": ", ".join(channels) or "",
                    })
        return sorted(events, key=lambda item: (item["starts_at"], item["match"]))

    @staticmethod
    def _starts_at(event, expected_date):
        raw = event.get("fecha")
        if not raw:
            raise ValueError(f"Evento sin fecha explícita para {expected_date}.")
        try:
            return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError) as error:
            raise ValueError(f"Fecha de evento inválida: {raw!r}.") from error
