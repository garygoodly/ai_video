import json
from pathlib import Path

from kvf.models.media import Media


class MediaRepository:

    def load(
        self,
        path: Path,
    ) -> Media:

        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            return Media.model_validate(
                json.load(f)
            )

    def save(
        self,
        media: Media,
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
                media.model_dump(mode="json"),
                f,
                indent=2,
                ensure_ascii=False,
            )