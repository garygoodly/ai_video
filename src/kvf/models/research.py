from pydantic import BaseModel, Field


class ResearchSection(BaseModel):
    title: str
    paragraphs: list[str]


class EditorialSection(BaseModel):
    section: str
    priority: str = "normal"
    topics: list[str] = Field(default_factory=list)
    purpose: str = ""


class EditorialPlan(BaseModel):
    lead_story: str = ""
    market_thesis: str = ""
    sections: list[EditorialSection] = Field(default_factory=list)


class Research(BaseModel):
    topic: str
    summary: str
    editorial_plan: EditorialPlan = Field(default_factory=EditorialPlan)
    sections: list[ResearchSection]
    sources: list[str]
