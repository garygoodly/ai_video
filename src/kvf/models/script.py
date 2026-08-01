from pydantic import BaseModel


class ScriptSection(BaseModel):

    title: str

    narration: str


class Script(BaseModel):

    topic: str

    sections: list[ScriptSection]