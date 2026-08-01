from pydantic import BaseModel


class Topic(BaseModel):
    id: str
    name: str
    category: str