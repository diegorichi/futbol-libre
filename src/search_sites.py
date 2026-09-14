#!/usr/bin/env python3
"""Fetch the first page of football sites from SearXNG."""

import os
import sys
from pathlib import Path
from urllib.request import build_opener
from dotenv import dotenv_values
from site_search import SiteSearchClient
from site_url_store import SiteUrlStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = Path(os.getenv("ENV_FILE", PROJECT_ROOT / ".env"))
if not ENV_FILE.is_absolute():
    ENV_FILE = PROJECT_ROOT / ENV_FILE
ENV = {**dotenv_values(ENV_FILE), **os.environ}

SEARCH_URL = ENV.get("SEARXNG_SEARCH_URL", "http://192.168.0.168/search")
ENGINE = ENV.get("SEARXNG_ENGINE", "duckduckgo")
QUERY = ENV.get("SEARXNG_QUERY", "futbol libre")
URLS_FILE = Path(ENV.get("FUTBOL_LIBRE_URL_FILE", PROJECT_ROOT / "futbol_libre_urls.env"))
if not URLS_FILE.is_absolute():
    URLS_FILE = PROJECT_ROOT / URLS_FILE


class SearchSitesCommand:
    def run(self) -> int:
        try:
            urls = SiteSearchClient(SEARCH_URL, ENGINE, QUERY, opener_factory=build_opener).fetch_urls()
            SiteUrlStore(URLS_FILE).write(urls)
        except Exception as error:
            print(f"No se pudieron actualizar los sitios desde SearXNG: {error}", file=sys.stderr)
            return 1
        print(f"Sitios actualizados desde {ENGINE}: {len(urls)}")
        for index, url in enumerate(urls, start=1): print(f"{index}. {url}")
        return 0


if __name__ == "__main__":
    raise SystemExit(SearchSitesCommand().run())
