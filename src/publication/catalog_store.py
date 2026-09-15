"""Persistencia atómica del documento JSON canónico."""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from domain.models import EventCatalogDocument


class CatalogStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def write(self, document: EventCatalogDocument | dict[str, Any]) -> None:
        if isinstance(document, dict):
            document = EventCatalogDocument.from_dict(document)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(document.as_dict(), ensure_ascii=False, indent=2) + "\n"
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, self.path)

    def read(self) -> EventCatalogDocument:
        with self.path.open(encoding="utf-8") as source:
            return EventCatalogDocument.from_dict(json.load(source))

