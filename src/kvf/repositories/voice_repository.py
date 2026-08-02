import json
from pathlib import Path

from kvf.models.voice import Voice


class VoiceRepository:

    def save(
        self,
        voice: Voice,
        path: Path,
    ):

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            voice.model_dump_json(
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(
        self,
        path: Path,
    ) -> Voice:

        return Voice.model_validate_json(
            path.read_text(
                encoding="utf-8",
            )
        )