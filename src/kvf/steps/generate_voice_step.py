from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from kvf.models.application import Application
from kvf.models.voice import Voice
from kvf.repositories.script_repository import ScriptRepository
from kvf.repositories.voice_repository import VoiceRepository
from kvf.services.exact_subtitle_service import ExactSubtitleService
from kvf.services.session_service import SessionService
from kvf.services.voice_engine_service import VoiceEngineService
from kvf.steps.base_step import BaseStep


class GenerateVoiceStep(BaseStep):
    """Generate narration cue-by-cue and record exact cue boundaries.

    Because subtitle cues and audio chunks share the same segmentation, changing
    TTS speed can no longer leave the old subtitle timing behind.
    """

    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        output_dir = workspace / "voice"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "narration.mp3"
        timing_path = output_dir / "cue_timing.json"
        metadata_path = output_dir / "voice.json"

        if audio_path.exists() and timing_path.exists():
            print("Voice and cue timing already exist. [SKIP]")
            return

        script = ScriptRepository().load(workspace / "script" / "script.json")
        metadata = SessionService._read_metadata(workspace)
        settings = metadata.get("subtitle_settings", {})
        segmenter = ExactSubtitleService(
            language_code=metadata.get("language_code", "en-US"),
            max_characters=settings.get("max_characters", 18),
            min_characters=settings.get("min_characters", 6),
            max_words=settings.get("max_words", 10),
        )
        texts = segmenter.segment_sections([section.narration for section in script.sections])
        if not texts:
            raise ValueError("The approved script produced no narration cues.")

        voice_engine = metadata.get("voice_engine", "edge")
        voice_name = metadata.get("voice", "en-US-AndrewNeural")
        voice_rate = metadata.get("voice_rate", "+0%")
        voice_pitch = metadata.get("voice_pitch", "+0Hz")
        language_code = metadata.get("language_code", "en-US")
        engine = VoiceEngineService()

        with tempfile.TemporaryDirectory(prefix="kvf-voice-") as tmp_name:
            tmp = Path(tmp_name)
            normalized_files: list[Path] = []
            cues: list[dict] = []
            cursor = 0.0

            for index, text in enumerate(texts, start=1):
                raw_ext = ".mp3" if voice_engine == "edge" else ".wav"
                raw = tmp / f"raw_{index:04d}{raw_ext}"
                wav = tmp / f"cue_{index:04d}.wav"
                engine.generate(
                    engine=voice_engine,
                    voice=voice_name,
                    language_code=language_code,
                    text=text,
                    output=raw,
                    rate=voice_rate,
                    pitch=voice_pitch,
                )
                subprocess.run(
                    ["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                     "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
                    check=True,
                )
                duration = self._probe_duration(wav)
                cues.append({"text": text, "start": cursor, "end": cursor + duration})
                cursor += duration
                normalized_files.append(wav)
                print(f"Voice cue {index}/{len(texts)} generated: {duration:.2f}s")

            concat_file = tmp / "cues.ffconcat"
            lines = ["ffconcat version 1.0"]
            for wav in normalized_files:
                escaped = str(wav.resolve()).replace("'", "'\\''")
                lines.append(f"file '{escaped}'")
            concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            combined_wav = tmp / "narration.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                 "-i", str(concat_file), "-c:a", "pcm_s16le", str(combined_wav)],
                check=True,
            )
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(combined_wav),
                 "-c:a", "libmp3lame", "-b:a", "128k", str(audio_path)],
                check=True,
            )

        timing_path.write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8")
        VoiceRepository().save(
            Voice(provider=voice_engine, voice=voice_name, file=audio_path.name),
            metadata_path,
        )
        print(
            f"Voice generated with {voice_engine}/{voice_name}, rate {voice_rate}, "
            f"pitch {voice_pitch}; exact cue timing saved to {timing_path}"
        )

    @staticmethod
    def _probe_duration(audio: Path) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
            check=True, capture_output=True, text=True,
        )
        return float(result.stdout.strip())
