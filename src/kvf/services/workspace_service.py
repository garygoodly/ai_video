import json
from pathlib import Path

from kvf.models.topic import Topic


class WorkspaceService:

    def __init__(self, root: str):

        self.root = Path(root)

    def create(self, topic: Topic) -> Path:

        workspace = self.root / topic.id

        workspace.mkdir(
            parents=True,
            exist_ok=True,
        )

        folders = [
            "research",
            "script",
            "images",
            "audio",
            "subtitles",
            "segments",
            "final",
        ]

        for folder in folders:

            (workspace / folder).mkdir(
                exist_ok=True
            )

        metadata = {
            "id": topic.id,
            "name": topic.name,
            "category": topic.category,
        }

        with (
            workspace / "metadata.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
            )

        return workspace