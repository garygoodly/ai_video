from __future__ import annotations

import re
import subprocess
from pathlib import Path


class ExactSubtitleService:
    """Create subtitles from the approved script text, never from ASR.

    This guarantees that names, Chinese characters, and Arabic numerals exactly
    match script.json. Timing is distributed over the narration duration using
    reading-weight estimates. Traditional Chinese is segmented at ， and 。,
    while the punctuation itself is not displayed.
    """

    CJK_LANGUAGES = {"zh-TW", "zh-CN", "ja-JP"}

    def __init__(
        self,
        language_code: str,
        max_characters: int = 18,
        min_characters: int = 6,
        max_words: int = 10,
        min_duration: float = 0.8,
    ) -> None:
        self.language_code = language_code
        self.is_cjk = language_code in self.CJK_LANGUAGES
        self.max_characters = max(6, int(max_characters))
        self.min_characters = max(1, min(int(min_characters), self.max_characters))
        self.max_words = max(3, int(max_words))
        self.min_duration = max(0.3, float(min_duration))

    def generate(self, narrations: list[str], audio: Path, output: Path) -> list[dict]:
        chunks: list[str] = []
        for narration in narrations:
            chunks.extend(self._segment(narration))
        chunks = [chunk for chunk in chunks if chunk.strip()]
        if not chunks:
            raise ValueError("The approved script contains no subtitle text.")

        total_duration = self._probe_duration(audio)
        weights = [self._weight(text) for text in chunks]
        total_weight = sum(weights) or float(len(chunks))

        cues: list[dict] = []
        cursor = 0.0
        for index, (text, weight) in enumerate(zip(chunks, weights)):
            if index == len(chunks) - 1:
                end = total_duration
            else:
                raw = total_duration * weight / total_weight
                end = min(total_duration, cursor + max(self.min_duration, raw))
            cues.append({"start": cursor, "end": max(end, cursor + 0.1), "text": text})
            cursor = end

        # Renormalize in case minimum durations pushed the cursor too far.
        scale = total_duration / cues[-1]["end"] if cues[-1]["end"] else 1.0
        for cue in cues:
            cue["start"] *= scale
            cue["end"] *= scale

        output.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for index, cue in enumerate(cues, start=1):
            lines.extend([
                str(index),
                f'{self._format(cue["start"])} --> {self._format(cue["end"])}',
                cue["text"],
                "",
            ])
        output.write_text("\n".join(lines), encoding="utf-8")
        return cues

    def _segment(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", "" if self.is_cjk else " ", text).strip()
        if self.language_code.startswith("zh"):
            # The punctuation defines the boundary but is intentionally hidden.
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
        # First split clauses that remain too long. Numeric values and Latin
        # identifiers are atomic, so 43682 and 0.16 are never cut apart.
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

        # Then merge isolated one- or two-character fragments with a neighbor.
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

    def _weight(self, text: str) -> float:
        if self.is_cjk:
            return max(1.0, len(text))
        return max(1.0, len(text.split()))

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
