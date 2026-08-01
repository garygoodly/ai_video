from pydantic import BaseModel


class ResearchSection(BaseModel):
    title: str
    paragraphs: list[str]


class Research(BaseModel):
    topic: str
    summary: str
    sections: list[ResearchSection]
    sources: list[str]