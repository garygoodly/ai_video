from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MediaProvider(str, Enum):
    WIKIMEDIA = "wikimedia"
    OPENVERSE = "openverse"
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    AI = "ai"


class MediaAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene: int

    provider: MediaProvider

    query: str

    file: str

    width: int

    height: int

    license: str | None = None

    author: str | None = None

    source_url: str


class Media(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assets: list[MediaAsset]

    @property
    def count(self) -> int:
        return len(self.assets)