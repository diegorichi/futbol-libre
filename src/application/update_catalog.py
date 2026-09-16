"""Caso de uso principal: descubrir eventos y publicar el catálogo."""

import logging
import sys
from selenium.common import WebDriverException

from scraping.browser_driver import USER_AGENT, BrowserDriverFactory
from scraping.site_scraper import SiteScraper
from scraping.stream_extractor import StreamExtractionPool
from infrastructure.progress import ProgressReporter
from domain.catalog import EventCatalog
from publication.publisher import OutputPublisher
from domain.projector import EventProjector
from scraping.site_validator import SiteValidator
from integrations.site_change_notifier import SiteChangeNotifier
from infrastructure.config import UpdateConfig
from infrastructure.logging_config import LoggingConfigurator
from integrations.threadfin import ThreadfinRefresher
from server.services.vpn_stream_resolver import VpnStreamResolver


SINTEL_URL = "https://demo.unified-streaming.com/k8s/live/scte35.isml/.m3u8"
MAX_CHANNELS = 100
LOGGER = logging.getLogger(__name__)


class FootballUpdater:
    """Orquesta el caso de uso; infraestructura y publicación son adaptadores."""

    def __init__(self, config=None, driver_factory=None, scraper=None, publisher=None, threadfin=None):
        LoggingConfigurator().configure()
        self.config = config or UpdateConfig.from_environment()
        self.driver_factory = driver_factory or BrowserDriverFactory().create
        self.scraper = scraper or SiteScraper()
        self.catalog = EventCatalog(self.config["m3u"], self.config["xml"], SINTEL_URL)
        self.projector = EventProjector(self.catalog)
        self.publisher = publisher or OutputPublisher(MAX_CHANNELS)
        self.validator = SiteValidator()
        self.notifier = SiteChangeNotifier(self.config["urls_file"], self.config["ntfy"])
        self.threadfin = threadfin or ThreadfinRefresher(self.config["threadfin"])

    def run(self, extra_only=False):
        LOGGER.info("Iniciando actualización: extra_only=%s", extra_only)
        driver = self.driver_factory()
        pool = None
        progress = ProgressReporter(self.config["progress"])
        progress.reset()
        try:
            urls = self._requested_urls(extra_only)
            raw, sites, valid, invalid = self._scrape(driver, urls, progress)
            self._require_valid_sites(valid, progress)
            active, _upcoming = self.projector.classify(raw)
            empty = [] if extra_only else self.validator.without_events(valid, sites)
            self.notifier.notify([url for url in valid if url not in empty], invalid + empty)
            pool, results = self._extract_streams(driver, active, progress)
            events = self.projector.tv_events(raw, results)
            self._publish(events, raw, extra_only)
            progress.complete("Actualización completa.")
        except Exception as error:
            progress.fail(str(error))
            raise
        finally:
            if pool is not None:
                pool.close()
            if driver is not None:
                try:
                    driver.quit()
                except WebDriverException:
                    pass

    def _requested_urls(self, extra_only):
        if extra_only:
            if not self.config["extra_url"]:
                raise RuntimeError("No hay un sitio adicional configurado.")
            return [self.config["extra_url"].strip()]
        return [url.strip() for url in self.config["urls"].split(",") if url.strip()]

    @staticmethod
    def _require_valid_sites(valid, progress):
        if valid:
            return
        progress.fail("Ningún dominio de la lista está operativo.")
        raise RuntimeError("Ningún dominio de la lista está operativo.")

    def _scrape(self, driver, urls, progress):
        progress.update("sites", 0, len(urls), "Iniciando parseo de sitios...")
        raw, sites, errors = self.scraper.scrape(
            driver,
            urls,
            validation_callback=self.validator.is_unavailable,
            progress_callback=lambda done, total, url: progress.update("sites", done, total, f"Sitio procesado: {url}"),
        )
        for error in errors:
            LOGGER.error("Fallo en %s: %s", error["url"], error["error"])
        valid = [site["url"] for site in sites]
        invalid = [error["url"] for error in errors if error.get("phase") == "validation"]
        return raw, sites, valid, invalid

    def _extract_streams(self, driver, active, progress):
        urls = list(dict.fromkeys(item["url"] for item in active))
        progress.update("streams", 0, len(urls), "Iniciando extracción de m3u8...")
        if self.config["parallel"]:
            driver.quit()
            driver = None
        pool = StreamExtractionPool(
            driver,
            paralelo=self.config["parallel"],
            workers=self.config["workers"],
            progress_total=len(urls),
            progress_callback=lambda done, total, url: progress.update("streams", done, total, f"Stream procesado: {done}/{total} ({url})"),
        )
        results = {}
        for url in urls:
            pool.submit(url)
        for url in urls:
            try:
                results[url] = pool.result(url)
            except Exception as error:
                LOGGER.error("Error extrayendo %s: %s", url, error)
                results[url] = (None, None)
        return pool, results

    def _publish(self, events, raw_events, extra_only):
        m3u = self.config["m3u"]
        xml = self.config["xml"] or m3u.replace(".m3u", ".xml")
        tv = self.config["events"] or m3u.replace(".m3u", ".json")
        if extra_only:
            events = self.catalog.merge_tv_events(events, tv)
        self.publisher.publish_catalog(events, tv, xml, m3u, USER_AGENT, SINTEL_URL)
        self.publisher.publish_agenda_from_events(
            raw_events,
            self.config["agenda"],
            preserve_path=self.config["agenda"] if extra_only else None,
        )
        self.threadfin.refresh()
        VpnStreamResolver.invalidate_cache(self.config["vpn_cache"])


if __name__ == "__main__":
    FootballUpdater().run(extra_only="--extra-only" in sys.argv[1:])
