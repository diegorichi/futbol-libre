"""Recorrido aislado de sitios y agrupación de eventos."""
import logging
from selenium.common.exceptions import WebDriverException
from .event_extractor import extraer_eventos
from .event_matching import agrupar_eventos

LOGGER = logging.getLogger(__name__)


class SiteScraper:
    def __init__(self, extractor=extraer_eventos, matcher=agrupar_eventos):
        self.extractor = extractor
        self.matcher = matcher

    def scrape(self, driver, urls, progress_callback=None, validation_callback=None):
        events, sites, errors = [], [], []
        LOGGER.info("Iniciando scraping de %d sitios", len(urls))
        for completed, url in enumerate(urls, start=1):
            phase = "validation"
            try:
                LOGGER.debug("Abriendo sitio %s", url)
                driver.switch_to.default_content(); driver.get(url)
                if validation_callback is not None and validation_callback(driver):
                    raise WebDriverException("Dominio activo pero sin contenido válido")
                phase = "scraping"
                found, strategy = self.extractor(driver)
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
            if progress_callback: progress_callback(completed, len(urls), url)
        driver.switch_to.default_content()
        grouped = self.matcher(events)
        LOGGER.info("Scraping terminado: %d eventos crudos, %d agrupados", len(events), len(grouped))
        return grouped, sites, errors
