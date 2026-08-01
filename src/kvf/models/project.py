from pathlib import Path
from pydantic import BaseModel, ConfigDict
from kvf.models.blueprint import Blueprint
from kvf.models.topic import Topic

class Project(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    topic: Topic
    blueprint: Blueprint
    workspace: Path | None = None