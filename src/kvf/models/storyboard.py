from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssetType(str, Enum):
    PHOTO = "photo"
    ILLUSTRATION = "illustration"
    MAP = "map"
    CHART = "chart"
    DIAGRAM = "diagram"
    SATELLITE = "satellite"
    AI_IMAGE = "ai_image"
    VIDEO = "video"


class CameraMotion(str, Enum):
    STATIC = "static"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    KEN_BURNS = "ken_burns"


class TransitionType(str, Enum):
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    CROSS_FADE = "cross_fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    ZOOM = "zoom"


class VisualSpec(BaseModel):
    """Describes what media should be retrieved."""

    model_config = ConfigDict(extra="forbid")

    asset_type: AssetType = Field(description="Preferred visual asset type.")
    query: str = Field(min_length=3, description="Search query for media provider.")
    notes: str | None = Field(default=None, description="Optional visual guidance.")


class CameraSpec(BaseModel):
    """Camera movement for the renderer.

    duration_seconds is retained only for compatibility with older storyboard
    JSON. It is optional and is not authoritative for final video timing.
    """

    model_config = ConfigDict(extra="forbid")

    motion: CameraMotion = CameraMotion.KEN_BURNS
    duration_seconds: float | None = Field(
        default=None,
        description="Optional non-authoritative camera-duration estimate.",
    )

    @field_validator("duration_seconds", mode="before")
    @classmethod
    def tolerate_optional_duration(cls, value: Any):
        return _optional_positive_number(value)


class TransitionSpec(BaseModel):
    """Transition into the next scene."""

    model_config = ConfigDict(extra="forbid")

    type: TransitionType = TransitionType.FADE
    duration_seconds: float = Field(default=1.0, ge=0, le=5)


class StoryboardScene(BaseModel):
    """One visual scene.

    estimated_duration_seconds is legacy/non-authoritative metadata. Final
    timing is derived after narration is rendered.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)
    section: str = Field(min_length=1)
    narration: str = Field(min_length=10)
    estimated_duration_seconds: float | None = Field(default=None)
    visual: VisualSpec
    camera: CameraSpec
    transition: TransitionSpec

    @field_validator("estimated_duration_seconds", mode="before")
    @classmethod
    def tolerate_optional_duration(cls, value: Any):
        return _optional_positive_number(value)


class Storyboard(BaseModel):
    """Entire storyboard document.

    total_estimated_duration_seconds is accepted for backward compatibility,
    but it never blocks validation and does not control final timing.
    """

    model_config = ConfigDict(extra="forbid")

    topic: str
    total_estimated_duration_seconds: float | None = None
    scenes: list[StoryboardScene]

    @field_validator("scenes")
    @classmethod
    def validate_scene_ids(cls, scenes: list[StoryboardScene]):
        ids = [scene.id for scene in scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate storyboard scene id.")
        return scenes

    @field_validator("total_estimated_duration_seconds", mode="before")
    @classmethod
    def tolerate_optional_total_duration(cls, value: Any):
        return _optional_positive_number(value)

    @property
    def scene_count(self) -> int:
        return len(self.scenes)

    @property
    def total_narration_length(self) -> int:
        return sum(len(scene.narration) for scene in self.scenes)


def _optional_positive_number(value: Any) -> float | None:
    """Convert usable duration metadata to float; otherwise ignore it.

    GPT duration estimates are advisory only. Missing, zero, negative, or
    prose values such as "about 8 seconds" must not prevent the user from
    continuing to the next stage.
    """

    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
