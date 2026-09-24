"""Agenda futura de TyC Sports extraída desde su HTML semántico."""

import re
from datetime import date as calendar_date, datetime
from html.parser import HTMLParser

import requests

from scraping.future_agenda_scraper import USER_AGENT


DEFAULT_TYC_AGENDA_URL = "https://www.tycsports.com/agenda-deportiva-hoy.html"
MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}
SPORTS = {
    "futbol": "Fútbol",
    "basquet": "Básquet",
    "automovilismo": "Automovilismo",
    "tenis": "Tenis",
    "rugby": "Rugby",
    "voley": "Vóley",
    "boxeo": "Boxeo",
}


def _clean(parts):
    return " ".join("".join(parts).split())


class _TycAgendaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.day_depth = None
        self.day = None
        self.day_heading = None
        self.competition_depth = None
        self.header_depth = None
        self.tournament = ""
        self.sport = ""
        self.item_depth = None
        self.item = None
        self.time_depth = None
        self.teams_depth = None
        self.channels_depth = None
        self.capture = None
        self.capture_parts = []
        self.events = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set(attributes.get("class", "").split())
        if tag == "div":
            self.depth += 1
            if "agenda_results" in classes:
                self.day_depth = self.depth
                self.day = None
            elif "agenda_comp_results" in classes and self.day_depth is not None:
                self.competition_depth = self.depth
                sport_key = attributes.get("data-selectdeporte", "").strip().lower()
                self.sport = SPORTS.get(sport_key, sport_key.replace("-", " ").title())
                self.tournament = ""
            elif "header_comp_agenda" in classes:
                self.header_depth = self.depth
            elif "item_agenda" in classes and self.day is not None:
                self.item_depth = self.depth
                self.item = {"time": "", "match": "", "channels": []}
            elif "hs-item-agenda" in classes and self.item is not None:
                self.time_depth = self.depth
                self.capture = "time"
                self.capture_parts = []
            elif "text-teams-agenda" in classes and self.item is not None:
                self.teams_depth = self.depth
            elif "text-channels-agenda" in classes and self.item is not None:
                self.channels_depth = self.depth
        elif tag == "h2" and self.day_depth is not None:
            if "border-bottom" in classes:
                self.capture = "day"
                self.capture_parts = []
            elif self.header_depth is not None:
                self.capture = "tournament"
                self.capture_parts = []
        elif tag == "h3" and self.teams_depth is not None:
            self.capture = "match"
            self.capture_parts = []
        elif tag == "span" and self.channels_depth is not None:
            self.capture = "channel"
            self.capture_parts = []

    def handle_data(self, data):
        if self.capture:
            self.capture_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "h2" and self.capture == "day":
            self.day = self._parse_day(_clean(self.capture_parts))
            self._stop_capture()
        elif tag == "h2" and self.capture == "tournament":
            self.tournament = _clean(self.capture_parts)
            self._stop_capture()
        elif tag == "h3" and self.capture == "match":
            self.item["match"] = _clean(self.capture_parts)
            self._stop_capture()
        elif tag == "span" and self.capture == "channel":
            channel = _clean(self.capture_parts)
            if channel and channel not in self.item["channels"]:
                self.item["channels"].append(channel)
            self._stop_capture()
        elif tag == "div":
            if self.depth == self.time_depth and self.capture == "time":
                self.item["time"] = _clean(self.capture_parts)
                self._stop_capture()
                self.time_depth = None
            if self.depth == self.teams_depth:
                self.teams_depth = None
            if self.depth == self.channels_depth:
                self.channels_depth = None
            if self.depth == self.item_depth:
                self._finish_item()
                self.item_depth = None
                self.item = None
            if self.depth == self.header_depth:
                self.header_depth = None
            if self.depth == self.competition_depth:
                self.competition_depth = None
                self.tournament = ""
                self.sport = ""
            if self.depth == self.day_depth:
                self.day_depth = None
                self.day = None
            self.depth -= 1

    def _stop_capture(self):
        self.capture = None
        self.capture_parts = []

    @staticmethod
    def _parse_day(text):
        match = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+del\s+(\d{4})", text.lower())
        if not match or match.group(2) not in MONTHS:
            raise ValueError(f"Fecha de TyC inválida: {text!r}.")
        return calendar_date(int(match.group(3)), MONTHS[match.group(2)], int(match.group(1)))

    def _finish_item(self):
        if not self.item or not self.day or not re.fullmatch(r"\d{2}:\d{2}", self.item["time"]):
            return
        if not self.item["match"]:
            return
        starts_at = datetime.combine(self.day, datetime.strptime(self.item["time"], "%H:%M").time())
        self.events.append({
            "starts_at": starts_at.isoformat(),
            "date": self.day.isoformat(),
            "time": self.item["time"],
            "sport": self.sport,
            "tournament": self.tournament,
            "match": self.item["match"],
            "channel": ", ".join(self.item["channels"]),
        })


class TycFutureAgendaScraper:
    def __init__(self, url=DEFAULT_TYC_AGENDA_URL, timeout=25, session=None):
        self.url = url
        self.timeout = timeout
        self.session = session or requests

    def fetch(self, today=None):
        response = self.session.get(self.url, headers={"User-Agent": USER_AGENT}, timeout=self.timeout)
        response.raise_for_status()
        response.encoding = "utf-8"
        return self.parse(response.text, today=today)

    @staticmethod
    def parse(html, today=None):
        parser = _TycAgendaParser()
        parser.feed(html)
        today = today or calendar_date.today()
        return sorted(
            (event for event in parser.events if calendar_date.fromisoformat(event["date"]) > today),
            key=lambda event: (event["starts_at"], event["match"]),
        )
