from pathlib import Path

from kvf.models.application import Application
from kvf.steps.base_step import BaseStep


class WaitForResearchStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        path = (
            application.project.workspace
            / "research"
            / "research.json"
        )

        print()

        print("=" * 60)

        print("Manual Step")

        print("=" * 60)

        print()

        print(
            "Paste ChatGPT JSON into:"
        )

        print(path)

        print()

        input(
            "Press ENTER when finished..."
        )