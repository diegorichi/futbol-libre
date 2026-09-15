"""Persistencia atómica de sitios descubiertos."""
from pathlib import Path
from dotenv import dotenv_values


class SiteUrlStore:
    def __init__(self, path): self.path = Path(path)

    def write(self, urls):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        extra_url = dotenv_values(self.path).get("FUTBOL_LIBRE_EXTRA_URL", "")
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            "# Generado por update-futbol-libre-sites.sh; no editar manualmente.\n"
            f'FUTBOL_LIBRE_URL="{",".join(urls)}"\n'
            f'FUTBOL_LIBRE_EXTRA_URL="{extra_url}"\n', encoding="utf-8")
        temporary.replace(self.path)
