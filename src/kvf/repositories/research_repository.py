import json
from pathlib import Path

from kvf.models.research import Research


class ResearchRepository:

    def load(
        self,
        path: Path,
    ) -> Research:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return Research.model_validate(data)