from __future__ import annotations

import array
import json
import subprocess
import tempfile
import wave
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
    """Generate narration with semantic rather than subtitle-driven pauses.

    Subtitle-only splits inside one sentence receive no inserted pause. A real
    sentence boundary receives a short pause. TTS-generated leading/trailing
    silence is trimmed from each cue first, preventing every subtitle chunk
    from sounding like an independent sentence.
    """

    # These values are deliberately small. They can become GUI settings later
    # without changing the cue-timing format.
    INTRA_SENTENCE_PAUSE_SECONDS = 0.0
    SENTENCE_PAUSE_SECONDS = 0.14

    # Trim only silence at the *edges* of generated clips. This avoids the
    # aggressive behavior of ffmpeg silenceremove on natural internal pauses.
    SILENCE_THRESHOLD_DBFS = -45.0
    EDGE_PADDING_SECONDS = 0.015
    ANALYSIS_WINDOW_SECONDS = 0.010

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
        units = segmenter.segment_units([section.narration for section in script.sections])
        if not units:
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

            for index, unit in enumerate(units, start=1):
                text = str(unit["text"])
                boundary_after = str(unit.get("boundary_after", "intra"))
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

                self._trim_edge_silence(wav)
                duration = self._probe_duration(wav)
                pause_after = self._pause_for_boundary(boundary_after, is_last=index == len(units))
                cues.append({
                    "text": text,
                    "start": cursor,
                    "end": cursor + duration,
                    "boundary_after": boundary_after,
                    "pause_after_seconds": pause_after,
                })
                cursor += duration + pause_after
                normalized_files.append(wav)
                print(
                    f"Voice cue {index}/{len(units)} generated: {duration:.2f}s, "
                    f"pause {pause_after:.2f}s ({boundary_after})"
                )

            combined_wav = tmp / "narration.wav"
            self._combine_with_semantic_pauses(normalized_files, cues, combined_wav)
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
            f"pitch {voice_pitch}; semantic cue timing saved to {timing_path}"
        )

    def _pause_for_boundary(self, boundary_after: str, *, is_last: bool) -> float:
        if is_last:
            return 0.0
        if boundary_after == "sentence":
            return self.SENTENCE_PAUSE_SECONDS
        return self.INTRA_SENTENCE_PAUSE_SECONDS

    def _trim_edge_silence(self, wav_path: Path) -> None:
        """Trim only leading/trailing low-level PCM silence from a mono WAV."""
        with wave.open(str(wav_path), "rb") as reader:
            channels = reader.getnchannels()
            sample_width = reader.getsampwidth()
            frame_rate = reader.getframerate()
            frames = reader.readframes(reader.getnframes())

        if channels != 1 or sample_width != 2 or not frames:
            return

        samples = array.array("h")
        samples.frombytes(frames)
        if not samples:
            return

        # 16-bit PCM amplitude corresponding to the configured dBFS threshold.
        threshold = 32767.0 * (10.0 ** (self.SILENCE_THRESHOLD_DBFS / 20.0))
        window = max(1, int(frame_rate * self.ANALYSIS_WINDOW_SECONDS))
        padding = max(0, int(frame_rate * self.EDGE_PADDING_SECONDS))

        first_active = None
        for start in range(0, len(samples), window):
            block = samples[start:start + window]
            if block and max(abs(value) for value in block) >= threshold:
                first_active = start
                break

        last_active = None
        for end in range(len(samples), 0, -window):
            start = max(0, end - window)
            block = samples[start:end]
            if block and max(abs(value) for value in block) >= threshold:
                last_active = end
                break

        if first_active is None or last_active is None or first_active >= last_active:
            return

        trim_start = max(0, first_active - padding)
        trim_end = min(len(samples), last_active + padding)
        trimmed = samples[trim_start:trim_end]

        with wave.open(str(wav_path), "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(frame_rate)
            writer.writeframes(trimmed.tobytes())

    @staticmethod
    def _combine_with_semantic_pauses(
        wav_files: list[Path],
        cues: list[dict],
        output: Path,
    ) -> None:
        if len(wav_files) != len(cues):
            raise ValueError("Voice cue file count does not match timing cue count.")

        frame_rate = 48000
        with wave.open(str(output), "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(frame_rate)

            for wav_path, cue in zip(wav_files, cues):
                with wave.open(str(wav_path), "rb") as reader:
                    if (
                        reader.getnchannels() != 1
                        or reader.getsampwidth() != 2
                        or reader.getframerate() != frame_rate
                    ):
                        raise ValueError(f"Unexpected voice cue WAV format: {wav_path}")
                    writer.writeframes(reader.readframes(reader.getnframes()))

                pause_seconds = max(0.0, float(cue.get("pause_after_seconds", 0.0)))
                pause_frames = round(frame_rate * pause_seconds)
                if pause_frames:
                    writer.writeframes(b"\x00\x00" * pause_frames)

    @staticmethod
    def _probe_duration(audio: Path) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
            check=True, capture_output=True, text=True,
        )
        return float(result.stdout.strip())
