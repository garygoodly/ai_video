from kvf.models.application import Application
from kvf.steps.base_step import BaseStep
from kvf.utils.file_utils import file_exists


class WaitForScriptStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        path = (
            application.project.source_dir / "script.json"
        )

        if file_exists(path):
            print("Script already exists. [SKIP]")
            return

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