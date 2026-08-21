import json

from kvf.models.application import Application
from kvf.models.subtitle import Subtitle
from kvf.repositories.script_repository import ScriptRepository
from kvf.repositories.subtitle_repository import SubtitleRepository
from kvf.services.exact_subtitle_service import ExactSubtitleService
from kvf.services.forced_alignment_service import ForcedAlignmentService
from kvf.services.session_service import SessionService
from kvf.services.native_timing_alignment_service import NativeTimingAlignmentService
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
        sections = [section.narration for section in script.sections]
        mode = session_metadata.get("narration_mode", "continuous")

        if mode == "continuous":
            exact_sections = [service.segment_sections([text]) for text in sections]
            timing_payload = {}
            if timing.exists():
                try:
                    timing_payload = json.loads(timing.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    timing_payload = {}
            section_timings = timing_payload.get("sections", []) if isinstance(timing_payload, dict) else []
            if section_timings and all(
                isinstance(item.get("word_timings"), list) and item.get("word_timings")
                for item in section_timings
            ):
                aligner = NativeTimingAlignmentService()
                cues = []
                for index, exact_group in enumerate(exact_sections):
                    if index >= len(section_timings):
                        break
                    item = section_timings[index]
                    cues.extend(
                        aligner.align_texts(
                            exact_group,
                            item.get("word_timings", []),
                            float(item.get("speech_start", 0.0)),
                            float(item.get("speech_end", 0.0)),
                        )
                    )
                provider = "approved_script_edge_native_word_timing"
            elif section_timings:
                cues = ForcedAlignmentService().align_sections(
                    exact_sections,
                    voice,
                    session_metadata.get("language_code", "en-US"),
                    section_timings,
                )
                provider = "approved_script_section_forced_alignment"
            else:
                exact_text = [cue for group in exact_sections for cue in group]
                cues = ForcedAlignmentService().align(
                    exact_text,
                    voice,
                    session_metadata.get("language_code", "en-US"),
                )
                provider = "approved_script_forced_alignment"
            service.write_cues(cues, srt)
        else:
            cues = service.generate(sections, voice, srt, timing_file=timing)
            provider = "approved_script_exact_tts_timing"

        SubtitleRepository().save(
            Subtitle(provider=provider, file="subtitle.srt"), metadata_path
        )
        source_srt.write_text(srt.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Exact approved-script subtitles generated with {len(cues)} cues: {srt}")
