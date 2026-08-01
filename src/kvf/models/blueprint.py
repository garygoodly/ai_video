from pydantic import BaseModel


class Section(BaseModel):
    id: str
    duration_seconds: int


class Blueprint(BaseModel):
    id: str
    title: str
    duration_minutes: int
    style: str
    sections: list[Section]