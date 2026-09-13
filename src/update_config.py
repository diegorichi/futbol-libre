"""Configuración del proceso de actualización."""
import os
from pathlib import Path
from dotenv import dotenv_values


class UpdateConfig:
    def __init__(self, values): self.values = values

    @classmethod
    def from_environment(cls):
        env_file = Path(os.getenv("ENV_FILE", ".env"))
        if not env_file.is_absolute(): env_file = Path.cwd() / env_file
        urls_file = Path(os.getenv("FUTBOL_LIBRE_URL_FILE", env_file.with_name("futbol_libre_urls.env")))
        if not urls_file.is_absolute(): urls_file = env_file.parent / urls_file
        urls = dotenv_values(urls_file)
        return cls({
            "urls_file": urls_file,
            "urls": urls.get("FUTBOL_LIBRE_URL") or os.getenv("FUTBOL_LIBRE_URL", ""),
            "extra_url": urls.get("FUTBOL_LIBRE_EXTRA_URL") or os.getenv("FUTBOL_LIBRE_EXTRA_URL", ""),
            "m3u": os.getenv("M3U_FILE") or str(Path.cwd() / "eventos.m3u"),
            "xml": os.getenv("XML_FILE"), "events": os.getenv("TV_EVENTS_FILE"),
            "agenda": os.getenv("AGENDA_FILE") or str(Path.cwd() / "agenda_web.json"),
            "threadfin": os.getenv("THREADFIN_API_URL", "http://localhost:34400/api/"),
            "ntfy": os.getenv("NTFY_URL"),
            "parallel": os.getenv("PARALLEL_STREAM_EXTRACTION", "0").lower() in {"1", "true", "yes", "on"},
            "workers": max(1, int(os.getenv("STREAM_EXTRACTION_WORKERS", "4"))),
            "progress": os.path.abspath(os.getenv("PROGRESS_FILE", str(Path(__file__).parent.parent / ".update-futbollibre.progress.json"))),
        })

    def __getitem__(self, key): return self.values[key]
