from pydantic import BaseModel, ConfigDict


class MediaSearchResult(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    provider: str

    title: str

    url: str

    width: int

    height: int

    author: str | None = None

    license: str | None = None

    source_url: str | None = None