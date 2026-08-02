from pydantic import BaseModel
from pydantic import ConfigDict


class TimelineScene(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    id: int

    image: str

    narration: str

    subtitle_start: float

    subtitle_end: float

    duration_seconds: float

    camera_motion: str

    transition: str


class Timeline(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    total_duration_seconds: float

    scenes: list[TimelineScene]