from kvf.models.application import Application
from kvf.steps.base_step import BaseStep


class WaitForScriptStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        path = (
            application.project.workspace
            / "script"
            / "script.json"
        )

        print()

        print("=" * 60)
        print("Manual Step")
        print("=" * 60)

        print()

        print("Paste ChatGPT JSON into:")

        print(path)

        print()

        input(
            "Press ENTER when finished..."
        )