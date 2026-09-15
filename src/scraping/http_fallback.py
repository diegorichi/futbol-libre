"""Descarga HTML sin seguir redirecciones para sitios con anti-adblock."""
from html import escape
import re
from urllib.parse import urljoin

import requests


def fetch_html(url, timeout=20):
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=timeout,
        allow_redirects=False,
    )
    if response.status_code >= 300 and response.status_code < 400:
        return None, f"HTTP {response.status_code} -> {response.headers.get('Location', '')}"
    response.raise_for_status()
    return response.text, None


def iframe_urls(html, base_url):
    return [
        urljoin(base_url, value)
        for value in re.findall(
            r"<iframe\b[^>]*\bsrc=[\"']([^\"']+)", html, re.I
        )
    ]


def load_html(driver, html, base_url):
    """Carga HTML descargado conservando la URL base para enlaces relativos."""
    base = f'<base href="{escape(base_url, quote=True)}">'
    document = html.replace("<head>", f"<head>{base}", 1)
    driver.execute_script(
        """
        document.open();
        document.write(arguments[0]);
        document.close();
        """,
        document,
    )
