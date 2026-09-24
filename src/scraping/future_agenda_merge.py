"""Fusión conservadora de agendas futuras provenientes de varios medios."""

import re
import unicodedata
from difflib import SequenceMatcher

from scraping.event_matching import normalizar_nombre


REGION_MARKERS = {"ba", "re", "se", "lp", "m", "u", "p"}
TEAM_EXPANSIONS = {"dep": "deportivo", "sp": "sportivo", "at": "atletico"}
TEAM_ALIASES = {
    "rep de corea": "corea del sur",
    "republica de corea": "corea del sur",
    "ee uu": "estados unidos",
    "eeuu": "estados unidos",
    "usa": "estados unidos",
}
TOURNAMENT_CATEGORIES = {"femenina", "reserva", "juvenil", "sub"}


def _tokens(value):
    normalized = normalizar_nombre(value)
    normalized = TEAM_ALIASES.get(normalized, normalized)
    result = []
    for token in normalized.split():
        token = TEAM_EXPANSIONS.get(token, token)
        if token in {"de", "del", "la", "el", "club", "fc"} or token in REGION_MARKERS:
            continue
        result.append(token[:-1] if len(token) > 5 and token.endswith("s") else token)
    return result


def _teams(match):
    normalized = normalizar_nombre(match)
    parts = re.split(r"\bvs\b", normalized, maxsplit=1)
    return tuple(_tokens(part) for part in parts) if len(parts) == 2 else ()


def _similar_tokens(left, right):
    if not left or not right:
        return False
    if left == right:
        return True
    left_set, right_set = set(left), set(right)
    if left_set <= right_set or right_set <= left_set:
        return True
    return SequenceMatcher(None, " ".join(left), " ".join(right)).ratio() >= 0.74


def _similar_tournament(left, right):
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    if not left_tokens or not right_tokens:
        return True
    left_set, right_set = set(left_tokens), set(right_tokens)
    if (left_set & TOURNAMENT_CATEGORIES) != (right_set & TOURNAMENT_CATEGORIES):
        return False
    overlap = len(left_set & right_set) / min(len(left_set), len(right_set))
    return overlap >= 0.5 or SequenceMatcher(None, " ".join(left_tokens), " ".join(right_tokens)).ratio() >= 0.7


def equivalent(left, right):
    if left.get("starts_at") != right.get("starts_at"):
        return False
    if not _similar_tournament(left.get("tournament", ""), right.get("tournament", "")):
        return False
    left_teams, right_teams = _teams(left.get("match", "")), _teams(right.get("match", ""))
    if not left_teams or not right_teams:
        return normalizar_nombre(left.get("match", "")) == normalizar_nombre(right.get("match", ""))
    return all(_similar_tokens(a, b) for a, b in zip(left_teams, right_teams))


def _channels(value):
    return [channel.strip() for channel in (value or "").split(",") if channel.strip()]


def _channel_key(channel):
    normalized = unicodedata.normalize("NFKD", channel or "")
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    normalized = re.sub(r"\s*\+\s*", "+", normalized.casefold())
    return re.sub(r"\s+", " ", normalized).strip()


def _merge_channels(left, right):
    result = []
    keys = set()
    for channel in _channels(left) + _channels(right):
        key = _channel_key(channel)
        if key and key not in keys:
            result.append(channel)
            keys.add(key)
    return ", ".join(result)


def merge_future_agendas(*agendas):
    merged = []
    for agenda in agendas:
        for event in agenda:
            existing = next((candidate for candidate in merged if equivalent(candidate, event)), None)
            if existing is None:
                merged.append(dict(event))
                continue
            existing["channel"] = _merge_channels(existing.get("channel"), event.get("channel"))
            if not existing.get("sport") and event.get("sport"):
                existing["sport"] = event["sport"]
            if not existing.get("tournament") and event.get("tournament"):
                existing["tournament"] = event["tournament"]
    return sorted(merged, key=lambda event: (event["starts_at"], event["match"]))


class MixedFutureAgendaScraper:
    def __init__(self, *scrapers):
        self.scrapers = scrapers
        self.urls = [scraper.url for scraper in scrapers]
        self.url = self.urls[0]

    def fetch(self, today=None):
        return merge_future_agendas(*(scraper.fetch(today=today) for scraper in self.scrapers))
