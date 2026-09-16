"""Proyecciones de eventos extraídos hacia los contratos de salida."""
import re
from datetime import datetime
from scraping.browser_driver import USER_AGENT
from domain.models import CatalogEvent, Source


class EventProjector:
    def __init__(self, catalog): self.catalog = catalog

    def classify(self, events):
        active, upcoming = [], []
        for event in events:
            event["nombre"] = self.catalog.sanitize_name(event["nombre"])
            event["hora"] = "23:59" if event["hora"] == "00:00" else event["hora"]
            if self.catalog.is_active(event["hora"]):
                active.extend({"nombre": event["nombre"], "hora": event["hora"], "canal": option["canal"], "logo": event["logo"], "url": option["url"]} for option in event["opciones"])
            elif self.catalog.is_upcoming(event["hora"]): upcoming.append(event)
        return active, upcoming

    def tv_events(self, events, stream_results, now=None):
        now = now or datetime.now(); output = []
        for event in events:
            hour = event.get("hora", "23:59")
            if not (self.catalog.is_active(hour, now) or self.catalog.is_upcoming(hour, now)): continue
            sources = []
            for index, option in enumerate(event.get("opciones", []), 1):
                link, origin = stream_results.get(option.get("url"), (None, None))
                if link: sources.append({"id": f"source-{index}", "name": option.get("canal") or origin or f"Fuente {index}", "url": link, "user_agent": USER_AGENT, "page_url": option.get("url")})
            try: starts_at = self.catalog.nearest_time(hour, now).isoformat()
            except (TypeError, ValueError): starts_at = now.isoformat()
            catalog_event = CatalogEvent(
                id=re.sub(r"[^a-z0-9]+", "-", event.get("nombre", "evento").lower()).strip("-") + f"-{hour.replace(':', '')}",
                title=event.get("nombre", "Evento"),
                starts_at=starts_at,
                status="available" if sources else ("upcoming" if self.catalog.is_upcoming(hour, now) else "unavailable"),
                logo=event.get("logo", ""),
                sources=tuple(Source.from_dict(source, index) for index, source in enumerate(sources, start=1)),
            )
            output.append(catalog_event.as_dict())
        return output
