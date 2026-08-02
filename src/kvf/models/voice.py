from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict


class Voice(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    provider: str

    voice: str

    file: str

    duration_seconds: float | None = None