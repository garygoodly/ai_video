from pydantic import BaseModel, ConfigDict

from kvf.models.project import Project


class Application(BaseModel):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    settings: dict

    project: Project