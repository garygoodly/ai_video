from kvf.models.application import Application
from kvf.repositories.script_repository import ScriptRepository
from kvf.steps.base_step import BaseStep


class ValidateScriptStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        path = (
            application.project.source_dir / "script.json"
        )
        if not path.exists():
            raise FileNotFoundError(path)

        script = ScriptRepository().load(
            path
        )

        print()

        print("Script validated.")

        print(
            f"Sections: {len(script.sections)}"
        )