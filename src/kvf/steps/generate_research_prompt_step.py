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
            project.source_dir / "research_prompt.md"
        )

        if file_exists(prompt_path):
            print("Research prompt already exists. [SKIP]")
            return

        service = PromptService()

        from kvf.services.session_service import SessionService
        metadata = SessionService._read_metadata(project.workspace)
        reference_date = date.fromisoformat(
            metadata.get("reference_date", date.today().isoformat())
        )

        profile = metadata.get("edition_profile", {})
        context = {
            "project_name": project.topic.name,
            "reference_date": reference_date.isoformat(),
            "previous_date": (reference_date - timedelta(days=1)).isoformat(),
            "edition_label": metadata.get("edition_label", "Global"),
            "output_language": metadata.get("output_language", "English"),
            "audience_note": profile.get("audience_note", "International viewers"),
            "research_focus": profile.get("research_focus", "Build a globally balanced briefing."),
            "editorial_structure": profile.get("editorial_structure", "Use a clear headline-to-markets-to-conclusion structure."),
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