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
        subtitle_dir = workspace / "subtitle"
        subtitle_dir.mkdir(parents=True, exist_ok=True)
        srt = subtitle_dir / "subtitle.srt"
        metadata_path = subtitle_dir / "subtitle.json"
        source_srt = application.project.source_dir / "subtitle.srt"
        session_metadata = SessionService._read_metadata(workspace)

        if not session_metadata.get("subtitles_enabled", True):
            # Keep an empty SRT as an explicit artifact so session progress and
            # regeneration remain deterministic while FFmpeg omits the filter.
            srt.write_text("", encoding="utf-8")
            source_srt.write_text("", encoding="utf-8")
            SubtitleRepository().save(
                Subtitle(provider="disabled", file="subtitle.srt"), metadata_path
            )
            print("Subtitles disabled for this session.")
            return

        if srt.exists() and metadata_path.exists():
            print("Subtitle already exists. [SKIP]")
            return

        if session_metadata.get("narration_mode", "continuous") == "continuous":
            raise RuntimeError(
                "Continuous narration is intentionally independent of subtitle chunks. "
                "Turn subtitles off, or choose Cue-synced narration for exact subtitles."
            )

        voice = workspace / "voice" / "narration.mp3"
        timing = workspace / "voice" / "cue_timing.json"
        settings = session_metadata.get("subtitle_settings", {})
        script = ScriptRepository().load(application.project.source_dir / "script.json")
        service = ExactSubtitleService(
            language_code=session_metadata.get("language_code", "en-US"),
            max_characters=settings.get("max_characters", 18),
            min_characters=settings.get("min_characters", 6),
            max_words=settings.get("max_words", 10),
        )
        cues = service.generate(
            [section.narration for section in script.sections], voice, srt, timing_file=timing
        )
        SubtitleRepository().save(
            Subtitle(provider="approved_script_exact_tts_timing", file="subtitle.srt"), metadata_path
        )
        source_srt.write_text(srt.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Exact-script subtitles generated with {len(cues)} synchronized cues: {srt}")
