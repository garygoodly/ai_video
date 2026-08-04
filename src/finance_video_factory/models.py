from __future__ import annotations
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str
    summary: str = ""
    url: str
    source: str
    published_at: datetime | None = None

class MarketSnapshot(BaseModel):
    symbol: str
    last: float | None = None
    change_pct: float | None = None
    as_of: str = ""

class RankedEvent(BaseModel):
    title: str
    score: float
    article_indexes: list[int]
    reason: str

class Scene(BaseModel):
    index: int
    narration: str
    on_screen_text: str
    visual_type: str = "photo"
    search_query: str = "finance markets"
    chart_symbol: str | None = None
    estimated_duration_seconds: float = 8.0
    image: str | None = None
    duration_seconds: float | None = None

class PipelineContext(BaseModel):
    run_id: str
    workspace: Path
    settings: dict
    articles: list[Article] = Field(default_factory=list)
    markets: list[MarketSnapshot] = Field(default_factory=list)
    ranked_events: list[RankedEvent] = Field(default_factory=list)
    research: dict = Field(default_factory=dict)
    script: dict = Field(default_factory=dict)
    scenes: list[Scene] = Field(default_factory=list)
