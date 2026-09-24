"""Recorrido aislado de sitios y agrupación de eventos."""
import logging
from urllib.parse import urlparse
from selenium.common.exceptions import WebDriverException
from .browser_driver import close_browser
from .event_extractor import extraer_eventos
from .event_matching import agrupar_eventos
from .http_fallback import fetch_html, iframe_urls, load_html

LOGGER = logging.getLogger(__name__)


def _same_host(requested_url, current_url):
    return urlparse(requested_url).netloc.lower().removeprefix("www.") == \
        urlparse(current_url).netloc.lower().removeprefix("www.")


class SiteScraper:
    def __init__(self, extractor=extraer_eventos, matcher=agrupar_eventos):
        self.extractor = extractor
        self.matcher = matcher

    def scrape(
        self,
        driver,
        urls,
        progress_callback=None,
        validation_callback=None,
        driver_factory=None,
    ):
        events, sites, errors = [], [], []
        LOGGER.info("Iniciando scraping de %d sitios", len(urls))
        for completed, url in enumerate(urls, start=1):
            phase = "validation"
            current_driver = driver
            try:
                if driver_factory is not None:
                    current_driver = driver_factory()
                LOGGER.debug("Abriendo sitio %s", url)
                current_driver.switch_to.default_content(); current_driver.get(url)
                if not _same_host(url, current_driver.current_url):
                    LOGGER.warning("Selenium redirigió %s -> %s; usando fallback HTTP", url, current_driver.current_url)
                    found, strategy = self._scrape_http_fallback(current_driver, url)
                else:
                    if validation_callback is not None and validation_callback(current_driver):
                        raise WebDriverException("Dominio activo pero sin contenido válido")
                    phase = "scraping"
                    found, strategy = self.extractor(current_driver)
                    if not found:
                        LOGGER.info("Sin eventos vía Selenium en %s; probando fallback HTTP", url)
                        found, strategy = self._scrape_http_fallback(current_driver, url)
                phase = "scraping"
                for event in found:
                    event["fuentes"] = [url]
                    for option in event.get("opciones", []):
                        option["fuente"] = url
                        LOGGER.log(5, "Opción detectada: sitio=%s canal=%s url=%s", url, option.get("canal"), option.get("url"))
                    events.append(event)
                sites.append({"url": url, "estrategia": strategy, "eventos": len(found)})
                LOGGER.info("Sitio %s: %d eventos vía %s", url, len(found), strategy)
            except Exception as error:
                LOGGER.exception("Falló la fase %s de %s", phase, url)
                errors.append({"url": url, "error": str(error), "phase": phase})
                if phase == "scraping":
                    sites.append({"url": url, "estrategia": "error", "eventos": 0})
            finally:
                if driver_factory is not None and current_driver is not None:
                    self._quit_driver(current_driver, url)
            if progress_callback: progress_callback(completed, len(urls), url)
        if driver_factory is None:
            driver.switch_to.default_content()
        grouped = self.matcher(events)
        LOGGER.info("Scraping terminado: %d eventos crudos, %d agrupados", len(events), len(grouped))
        return grouped, sites, errors

    @staticmethod
    def _quit_driver(driver, url):
        LOGGER.debug("Cerrando Chrome aislado de %s", url)
        close_browser(driver)

    def _scrape_http_fallback(self, driver, url):
        html, error = fetch_html(url)
        if error:
            raise WebDriverException(f"Fallback HTTP falló para {url}: {error}")
        load_html(driver, html, url)
        found, strategy = self.extractor(driver)
        if found:
            LOGGER.info("Fallback HTTP en %s: %d eventos vía %s", url, len(found), strategy)
            return found, strategy

        for frame_url in iframe_urls(html, url):
            LOGGER.info("Probando iframe nivel 1: %s", frame_url)
            driver.switch_to.default_content()
            driver.get(frame_url)
            found, strategy = self.extractor(driver)
            if found:
                LOGGER.info("Iframe nivel 1 en %s: %d eventos vía %s", frame_url, len(found), strategy)
                return found, strategy
        LOGGER.info("Fallback HTTP en %s: %d eventos vía %s", url, len(found), strategy)
        return found, strategy
