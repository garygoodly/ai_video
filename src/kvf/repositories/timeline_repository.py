from pathlib import Path

from kvf.models.timeline import Timeline


class TimelineRepository:

    def save(
        self,
        timeline: Timeline,
        path: Path,
    ):

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            timeline.model_dump_json(
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(
        self,
        path: Path,
    ) -> Timeline:

        return Timeline.model_validate_json(
            path.read_text(
                encoding="utf-8",
            )
        )