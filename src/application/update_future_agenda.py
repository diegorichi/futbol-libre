"""Actualiza la agenda futura sin modificar la agenda de hoy."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from dotenv import dotenv_values

from infrastructure.logging_config import LoggingConfigurator
from scraping.future_agenda_merge import MixedFutureAgendaScraper
from scraping.future_agenda_scraper import DEFAULT_AGENDA_URL, FutureAgendaScraper
from scraping.tyc_future_agenda_scraper import DEFAULT_TYC_AGENDA_URL, TycFutureAgendaScraper


LOGGER = logging.getLogger(__name__)


class FutureAgendaUpdater:
    def __init__(self, scraper=None, output_path=None):
        env_path = Path(os.getenv("ENV_FILE", ".env"))
        if not env_path.is_absolute():
            env_path = Path.cwd() / env_path
        config = dotenv_values(env_path)
        source_url = os.getenv("FUTURE_AGENDA_URL") or config.get("FUTURE_AGENDA_URL") or DEFAULT_AGENDA_URL
        tyc_source_url = os.getenv("FUTURE_AGENDA_TYC_URL") or config.get("FUTURE_AGENDA_TYC_URL") or DEFAULT_TYC_AGENDA_URL
        configured_output = os.getenv("FUTURE_AGENDA_FILE") or config.get("FUTURE_AGENDA_FILE") or "data/agenda_future.json"
        self.scraper = scraper or MixedFutureAgendaScraper(
            TycFutureAgendaScraper(tyc_source_url),
            FutureAgendaScraper(source_url),
        )
        self.output_path = Path(output_path or configured_output)
        if not self.output_path.is_absolute():
            self.output_path = env_path.parent / self.output_path

    def run(self):
        LoggingConfigurator().configure()
        events = self.scraper.fetch()
        if not events:
            raise RuntimeError("La fuente no entregó eventos futuros; se conserva la agenda anterior.")
        payload = {
            "api_version": "v1",
            "generated_at": datetime.now().isoformat(),
            "source": self.scraper.url,
            "sources": getattr(self.scraper, "urls", [self.scraper.url]),
            "events": events,
        }
        self._atomic_write(payload)
        LOGGER.info("Agenda futura actualizada: %s eventos en %s", len(events), self.output_path)
        return events

    def _atomic_write(self, payload):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.output_path.parent, delete=False) as temporary:
            json.dump(payload, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, self.output_path)


if __name__ == "__main__":
    FutureAgendaUpdater().run()
