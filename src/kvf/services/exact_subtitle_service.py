from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


class ExactSubtitleService:
    """Create deterministic subtitles from the approved script.

    Text never comes from ASR, so names, Chinese characters and Arabic numerals
    remain exactly as approved. When cue timing produced during TTS exists, it
    is used directly; this keeps subtitles aligned after any voice-speed change.
    """

    def __init__(
        self,
        language_code: str,
        max_characters: int = 18,
        min_characters: int = 6,
        max_words: int = 10,
    ) -> None:
        self.language_code = language_code
        self.max_characters = int(max_characters)
        self.min_characters = int(min_characters)
        self.max_words = int(max_words)
        self.is_cjk = language_code.startswith(("zh", "ja"))

    def segment_sections(self, sections: list[str]) -> list[str]:
        cues: list[str] = []
        for section in sections:
            cues.extend(self._segment(section))
        return [cue for cue in cues if cue.strip()]

    def generate(
        self,
        sections: list[str],
        audio: Path,
        output: Path,
        timing_file: Path | None = None,
    ) -> list[dict]:
        if timing_file and timing_file.exists():
            cues = json.loads(timing_file.read_text(encoding="utf-8"))
            self._validate_timing_text(cues, self.segment_sections(sections))
        else:
            cues = self._proportional_timing(self.segment_sections(sections), audio)
        self._write_srt(cues, output)
        return cues

    def _validate_timing_text(self, cues: list[dict], expected: list[str]) -> None:
        actual = [str(cue.get("text", "")) for cue in cues]
        if actual != expected:
            raise ValueError(
                "Voice cue timing does not match the approved script. "
                "Regenerate the narration voice before generating subtitles."
            )

    def _proportional_timing(self, segments: list[str], audio: Path) -> list[dict]:
        duration = self._probe_duration(audio)
        weights = [self._weight(text) for text in segments]
        total = sum(weights) or 1.0
        cursor = 0.0
        cues = []
        for index, (text, weight) in enumerate(zip(segments, weights)):
            end = duration if index == len(segments) - 1 else cursor + duration * weight / total
            cues.append({"text": text, "start": cursor, "end": end})
            cursor = end
        return cues

    def _segment(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", "" if self.is_cjk else " ", text).strip()
        if self.language_code.startswith("zh"):
            clauses = [part.strip() for part in re.split(r"[，。！？；：]+", normalized) if part.strip()]
            return self._balance_cjk(clauses)
        if self.language_code.startswith("ja"):
            clauses = [part.strip() for part in re.split(r"[、。！？；：]+", normalized) if part.strip()]
            return self._balance_cjk(clauses)

        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
        chunks: list[str] = []
        for sentence in sentences:
            words = sentence.rstrip(".!?").split()
            while words:
                chunks.append(" ".join(words[: self.max_words]))
                words = words[self.max_words :]
        return chunks

    def _balance_cjk(self, clauses: list[str]) -> list[str]:
        pieces: list[str] = []
        for clause in clauses:
            atoms = re.findall(r"[A-Za-z]+(?:[._/-][A-Za-z0-9]+)*|\d+(?:[.,]\d+)*%?|.", clause)
            current = ""
            for atom in atoms:
                if current and len(current) + len(atom) > self.max_characters:
                    pieces.append(current)
                    current = atom
                else:
                    current += atom
            if current:
                pieces.append(current)

        balanced: list[str] = []
        pending = ""
        for piece in pieces:
            if pending:
                piece = pending + piece
                pending = ""
            if len(piece) < self.min_characters:
                if balanced and len(balanced[-1]) + len(piece) <= self.max_characters:
                    balanced[-1] += piece
                else:
                    pending = piece
            else:
                balanced.append(piece)
        if pending:
            if balanced:
                balanced[-1] += pending
            else:
                balanced.append(pending)
        return balanced

    def write_cues(self, cues: list[dict], output: Path) -> None:
        """Write already-aligned exact-text cues as SRT."""
        self._write_srt(cues, output)

    def _write_srt(self, cues: list[dict], output: Path) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for index, cue in enumerate(cues, start=1):
            lines.extend([
                str(index),
                f'{self._format(float(cue["start"]))} --> {self._format(float(cue["end"]))}',
                str(cue["text"]),
                "",
            ])
        output.write_text("\n".join(lines), encoding="utf-8")

    def _weight(self, text: str) -> float:
        return max(1.0, len(text) if self.is_cjk else len(text.split()))

    @staticmethod
    def _probe_duration(audio: Path) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
            check=True, capture_output=True, text=True,
        )
        duration = float(result.stdout.strip())
        if duration <= 0:
            raise ValueError("Narration audio duration must be positive.")
        return duration

    @staticmethod
    def _format(seconds: float) -> str:
        milliseconds = max(0, round(seconds * 1000))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
