import json
from pathlib import Path

from kvf.models.storyboard import Storyboard


class StoryboardRepository:

    def load(
        self,
        path: Path,
    ) -> Storyboard:

        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        return Storyboard.model_validate(data)

    def save(
        self,
        storyboard: Storyboard,
        path: Path,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                storyboard.model_dump(mode="json"),
                f,
                indent=2,
                ensure_ascii=False,
            )