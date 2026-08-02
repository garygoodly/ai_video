from pydantic import BaseModel
from pydantic import ConfigDict


class Subtitle(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    provider: str

    file: str