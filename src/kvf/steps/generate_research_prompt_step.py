import json

from kvf.models.application import Application
from kvf.services.prompt_service import PromptService
from kvf.steps.base_step import BaseStep
from kvf.utils.file_utils import file_exists


class GenerateResearchPromptStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        project = application.project

        prompt_path = (
            project.workspace
            / "research"
            / "prompt.md"
        )

        if file_exists(prompt_path):
            print("Research prompt already exists. [SKIP]")
            return

        service = PromptService()

        context = {
            "topic": project.topic.name,
            "category": project.topic.category,
            "blueprint": json.dumps(
                project.blueprint.model_dump(),
                indent=2,
            ),
        }

        prompt = service.render(
            "prompts/research.md",
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

        print(f"Prompt generated: {prompt_path} [DONE]")