from __future__ import annotations

import re
import subprocess
from pathlib import Path


class ForcedAlignmentService:
    """Align exact approved subtitle text to continuous narration audio.

    Whisper is used only as a timing sensor. Recognized words are never written
    into subtitles, so names, numbers and Chinese characters remain exactly as
    they appear in the approved script. If Whisper is unavailable, timing falls
    back to speech-aware proportional allocation over the real audio duration.
    """

    def align(self, exact_cues: list[str], audio: Path, language_code: str) -> list[dict]:
        if not exact_cues:
            return []
        try:
            anchors = self._whisper_anchors(audio, language_code)
            if anchors:
                return self._map_by_text_weight(exact_cues, anchors)
        except Exception as exc:
            print(f"Forced alignment warning: Whisper timing unavailable ({exc}); using audio-duration fallback.")
        return self._duration_fallback(exact_cues, audio)

    def _whisper_anchors(self, audio: Path, language_code: str) -> list[dict]:
        try:
            import whisper  # type: ignore
        except ImportError as exc:
            raise RuntimeError("openai-whisper is not installed") from exc

        model = whisper.load_model("tiny")
        language = "zh" if language_code.startswith("zh") else "ja" if language_code.startswith("ja") else "en"
        result = model.transcribe(str(audio), language=language, word_timestamps=True, verbose=False)
        words = []
        for segment in result.get("segments", []):
            for word in segment.get("words", []) or []:
                text = str(word.get("word", "")).strip()
                if text:
                    words.append({"text": text, "start": float(word["start"]), "end": float(word["end"])})
        return words

    def _map_by_text_weight(self, cues: list[str], words: list[dict]) -> list[dict]:
        # We intentionally do not copy ASR text. Word timestamps provide the
        # speech clock; approved-text weights decide how that clock is divided.
        total_units = sum(self._units(cue) for cue in cues) or 1.0
        word_units = [max(self._units(word["text"]), 1.0) for word in words]
        cumulative = []
        running = 0.0
        for units in word_units:
            running += units
            cumulative.append(running)
        word_total = running or 1.0

        aligned = []
        cue_running = 0.0
        previous_end = float(words[0]["start"])
        for index, cue in enumerate(cues):
            cue_running += self._units(cue)
            target = word_total * cue_running / total_units
            word_index = next((i for i, value in enumerate(cumulative) if value >= target), len(words) - 1)
            end = float(words[word_index]["end"])
            if index == len(cues) - 1:
                end = float(words[-1]["end"])
            end = max(end, previous_end + 0.05)
            aligned.append({"text": cue, "start": previous_end, "end": end})
            previous_end = end
        return aligned

    def _duration_fallback(self, cues: list[str], audio: Path) -> list[dict]:
        duration = self._probe_duration(audio)
        weights = [self._units(cue) for cue in cues]
        total = sum(weights) or 1.0
        cursor = 0.0
        aligned = []
        for index, (cue, weight) in enumerate(zip(cues, weights)):
            end = duration if index == len(cues) - 1 else cursor + duration * weight / total
            aligned.append({"text": cue, "start": cursor, "end": end})
            cursor = end
        return aligned

    @staticmethod
    def _units(text: str) -> float:
        cjk = len(re.findall(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", text))
        latin = len(re.findall(r"[A-Za-z0-9]+(?:[.,:/%-][A-Za-z0-9]+)*", text))
        return max(float(cjk + latin), 1.0)

    @staticmethod
    def _probe_duration(audio: Path) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
            check=True, capture_output=True, text=True,
        )
        return float(result.stdout.strip())
