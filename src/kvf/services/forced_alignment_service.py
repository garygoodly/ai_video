from __future__ import annotations

import re
import subprocess
from pathlib import Path


class ForcedAlignmentService:
    """Align exact approved text to continuous narration audio.

    ASR text is never emitted. Whisper is only a timing sensor. Section-aware
    alignment respects the silent title-card gaps created during narration.
    """

    def align(self, exact_cues: list[str], audio: Path, language_code: str) -> list[dict]:
        if not exact_cues:
            return []
        try:
            anchors = self._whisper_anchors(audio, language_code)
            if anchors:
                return self._map_by_text_weight(exact_cues, anchors)
        except Exception as exc:
            print(
                "Forced alignment warning: Whisper timing unavailable "
                f"({exc}); using audio-duration fallback."
            )
        return self._duration_fallback(exact_cues, audio)

    def align_sections(
        self,
        exact_sections: list[list[str]],
        audio: Path,
        language_code: str,
        section_timings: list[dict],
    ) -> list[dict]:
        """Align each exact-text section only inside its measured speech window."""
        if not exact_sections:
            return []
        anchors: list[dict] = []
        try:
            anchors = self._whisper_anchors(audio, language_code)
        except Exception as exc:
            print(
                "Section alignment warning: Whisper timing unavailable "
                f"({exc}); using measured section-duration fallback."
            )

        output: list[dict] = []
        for index, cues in enumerate(exact_sections):
            if not cues:
                continue
            if index >= len(section_timings):
                raise ValueError("Narration section timing does not match the approved script sections.")
            timing = section_timings[index]
            start = float(timing["speech_start"])
            end = float(timing["speech_end"])
            if end <= start:
                continue

            local_words = [
                word for word in anchors
                if start - 0.10 <= (float(word["start"]) + float(word["end"])) / 2.0 <= end + 0.10
            ]
            if local_words:
                aligned = self._map_by_text_weight(cues, local_words, clamp_start=start, clamp_end=end)
            else:
                aligned = self._proportional_window(cues, start, end)
            output.extend(aligned)
        return output

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
                    words.append(
                        {
                            "text": text,
                            "start": float(word["start"]),
                            "end": float(word["end"]),
                        }
                    )
        return words

    def _map_by_text_weight(
        self,
        cues: list[str],
        words: list[dict],
        clamp_start: float | None = None,
        clamp_end: float | None = None,
    ) -> list[dict]:
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
        previous_end = max(float(words[0]["start"]), clamp_start or 0.0)
        for index, cue in enumerate(cues):
            cue_running += self._units(cue)
            target = word_total * cue_running / total_units
            word_index = next(
                (i for i, value in enumerate(cumulative) if value >= target),
                len(words) - 1,
            )
            end = float(words[word_index]["end"])
            if index == len(cues) - 1:
                end = float(words[-1]["end"])
            if clamp_end is not None:
                end = min(end, clamp_end)
            end = max(end, previous_end + 0.05)
            aligned.append({"text": cue, "start": previous_end, "end": end})
            previous_end = end
        return aligned

    def _duration_fallback(self, cues: list[str], audio: Path) -> list[dict]:
        return self._proportional_window(cues, 0.0, self._probe_duration(audio))

    def _proportional_window(self, cues: list[str], start: float, end: float) -> list[dict]:
        weights = [self._units(cue) for cue in cues]
        total = sum(weights) or 1.0
        cursor = start
        aligned = []
        duration = max(end - start, 0.05)
        for index, (cue, weight) in enumerate(zip(cues, weights)):
            cue_end = end if index == len(cues) - 1 else cursor + duration * weight / total
            aligned.append({"text": cue, "start": cursor, "end": cue_end})
            cursor = cue_end
        return aligned

    @staticmethod
    def _units(text: str) -> float:
        cjk = len(re.findall(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", text))
        latin = len(re.findall(r"[A-Za-z0-9]+(?:[.,:/%-][A-Za-z0-9]+)*", text))
        return max(float(cjk + latin), 1.0)

    @staticmethod
    def _probe_duration(audio: Path) -> float:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(audio),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
