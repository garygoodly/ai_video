from kvf.models.application import Application
from kvf.models.subtitle import Subtitle
from kvf.repositories.script_repository import ScriptRepository
from kvf.repositories.subtitle_repository import SubtitleRepository
from kvf.services.exact_subtitle_service import ExactSubtitleService
from kvf.services.session_service import SessionService
from kvf.steps.base_step import BaseStep


class GenerateSubtitleStep(BaseStep):
    def execute(self, application: Application):
        workspace = application.project.workspace
        voice = workspace / "voice" / "narration.mp3"
        timing = workspace / "voice" / "cue_timing.json"
        subtitle_dir = workspace / "subtitle"
        srt = subtitle_dir / "subtitle.srt"
        metadata_path = subtitle_dir / "subtitle.json"

        if srt.exists() and metadata_path.exists():
            print("Subtitle already exists. [SKIP]")
            return

        session_metadata = SessionService._read_metadata(workspace)
        settings = session_metadata.get("subtitle_settings", {})
        script = ScriptRepository().load(workspace / "script" / "script.json")
        service = ExactSubtitleService(
            language_code=session_metadata.get("language_code", "en-US"),
            max_characters=settings.get("max_characters", 18),
            min_characters=settings.get("min_characters", 6),
            max_words=settings.get("max_words", 10),
        )
        cues = service.generate(
            [section.narration for section in script.sections], voice, srt,
            timing_file=timing,
        )
        SubtitleRepository().save(
            Subtitle(provider="approved_script_exact_tts_timing", file="subtitle.srt"),
            metadata_path,
        )
        print(f"Exact-script subtitles generated with {len(cues)} synchronized cues: {srt}")
