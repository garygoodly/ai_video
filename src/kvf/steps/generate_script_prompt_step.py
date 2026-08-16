import json

from kvf.services.session_service import SessionService

from kvf.models.application import Application
from kvf.repositories.research_repository import ResearchRepository
from kvf.services.prompt_service import PromptService
from kvf.steps.base_step import BaseStep
from kvf.utils.file_utils import file_exists


class GenerateScriptPromptStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        workspace = application.project.workspace
        source_dir = application.project.source_dir

        prompt_path = (
            source_dir / "script_prompt.md"
        )

        if file_exists(prompt_path):
            print("Script prompt already exists. [SKIP]")
            return

        research_path = (
            source_dir / "research.json"
        )

        research = ResearchRepository().load(
            research_path
        )

        metadata = SessionService._read_metadata(workspace)
        profile = metadata.get("edition_profile", {})
        context = {
            "topic": research.topic,
            "summary": research.summary,
            "editorial_plan": json.dumps(
                research.editorial_plan.model_dump(),
                ensure_ascii=False,
                indent=2,
            ),
            "edition_label": metadata.get("edition_label", "Global"),
            "output_language": metadata.get("output_language", "English"),
            "audience_note": profile.get("audience_note", "International viewers"),
            "script_language_rule": profile.get("script_language_rule", "Write natural spoken English."),
            "research": json.dumps(
                research.model_dump(),
                indent=2,
            ),
        }

        prompt = PromptService().render(
            "prompts/script.md",
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
            f"Script prompt generated: {prompt_path} [DONE]"
        )