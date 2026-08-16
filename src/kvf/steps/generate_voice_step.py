from __future__ import annotations

import json
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
    """Generate narration in either natural continuous or cue-synced mode.

    Continuous mode deliberately decouples TTS from subtitle segmentation. The
    complete approved article is sent to the selected TTS engine as one text,
    allowing the engine to control phrasing and sentence pauses naturally.

    Cue-synced mode remains available when exact subtitle/audio boundaries are
    more important than maximum narration naturalness.
    """

    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        output_dir = workspace / "voice"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "narration.mp3"
        timing_path = output_dir / "cue_timing.json"
        metadata_path = output_dir / "voice.json"

        if audio_path.exists():
            print("Voice already exists. [SKIP]")
            return

        script = ScriptRepository().load(workspace / "script" / "script.json")
        metadata = SessionService._read_metadata(workspace)
        mode = metadata.get("narration_mode", "continuous")
        if mode == "continuous":
            self._generate_continuous(script, metadata, audio_path, timing_path)
        else:
            self._generate_cue_synced(script, metadata, audio_path, timing_path)

        VoiceRepository().save(
            Voice(
                provider=metadata.get("voice_engine", "edge"),
                voice=metadata.get("voice", "en-US-AndrewNeural"),
                file=audio_path.name,
            ),
            metadata_path,
        )
        print(f"Voice generated in {mode} narration mode: {audio_path}")

    def _generate_continuous(self, script, metadata, audio_path: Path, timing_path: Path) -> None:
        # Preserve the approved article's punctuation. Do NOT split at subtitle
        # boundaries: this is the key to natural cross-clause prosody.
        article = "\n\n".join(
            section.narration.strip() for section in script.sections
            if section.narration.strip()
        )
        if not article:
            raise ValueError("The approved script contains no narration text.")

        engine = VoiceEngineService()
        engine.generate(
            engine=metadata.get("voice_engine", "edge"),
            voice=metadata.get("voice", "en-US-AndrewNeural"),
            language_code=metadata.get("language_code", "en-US"),
            text=article,
            output=audio_path,
            rate=metadata.get("voice_rate", "+0%"),
            pitch=metadata.get("voice_pitch", "+0Hz"),
        )
        duration = self._probe_duration(audio_path)
        timing_path.write_text(
            json.dumps({
                "mode": "continuous",
                "duration_seconds": duration,
                "note": "Narration synthesized independently from subtitle segmentation."
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _generate_cue_synced(self, script, metadata, audio_path: Path, timing_path: Path) -> None:
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

        engine = VoiceEngineService()
        voice_engine = metadata.get("voice_engine", "edge")
        with tempfile.TemporaryDirectory(prefix="kvf-voice-") as tmp_name:
            tmp = Path(tmp_name)
            files = []
            cues = []
            cursor = 0.0
            for index, text in enumerate(texts, start=1):
                raw = tmp / f"raw_{index:04d}{'.mp3' if voice_engine == 'edge' else '.wav'}"
                wav = tmp / f"cue_{index:04d}.wav"
                engine.generate(
                    engine=voice_engine, voice=metadata.get("voice", "en-US-AndrewNeural"),
                    language_code=metadata.get("language_code", "en-US"), text=text, output=raw,
                    rate=metadata.get("voice_rate", "+0%"), pitch=metadata.get("voice_pitch", "+0Hz"),
                )
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                                "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)], check=True)
                duration = self._probe_duration(wav)
                cues.append({"text": text, "start": cursor, "end": cursor + duration})
                cursor += duration
                files.append(wav)

            concat = tmp / "cues.ffconcat"
            lines = ["ffconcat version 1.0"]
            for wav in files:
                escaped = str(wav.resolve()).replace("'", "'\\''")
                lines.append(f"file '{escaped}'")
            concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
            combined = tmp / "narration.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                            "-i", str(concat), "-c:a", "pcm_s16le", str(combined)], check=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(combined),
                            "-c:a", "libmp3lame", "-b:a", "128k", str(audio_path)], check=True)
        timing_path.write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _probe_duration(audio: Path) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
            check=True, capture_output=True, text=True,
        )
        return float(result.stdout.strip())
