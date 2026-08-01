import json
from pathlib import Path

from kvf.models.script import Script


class ScriptRepository:

    def load(
        self,
        path: Path,
    ) -> Script:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return Script.model_validate(data)