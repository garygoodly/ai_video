import json
import shutil
from pathlib import Path
from typing import Callable

from kvf.models.application import Application
from kvf.models.project import Project
from kvf.models.research import Research
from kvf.models.script import Script
from kvf.models.storyboard import Storyboard
from kvf.models.topic import Topic
from kvf.services.blueprint_service import BlueprintService
from kvf.services.edition_service import EditionService
from kvf.services.project_source_service import ProjectSourceService
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
        workspace_root = project_root / settings["workspace"]["root"]
        projects_root = project_root / settings.get("projects", {}).get("root", "projects")
        self.sessions = SessionService(workspace_root, projects_root)
        self.editions = EditionService(project_root / "config" / "editions.yaml")
        self.blueprint = BlueprintService(str(project_root / "config" / "blueprints")).load("country")

    def create_session(self, name: str, edition: str) -> Path:
        profile = self.editions.get(edition)
        return self.sessions.create(name, edition=profile["key"], edition_profile=profile)

    def edition_for_workspace(self, workspace: Path) -> dict:
        metadata = SessionService._read_metadata(workspace)
        return self.editions.get(metadata.get("edition", "global"))

    def application_for(self, workspace: Path) -> Application:
        metadata = SessionService._read_metadata(workspace)
        topic = Topic(
            id=metadata["id"],
            name=metadata["name"],
            category=metadata.get("category", "finance"),
        )
        source_dir = self.sessions.project_dir_for(workspace)
        project = Project(
            topic=topic,
            blueprint=self.blueprint,
            workspace=workspace,
            source_dir=source_dir,
        )
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
        return ProjectSourceService.prompt(application.project.source_dir, stage)

    def normalize_and_validate(self, stage: str, text: str) -> str:
        normalized = self.sessions.extract_json(text)
        payload = json.loads(normalized)
        models = {"research": Research, "script": Script, "storyboard": Storyboard}
        if stage not in models:
            raise ValueError(f"Unsupported manual stage: {stage}")
        models[stage].model_validate(payload)
        return normalized

    def save_and_validate(self, workspace: Path, stage: str, text: str) -> None:
        normalized = self.normalize_and_validate(stage, text)
        application = self.application_for(workspace)
        output = ProjectSourceService.artifact(application.project.source_dir, stage)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(normalized, encoding="utf-8")

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

    def regenerate(
        self,
        workspace: Path,
        selected: set[str],
        voice: str | None = None,
        voice_engine: str | None = None,
        subtitle_settings: dict | None = None,
        subtitle_style: dict | None = None,
        voice_rate: str | None = None,
        voice_pitch: str | None = None,
        media_settings: dict | None = None,
        narration_mode: str | None = None,
        subtitles_enabled: bool | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> set[str]:
        from kvf.services.regeneration_service import RegenerationService

        rebuilt = RegenerationService.invalidate(
            workspace, selected, voice, voice_engine, voice_rate, voice_pitch,
            subtitle_settings, subtitle_style, media_settings,
            narration_mode, subtitles_enabled
        )
        self.sessions.touch(workspace)
        self.run_automatic(workspace, progress_callback)
        return rebuilt

    def generate_voice_preview(
        self,
        workspace: Path,
        *,
        engine: str,
        voice: str,
        rate: str,
        pitch: str,
        text: str,
    ) -> Path:
        from kvf.services.voice_engine_service import VoiceEngineService

        metadata = SessionService._read_metadata(workspace)
        preview_dir = workspace / "_preview"
        preview_dir.mkdir(parents=True, exist_ok=True)
        output = preview_dir / "voice_preview.mp3"
        output.unlink(missing_ok=True)
        VoiceEngineService().generate(
            engine=engine, voice=voice,
            language_code=metadata.get("language_code", "en-US"),
            text=text, output=output, rate=rate, pitch=pitch,
        )
        return output

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
