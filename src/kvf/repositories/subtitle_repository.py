from pathlib import Path

from kvf.models.subtitle import Subtitle


class SubtitleRepository:

    def save(
        self,
        subtitle: Subtitle,
        path: Path,
    ):

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            subtitle.model_dump_json(
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(
        self,
        path: Path,
    ) -> Subtitle:

        return Subtitle.model_validate_json(
            path.read_text(
                encoding="utf-8",
            )
        )