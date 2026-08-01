import json

from kvf.models.application import Application
from kvf.services.prompt_service import PromptService
from kvf.steps.base_step import BaseStep


class GenerateResearchPromptStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        project = application.project

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

        output_path = (
            project.workspace
            / "research"
            / "prompt.md"
        )

        output_path.write_text(
            prompt,
            encoding="utf-8",
        )

        print(f"Prompt generated: {output_path}")