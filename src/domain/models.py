"""Contratos tipados que cruzan scraping, publicación y API."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    url: str
    user_agent: str | None = None
    page_url: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any], index: int = 1) -> "Source":
        return cls(
            id=str(raw.get("id") or f"source-{index}"),
            name=str(raw.get("name") or f"Fuente {index}"),
            url=str(raw.get("url") or ""),
            user_agent=raw.get("user_agent"),
            page_url=raw.get("page_url"),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "user_agent": self.user_agent,
            "page_url": self.page_url,
        }


@dataclass(frozen=True)
class CatalogEvent:
    id: str
    title: str
    starts_at: str
    status: str
    logo: str = ""
    sources: tuple[Source, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CatalogEvent":
        sources = tuple(
            Source.from_dict(source, index)
            for index, source in enumerate(raw.get("sources", []), start=1)
            if isinstance(source, dict)
        )
        return cls(
            id=str(raw.get("id") or "event"),
            title=str(raw.get("title") or "Evento"),
            starts_at=str(raw.get("starts_at") or ""),
            status=str(raw.get("status") or "unavailable"),
            logo=str(raw.get("logo") or ""),
            sources=sources,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "starts_at": self.starts_at,
            "status": self.status,
            "logo": self.logo,
            "sources": [source.as_dict() for source in self.sources],
        }


@dataclass(frozen=True)
class EventCatalogDocument:
    api_version: str
    events: tuple[CatalogEvent, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EventCatalogDocument":
        return cls(
            api_version=str(raw.get("api_version") or "v1"),
            events=tuple(
                CatalogEvent.from_dict(event)
                for event in raw.get("events", [])
                if isinstance(event, dict)
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "api_version": self.api_version,
            "events": [event.as_dict() for event in self.events],
        }
