"""Factory única de Chrome para scraping."""
import logging
import os
import shutil
import tempfile
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

load_dotenv(os.getenv("ENV_FILE", ".env"))
LOGGER = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
DEFAULT_PAGE_LOAD_TIMEOUT_SECONDS = 30
PROFILE_PREFIX = "futbol-chrome"


def close_browser(driver):
    """Cierra Chrome y elimina su perfil incluso si WebDriver ya se rompió."""
    profile_dir = getattr(driver, "_futbol_profile_dir", None)
    try:
        driver.quit()
    except Exception:
        LOGGER.exception("No se pudo cerrar la sesión de Chrome")
    finally:
        if profile_dir:
            shutil.rmtree(profile_dir, ignore_errors=True)


class BrowserDriverFactory:
    def __init__(self, user_agent=USER_AGENT, headless=None, proxy_url=None, page_load_timeout=None):
        self.user_agent = user_agent
        self.headless = headless
        self.proxy_url = proxy_url
        self.page_load_timeout = page_load_timeout

    def create(self):
        options = webdriver.ChromeOptions()
        profile_dir = tempfile.mkdtemp(prefix=f"{PROFILE_PREFIX}-{os.getsid(0)}-")
        options.add_argument(f"user-agent={self.user_agent}")
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--window-size=1440,900")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if self.proxy_url:
            options.add_argument(f"--proxy-server={self.proxy_url}")
        chrome_binary = os.getenv("CHROME_BINARY")
        if chrome_binary:
            options.binary_location = chrome_binary
        if self._headless(): options.add_argument("--headless=new")
        LOGGER.debug("Creando Chrome: headless=%s", self._headless())
        driver_path = os.getenv("CHROMEDRIVER_PATH")
        service = Service(executable_path=driver_path) if driver_path else None
        try:
            driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            shutil.rmtree(profile_dir, ignore_errors=True)
            raise
        driver._futbol_profile_dir = profile_dir
        timeout = self._page_load_timeout()
        driver.set_page_load_timeout(timeout)
        LOGGER.info("Chrome creado para scraping (timeout de carga: %ss)", timeout)
        return driver

    def _headless(self):
        if self.headless is not None: return self.headless
        return os.getenv("HEADLESS", "1").strip().lower() in {"1", "true", "yes", "on"}

    def _page_load_timeout(self):
        if self.page_load_timeout is not None:
            return self.page_load_timeout
        return float(os.getenv("PAGE_LOAD_TIMEOUT_SECONDS", DEFAULT_PAGE_LOAD_TIMEOUT_SECONDS))
