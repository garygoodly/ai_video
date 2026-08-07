from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from kvf.providers.edge_tts_provider import EdgeTTSProvider


class VoiceEngineService:
    """Small pluggable TTS facade.

    Edge TTS remains the zero-setup engine. Kokoro is optional and is loaded only
    when selected, so the base project stays lightweight.
    """

    ENGINE_LABELS = {
        "edge": "Microsoft Edge TTS",
        "kokoro": "Kokoro (local, optional)",
    }

    KOKORO_LANG = {
        "zh-TW": "z",
        "zh-CN": "z",
        "ja-JP": "j",
        "en-US": "a",
        "en-GB": "b",
    }

    def generate(
        self,
        *,
        engine: str,
        voice: str,
        language_code: str,
        text: str,
        output: Path,
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        engine = engine.casefold().strip()
        if engine == "edge":
            EdgeTTSProvider(voice=voice, rate=rate, pitch=pitch).generate(text, output)
            return
        if engine == "kokoro":
            self._generate_kokoro(
                voice=voice,
                language_code=language_code,
                text=text,
                output=output,
                rate=rate,
            )
            return
        raise ValueError(f"Unsupported voice engine: {engine}")

    def _generate_kokoro(
        self,
        *,
        voice: str,
        language_code: str,
        text: str,
        output: Path,
        rate: str,
    ) -> None:
        try:
            import soundfile as sf  # type: ignore
            from kokoro import KPipeline  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Kokoro is optional. Install it with: "
                "pip install -r requirements-optional-voices.txt"
            ) from exc

        lang_code = self.KOKORO_LANG.get(language_code, "a")
        speed = self._rate_to_speed(rate)
        pipeline = KPipeline(lang_code=lang_code)
        chunks = []
        for _graphemes, _phonemes, audio in pipeline(text, voice=voice, speed=speed):
            chunks.append(audio)
        if not chunks:
            raise RuntimeError("Kokoro produced no audio.")

        import numpy as np  # type: ignore

        audio = np.concatenate(chunks)
        if output.suffix.lower() == ".wav":
            sf.write(output, audio, 24000)
            return

        with tempfile.TemporaryDirectory(prefix="kvf-kokoro-") as tmp:
            wav = Path(tmp) / "voice.wav"
            sf.write(wav, audio, 24000)
            subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                    "-ar", "48000", "-ac", "1", str(output),
                ],
                check=True,
            )

    @staticmethod
    def _rate_to_speed(rate: str) -> float:
        value = rate.strip().replace("%", "")
        try:
            percent = float(value)
        except ValueError:
            percent = 0.0
        return max(0.5, min(1.6, 1.0 + percent / 100.0))
