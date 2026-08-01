import json

from kvf.models.application import Application
from kvf.repositories.research_repository import ResearchRepository
from kvf.services.prompt_service import PromptService
from kvf.steps.base_step import BaseStep


class GenerateScriptPromptStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        workspace = application.project.workspace

        research_path = (
            workspace
            / "research"
            / "research.json"
        )

        research = ResearchRepository().load(
            research_path
        )

        context = {
            "topic": research.topic,
            "summary": research.summary,
            "research": json.dumps(
                research.model_dump(),
                indent=2,
            ),
        }

        prompt = PromptService().render(
            "prompts/script.md",
            context,
        )

        output = (
            workspace
            / "script"
            / "prompt.md"
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output.write_text(
            prompt,
            encoding="utf-8",
        )

        print(
            f"Script prompt generated: {output}"
        )