"""Validación de dominios antes del scraping."""
from selenium.common.exceptions import WebDriverException


class SiteValidator:
    MARKERS = ("404", "not found", "page not found", "site not found", "sitio no disponible")

    def is_unavailable(self, driver):
        title = (driver.title or "").lower()
        source = (driver.page_source or "")[:10000].lower()
        return not title or any(marker in title or marker in source for marker in self.MARKERS)

    def validate(self, driver, urls):
        valid, invalid = [], []
        for url in urls:
            try:
                driver.get(url)
                if self.is_unavailable(driver): raise WebDriverException("Dominio activo pero sin contenido válido")
                valid.append(url)
            except Exception as error:
                invalid.append((url, error))
        return valid, invalid

    def without_events(self, urls, sites):
        counts = {site["url"]: site.get("eventos", 0) for site in sites}
        return [url for url in urls if counts.get(url) == 0]
