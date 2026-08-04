import json
from pathlib import Path
from typing import Callable

from kvf.models.application import Application
from kvf.models.project import Project
from kvf.models.research import Research
from kvf.models.script import Script
from kvf.models.storyboard import Storyboard
from kvf.models.topic import Topic
from kvf.services.blueprint_service import BlueprintService
from kvf.services.session_service import SessionService
from kvf.steps.generate_research_prompt_step import GenerateResearchPromptStep
from kvf.steps.generate_script_prompt_step import GenerateScriptPromptStep
from kvf.steps.generate_storyboard_prompt_step import GenerateStoryboardPromptStep
from kvf.steps.validate_research_step import ValidateResearchStep
from kvf.steps.validate_script_step import ValidateScriptStep
from kvf.steps.validate_storyboard_step import ValidateStoryboardStep


class SessionController:
    MANUAL_STAGES = ("research", "script", "storyboard")

    def __init__(self, settings: dict, project_root: Path):
        self.settings = settings
        self.project_root = project_root
        self.sessions = SessionService(project_root / settings["workspace"]["root"])
        self.blueprint = BlueprintService(
            str(project_root / "config" / "blueprints")
        ).load("country")

    def application_for(self, workspace: Path) -> Application:
        metadata = SessionService._read_metadata(workspace)
        topic = Topic(
            id=metadata["id"],
            name=metadata["name"],
            category=metadata.get("category", "finance"),
        )
        project = Project(topic=topic, blueprint=self.blueprint, workspace=workspace)
        return Application(settings=self.settings, project=project)

    def prepare_stage(self, workspace: Path, stage: str) -> Path:
        application = self.application_for(workspace)
        generators = {
            "research": GenerateResearchPromptStep,
            "script": GenerateScriptPromptStep,
            "storyboard": GenerateStoryboardPromptStep,
        }
        if stage not in generators:
            raise ValueError(f"Unsupported manual stage: {stage}")
        generators[stage]().execute(application)
        return workspace / stage / "prompt.md"

    def normalize_and_validate(self, stage: str, text: str) -> str:
        normalized = self.sessions.extract_json(text)
        payload = json.loads(normalized)
        models = {
            "research": Research,
            "script": Script,
            "storyboard": Storyboard,
        }
        if stage not in models:
            raise ValueError(f"Unsupported manual stage: {stage}")
        models[stage].model_validate(payload)
        return normalized

    def save_and_validate(self, workspace: Path, stage: str, text: str) -> None:
        normalized = self.normalize_and_validate(stage, text)
        output = workspace / stage / f"{stage}.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(normalized, encoding="utf-8")

        application = self.application_for(workspace)
        validators = {
            "research": ValidateResearchStep,
            "script": ValidateScriptStep,
            "storyboard": ValidateStoryboardStep,
        }
        validators[stage]().execute(application)
        self.sessions.touch(workspace)

    def next_manual_stage(self, workspace: Path) -> str | None:
        inspection = self.sessions.inspect(workspace)
        stage = inspection["current_stage"]
        return stage if stage in self.MANUAL_STAGES else None

    def run_automatic(
        self,
        workspace: Path,
        progress_callback: Callable[[str], None] | None = None,
    ) -> None:
        from kvf.steps.download_media_step import DownloadMediaStep
        from kvf.steps.generate_subtitle_step import GenerateSubtitleStep
        from kvf.steps.generate_timeline_step import GenerateTimelineStep
        from kvf.steps.generate_video_step import GenerateVideoStep
        from kvf.steps.generate_voice_step import GenerateVoiceStep

        application = self.application_for(workspace)
        steps = [
            ("Downloading media", DownloadMediaStep()),
            ("Generating voice", GenerateVoiceStep()),
            ("Generating subtitles", GenerateSubtitleStep()),
            ("Building timeline", GenerateTimelineStep()),
            ("Rendering video", GenerateVideoStep()),
        ]
        for label, step in steps:
            if progress_callback:
                progress_callback(label)
            step.execute(application)
            self.sessions.touch(workspace)
