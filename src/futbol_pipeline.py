"""Caso de uso de actualización de Fútbol Libre."""
import sys
import time
import logging
from pathlib import Path
from selenium.common.exceptions import WebDriverException
from scraping.browser_driver import USER_AGENT, BrowserDriverFactory
from scraping.site_scraper import SiteScraper
from scraping.stream_extractor import StreamExtractionPool
from progress import ProgressReporter
from futbol_events import EventCatalog
from futbol_output import OutputPublisher
from event_projector import EventProjector
from site_validator import SiteValidator
from site_change_notifier import SiteChangeNotifier
from update_config import UpdateConfig
from logging_config import LoggingConfigurator

SINTEL_URL = "https://demo.unified-streaming.com/k8s/live/scte35.isml/.m3u8"
MAX_CHANNELS = 100
LOGGER = logging.getLogger(__name__)


class FootballUpdater:
    """Orquesta etapas; cada responsabilidad técnica vive en un servicio."""

    def __init__(self, config=None, driver_factory=None):
        LoggingConfigurator().configure()
        self.config = config or UpdateConfig.from_environment()
        self.driver_factory = driver_factory or BrowserDriverFactory().create
        self.scraper = SiteScraper()
        self.catalog = EventCatalog(self.config["m3u"], self.config["xml"], SINTEL_URL)
        self.projector = EventProjector(self.catalog)
        self.publisher = OutputPublisher(MAX_CHANNELS)
        self.validator = SiteValidator()
        self.notifier = SiteChangeNotifier(self.config["urls_file"], self.config["ntfy"])

    def run(self, extra_only=False):
        LOGGER.info("Iniciando actualización: extra_only=%s", extra_only)
        driver = self.driver_factory(); pool = None
        progress = ProgressReporter(self.config["progress"]); progress.reset()
        try:
            urls = self._requested_urls(extra_only)
            valid, invalid = self._validate_sites(driver, urls)
            self._require_valid_sites(valid, progress)
            raw, sites = self._scrape(driver, valid, progress)
            active, upcoming = self.projector.classify(raw)
            empty = [] if extra_only else self.validator.without_events(valid, sites)
            self.notifier.notify([url for url in valid if url not in empty], invalid + empty)
            pool, results = self._extract_streams(driver, active)
            events = self.projector.tv_events(raw, results)
            active = [item for item in active if results[item["url"]][0]]
            if extra_only: active, upcoming = self.catalog.merge_extra_site(active, upcoming)
            self._publish(active, upcoming, events, raw, pool, extra_only)
            progress.complete("Actualización completa.")
        except Exception as error:
            progress.fail(str(error)); raise
        finally:
            if pool is not None: pool.close()
            if driver is not None:
                try: driver.quit()
                except WebDriverException: pass

    def _requested_urls(self, extra_only):
        if extra_only:
            if not self.config["extra_url"]: raise RuntimeError("No hay un sitio adicional configurado.")
            return [self.config["extra_url"].strip()]
        return [url.strip() for url in self.config["urls"].split(",") if url.strip()]

    def _validate_sites(self, driver, urls):
        valid, invalid = self.validator.validate(driver, urls)
        for url, error in invalid: print(f"Fallo en {url}: {error}")
        return valid, [url for url, _ in invalid]

    @staticmethod
    def _require_valid_sites(valid, progress):
        if valid: return
        progress.fail("Ningún dominio de la lista está operativo.")
        raise RuntimeError("Ningún dominio de la lista está operativo.")

    def _scrape(self, driver, urls, progress):
        time.sleep(2)
        raw, sites, errors = self.scraper.scrape(driver, urls, progress_callback=lambda done, total, url: progress.update("sites", done, total, f"Sitio parseado: {url}"))
        for error in errors: print(f"Error en {error['url']}: {error['error']}")
        return raw, sites

    def _extract_streams(self, driver, active):
        if self.config["parallel"]:
            driver.quit(); driver = None
        pool = StreamExtractionPool(driver, paralelo=self.config["parallel"], workers=self.config["workers"])
        results = {}
        urls = list(dict.fromkeys(item["url"] for item in active))
        for url in urls: pool.submit(url)
        for url in urls:
            try: results[url] = pool.result(url)
            except Exception as error: print(f"[Stream] Error en {url}: {error}"); results[url] = (None, None)
        return pool, results

    def _publish(self, active, upcoming, events, raw, pool, extra_only):
        playlist, guide = self.publisher.build_playlist(active, upcoming, pool, USER_AGENT, SINTEL_URL)
        m3u = self.config["m3u"]; xml = self.config["xml"] or m3u.replace(".m3u", ".xml"); tv = self.config["events"] or m3u.replace(".m3u", ".json")
        if extra_only: events = self.catalog.merge_tv_events(events, tv)
        self.publisher.publish_xml(guide, xml); Path(m3u).write_text(playlist, encoding="utf-8"); self.publisher.publish_tv_events(events, tv)
        self.publisher.publish_agenda(raw, self.config["agenda"], preserve_path=self.config["agenda"] if extra_only else None)


if __name__ == "__main__":
    FootballUpdater().run(extra_only="--extra-only" in sys.argv[1:])
