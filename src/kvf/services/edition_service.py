from __future__ import annotations

from pathlib import Path
from typing import Any

from kvf.utils.yaml_loader import load_yaml


class EditionService:
    """Load and validate regional video-edition profiles."""

    DEFAULT_KEY = "global"

    def __init__(self, config_path: str | Path):
        payload = load_yaml(str(config_path))
        self._editions: dict[str, dict[str, Any]] = payload.get("editions", {})
        if self.DEFAULT_KEY not in self._editions:
            raise ValueError("The editions configuration must define a global profile.")

    def all(self) -> dict[str, dict[str, Any]]:
        return {key: dict(value) for key, value in self._editions.items()}

    def get(self, key: str | None) -> dict[str, Any]:
        normalized = (key or self.DEFAULT_KEY).strip().lower()
        if normalized not in self._editions:
            normalized = self.DEFAULT_KEY
        return {"key": normalized, **self._editions[normalized]}
