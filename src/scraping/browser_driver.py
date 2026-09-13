"""Factory única de Chrome para scraping."""
import logging
import os
from dotenv import load_dotenv
from selenium import webdriver

load_dotenv(os.getenv("ENV_FILE", ".env"))
LOGGER = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


class BrowserDriverFactory:
    def __init__(self, user_agent=USER_AGENT, headless=None):
        self.user_agent = user_agent
        self.headless = headless

    def create(self):
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={self.user_agent}")
        options.add_argument("--window-size=1440,900")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if self._headless(): options.add_argument("--headless=new")
        LOGGER.debug("Creando Chrome: headless=%s", self._headless())
        driver = webdriver.Chrome(options=options)
        LOGGER.info("Chrome creado para scraping")
        return driver

    def _headless(self):
        if self.headless is not None: return self.headless
        return os.getenv("HEADLESS", "1").strip().lower() in {"1", "true", "yes", "on"}
