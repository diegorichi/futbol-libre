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
        project_root = env_file.parent
        config = dotenv_values(env_file)

        def setting(name, default=None):
            return os.getenv(name) or config.get(name) or default

        urls_file = Path(os.getenv("FUTBOL_LIBRE_URL_FILE", project_root / "config/futbol_libre_urls.env"))
        if not urls_file.is_absolute(): urls_file = env_file.parent / urls_file
        urls = dotenv_values(urls_file)
        return cls({
            "urls_file": urls_file,
            "urls": urls.get("FUTBOL_LIBRE_URL") or os.getenv("FUTBOL_LIBRE_URL", ""),
            "extra_url": urls.get("FUTBOL_LIBRE_EXTRA_URL") or os.getenv("FUTBOL_LIBRE_EXTRA_URL", ""),
            "m3u": setting("M3U_FILE", str(project_root / "data/eventos.m3u")),
            "xml": setting("XML_FILE"), "events": setting("TV_EVENTS_FILE"),
            "agenda": setting("AGENDA_FILE", str(project_root / "data/agenda_web.json")),
            "threadfin": setting("THREADFIN_API_URL", "http://localhost:34400/api/"),
            "ntfy": setting("NTFY_URL"),
            "parallel": setting("PARALLEL_STREAM_EXTRACTION", "0").lower() in {"1", "true", "yes", "on"},
            "workers": max(1, int(setting("STREAM_EXTRACTION_WORKERS", "4"))),
            "progress": os.path.abspath(setting("PROGRESS_FILE", str(project_root / "data/.update-futbollibre.progress.json"))),
        })

    def __getitem__(self, key): return self.values[key]
