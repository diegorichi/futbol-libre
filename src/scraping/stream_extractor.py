"""Extracción de URLs HLS sin compartir drivers entre workers."""

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from .browser_driver import BrowserDriverFactory

PLAYBACK_URL = re.compile(r"\bplaybackURL\b\s*[:=]\s*[\"'](https?://[^\"']+)[\"']", re.I)
M3U8_URL = re.compile(r"https?://[^\s\"'<>\\]+\.m3u8(?:\?[^\s\"'<>\\]*)?", re.I)
LOGGER = logging.getLogger(__name__)


class StreamExtractionPool:
    """Planifica extracción serial/paralela y encapsula todo el ciclo Selenium."""

    def __init__(self, driver, paralelo=False, workers=2, espera=5, driver_factory=None):
        self.driver = driver
        self.paralelo = paralelo
        self.espera = espera
        self.driver_factory = driver_factory or BrowserDriverFactory().create
        self.executor = ThreadPoolExecutor(max_workers=workers) if paralelo else None
        self.pending, self.results, self.lock = {}, {}, Lock()

    @staticmethod
    def extract_url(text):
        text = (text or "").replace("\\/", "/")
        playback = PLAYBACK_URL.search(text)
        if playback:
            LOGGER.log(5, "URL playbackURL detectada")
            return playback.group(1).replace("\\/", "/"), "playbackURL"
        m3u8 = M3U8_URL.search(text)
        if m3u8:
            LOGGER.log(5, "URL m3u8 detectada")
            return m3u8.group(0).replace("\\/", "/"), "m3u8"
        return None, None

    @staticmethod
    def extract_runtime_url(driver):
        """Lee playbackURL después de que el JavaScript de la página lo descifra."""
        try:
            url = driver.execute_script("""
                const value = window.playbackURL;
                return typeof value === "string" && value.startsWith("http")
                    ? value
                    : null;
            """)
        except WebDriverException:
            return None, None
        if url:
            LOGGER.log(5, "URL playbackURL runtime detectada")
            return url, "playbackURL-runtime"
        return None, None

    def extract_from_link(self, driver, url):
        try:
            driver.switch_to.default_content(); driver.get(url)
            try: driver.switch_to.frame("embedIframe")
            except Exception: pass
            result = WebDriverWait(driver, self.espera, poll_frequency=0.25).until(
                self._stream_available
            )
            LOGGER.debug("Extracción finalizada: url=%s origen=%s", url, result[1])
            return result
        except TimeoutException:
            LOGGER.info("Timeout buscando stream: url=%s timeout=%ss", url, self.espera)
            return None, None
        finally:
            try: driver.switch_to.default_content()
            except WebDriverException: pass

    def _stream_available(self, driver):
        result = self._extract_context(driver)
        return result if result[0] else False

    def _extract_context(self, driver):
        runtime = self.extract_runtime_url(driver)
        if runtime[0]: return runtime
        result = self.extract_url(driver.page_source)
        if result[0]: return result
        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            try:
                driver.switch_to.frame(iframe)
                result = self._extract_context(driver)
                driver.switch_to.parent_frame()
                if result[0]: return result
            except Exception:
                try: driver.switch_to.default_content()
                except WebDriverException: pass
                return None, None
        return None, None

    def _extract_with_new_driver(self, url):
        driver = self.driver_factory()
        try: return self.extract_from_link(driver, url)
        finally:
            try: driver.quit()
            except WebDriverException: pass

    def submit(self, url):
        if not url or url in self.pending: return
        LOGGER.debug("Programando extracción de stream: %s", url)
        self.pending[url] = self.executor.submit(self._extract_with_new_driver, url) if self.paralelo else None

    def result(self, url):
        with self.lock:
            if url in self.results: return self.results[url]
        result = self.pending[url].result() if self.paralelo else self.extract_from_link(self.driver, url)
        with self.lock: self.results[url] = result
        LOGGER.info("Stream %s: %s", url, result[1] or "no encontrado")
        return result

    def close(self):
        if self.executor:
            self.executor.shutdown(wait=True); self.executor = None
