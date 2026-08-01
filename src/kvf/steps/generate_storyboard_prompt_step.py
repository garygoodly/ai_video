import json

from kvf.models.application import Application
from kvf.repositories.script_repository import ScriptRepository
from kvf.services.prompt_service import PromptService
from kvf.steps.base_step import BaseStep
from kvf.utils.file_utils import file_exists


class GenerateStoryboardPromptStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        workspace = application.project.workspace

        prompt_path = (
            workspace
            / "storyboard"
            / "prompt.md"
        )

        if file_exists(prompt_path):
            print("Storyboard prompt already exists. [SKIP]")
            return

        script_path = (
            workspace
            / "script"
            / "script.json"
        )

        script = ScriptRepository().load(
            script_path
        )

        context = {
            "topic": script.topic,
            "script": json.dumps(
                script.model_dump(),
                indent=2,
                ensure_ascii=False,
            ),
        }

        prompt = PromptService().render(
            "prompts/storyboard.md",
            context,
        )

        prompt_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        prompt_path.write_text(
            prompt,
            encoding="utf-8",
        )

        print(
            f"Storyboard prompt generated: {prompt_path} [DONE]"
        )