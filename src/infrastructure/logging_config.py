"""Logging común del scraper, incluyendo nivel TRACE."""
import logging
import os


class LoggingConfigurator:
    TRACE = 5

    def __init__(self, level=None):
        self.level = level or os.getenv("LOG_LEVEL", "INFO").upper()

    def configure(self):
        logging.addLevelName(self.TRACE, "TRACE")
        logging.TRACE = self.TRACE
        if not hasattr(logging.Logger, "trace"):
            logging.Logger.trace = lambda logger, message, *args, **kwargs: logger.log(self.TRACE, message, *args, **kwargs)
        logging.basicConfig(level=getattr(logging, self.level, logging.INFO), format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
