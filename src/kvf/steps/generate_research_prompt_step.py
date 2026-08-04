import json
from datetime import date, timedelta

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

        metadata_path = project.workspace / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        reference_date = date.fromisoformat(
            metadata.get("reference_date", date.today().isoformat())
        )

        context = {
            "project_name": project.topic.name,
            "reference_date": reference_date.isoformat(),
            "previous_date": (reference_date - timedelta(days=1)).isoformat(),
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