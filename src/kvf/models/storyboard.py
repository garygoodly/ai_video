from __future__ import annotations

from enum import Enum

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
    """
    Describes WHAT media should be retrieved.

    No filenames here.
    MediaStage decides which provider to use and
    where the file is stored.
    """

    model_config = ConfigDict(extra="forbid")

    asset_type: AssetType = Field(
        description="Preferred visual asset type."
    )

    query: str = Field(
        min_length=3,
        description="Search query for media provider."
    )

    notes: str | None = Field(
        default=None,
        description="Optional visual guidance."
    )


class CameraSpec(BaseModel):
    """
    Camera movement for the renderer.
    """

    model_config = ConfigDict(extra="forbid")

    motion: CameraMotion = CameraMotion.KEN_BURNS

    duration_seconds: float = Field(
        gt=0,
        description="Camera animation duration."
    )


class TransitionSpec(BaseModel):
    """
    Transition into the next scene.
    """

    model_config = ConfigDict(extra="forbid")

    type: TransitionType = TransitionType.FADE

    duration_seconds: float = Field(
        default=1.0,
        ge=0,
        le=5
    )


class StoryboardScene(BaseModel):
    """
    One visual scene.

    Downstream stages should never modify narration.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)

    section: str = Field(
        min_length=1
    )

    narration: str = Field(
        min_length=10
    )

    estimated_duration_seconds: float = Field(
        gt=0
    )

    visual: VisualSpec

    camera: CameraSpec

    transition: TransitionSpec


class Storyboard(BaseModel):
    """
    Entire storyboard document.
    """

    model_config = ConfigDict(extra="forbid")

    topic: str

    total_estimated_duration_seconds: float

    scenes: list[StoryboardScene]

    @field_validator("scenes")
    @classmethod
    def validate_scene_ids(cls, scenes: list[StoryboardScene]):
        ids = [scene.id for scene in scenes]

        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate storyboard scene id.")

        return scenes

    @field_validator("total_estimated_duration_seconds")
    @classmethod
    def validate_total_duration(cls, value: float):
        if value <= 0:
            raise ValueError("Duration must be positive.")

        return value

    @property
    def scene_count(self) -> int:
        return len(self.scenes)

    @property
    def total_narration_length(self) -> int:
        return sum(len(scene.narration) for scene in self.scenes)