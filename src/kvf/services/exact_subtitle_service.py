from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


class ExactSubtitleService:
    """Create deterministic subtitles from the approved script.

    Text never comes from ASR, so names, Chinese characters and Arabic numerals
    remain exactly as approved. Segmentation also preserves whether a cue break
    is inside a sentence or at a real sentence boundary. The voice step uses
    that information to avoid unnatural pauses between subtitle-only chunks.
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
        return [unit["text"] for unit in self.segment_units(sections)]

    def segment_units(self, sections: list[str]) -> list[dict]:
        """Return subtitle/TTS units with semantic pause information.

        ``boundary_after`` is:
        - ``intra``: the next cue is still part of the same written sentence.
          This includes comma splits and length-only subtitle splits.
        - ``sentence``: the written sentence really ended (period, !, ?, etc.).

        Punctuation used as a boundary is intentionally omitted from the cue
        text for CJK editions, matching the subtitle-display policy.
        """
        units: list[dict] = []
        for section in sections:
            units.extend(self._segment_units(section))
        return [unit for unit in units if str(unit.get("text", "")).strip()]

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

    def _segment_units(self, text: str) -> list[dict]:
        normalized = re.sub(r"\s+", "" if self.is_cjk else " ", text).strip()
        if not normalized:
            return []

        if self.language_code.startswith("zh"):
            return self._segment_cjk_with_boundaries(normalized, comma_chars="，；：", sentence_chars="。！？")
        if self.language_code.startswith("ja"):
            return self._segment_cjk_with_boundaries(normalized, comma_chars="、，；：", sentence_chars="。！？")
        return self._segment_latin_with_boundaries(normalized)

    def _segment_cjk_with_boundaries(
        self,
        text: str,
        *,
        comma_chars: str,
        sentence_chars: str,
    ) -> list[dict]:
        boundary_chars = re.escape(comma_chars + sentence_chars)
        parts = re.split(f"([{boundary_chars}])", text)
        units: list[dict] = []

        index = 0
        while index < len(parts):
            clause = parts[index].strip()
            delimiter = parts[index + 1] if index + 1 < len(parts) else ""
            index += 2
            if not clause:
                continue

            pieces = self._balance_cjk([clause])
            for piece_index, piece in enumerate(pieces):
                is_last_piece = piece_index == len(pieces) - 1
                if not is_last_piece:
                    boundary_after = "intra"
                elif delimiter and delimiter in sentence_chars:
                    boundary_after = "sentence"
                else:
                    # Comma-like punctuation or a section ending without a
                    # sentence mark should not create a large audible pause.
                    boundary_after = "intra"
                units.append({"text": piece, "boundary_after": boundary_after})

        if units:
            # A section boundary is a real narration boundary unless the source
            # explicitly continues into the next section. Keep it short, but
            # don't run sections together with zero separation.
            units[-1]["boundary_after"] = "sentence"
        return units

    def _segment_latin_with_boundaries(self, text: str) -> list[dict]:
        sentence_matches = list(re.finditer(r".*?(?:[.!?]+(?=\s|$)|$)", text))
        units: list[dict] = []
        for match in sentence_matches:
            sentence = match.group(0).strip()
            if not sentence:
                continue
            words = sentence.rstrip(".!?").split()
            sentence_chunks: list[str] = []
            while words:
                sentence_chunks.append(" ".join(words[: self.max_words]))
                words = words[self.max_words :]
            for index, chunk in enumerate(sentence_chunks):
                units.append({
                    "text": chunk,
                    "boundary_after": "sentence" if index == len(sentence_chunks) - 1 else "intra",
                })
        if units:
            units[-1]["boundary_after"] = "sentence"
        return units

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
