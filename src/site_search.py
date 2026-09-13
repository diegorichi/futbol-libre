"""Cliente aislado para descubrir sitios mediante SearXNG."""

import json
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "es-US,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "DNT": "1", "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
}


class SiteSearchClient:
    """Única responsabilidad: consultar y normalizar la respuesta de SearXNG."""

    def __init__(self, search_url, engine, query, opener_factory=build_opener):
        self.search_url = search_url
        self.engine = engine
        self.query = query
        self.opener_factory = opener_factory

    def fetch_urls(self, limit=10):
        opener = self.opener_factory(HTTPCookieProcessor(CookieJar()))
        payloads = []
        for engine in ([self.engine] if self.engine else [None]):
            params = {"q": f'"{self.query}"', "format": "json", "size": limit}
            if engine:
                params["engines"] = engine
            request = Request(f"{self.search_url}?{urlencode(params)}", headers=DEFAULT_HEADERS)
            with opener.open(request, timeout=30) as response:
                payload = json.load(response)
            payloads.append(payload)
            if payload.get("results"):
                break
        urls, seen = [], set()
        for payload in payloads:
            for result in payload.get("results", [])[:limit]:
                url = (result.get("url") or "").strip()
                if url.startswith(("http://", "https://")) and url not in seen:
                    urls.append(url)
                    seen.add(url)
            if len(urls) >= limit:
                break
        if not urls:
            engines = [item for payload in payloads for item in payload.get("unresponsive_engines", [])]
            detail = f" Motores sin respuesta: {engines}." if engines else ""
            raise RuntimeError(f"SearXNG no devolvió URLs.{detail}")
        return urls[:limit]
