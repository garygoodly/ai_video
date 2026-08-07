from __future__ import annotations

import re
from pathlib import Path

import whisper

from kvf.providers.subtitle_provider import SubtitleProvider


class WhisperProvider(SubtitleProvider):
    """Generate short language-aware SRT cues from Whisper word timestamps."""

    SENTENCE_END = re.compile(r"[.!?。！？]+$")
    SOFT_BREAK = re.compile(r"[,;:，、；：]$")

    def __init__(
        self,
        model: str = "tiny",
        max_words: int = 10,
        max_characters: int = 58,
        max_duration_seconds: float = 4.5,
        language: str | None = None,
    ) -> None:
        self.model = whisper.load_model(model)
        self.max_words = max(4, int(max_words))
        self.max_characters = max(12, int(max_characters))
        self.max_duration_seconds = max(1.5, float(max_duration_seconds))
        self.language = language
        self.is_cjk = (language or "").lower() in {"zh", "ja", "ko", "zh-tw", "ja-jp"}

    def generate(self, audio: Path, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        kwargs = {"word_timestamps": True}
        if self.language:
            kwargs["language"] = self.language
        result = self.model.transcribe(str(audio), **kwargs)
        cues = self._sentence_cues(result.get("segments", []))

        srt_path = output_dir / "subtitle.srt"
        with srt_path.open("w", encoding="utf-8") as stream:
            for index, cue in enumerate(cues, start=1):
                stream.write(f"{index}\n")
                stream.write(f"{self._format(cue['start'])} --> {self._format(cue['end'])}\n")
                stream.write(f"{cue['text']}\n\n")

    def _sentence_cues(self, segments: list[dict]) -> list[dict]:
        words: list[dict] = []
        for segment in segments:
            segment_words = segment.get("words") or []
            if segment_words:
                words.extend(segment_words)
            else:
                text = str(segment.get("text", "")).strip()
                if text:
                    words.append({
                        "word": text,
                        "start": float(segment.get("start", 0.0)),
                        "end": float(segment.get("end", 0.0)),
                    })

        cues: list[dict] = []
        current: list[dict] = []
        for item in words:
            token = str(item.get("word", "")).strip()
            if not token:
                continue
            current.append({
                "word": token,
                "start": float(item.get("start", 0.0)),
                "end": float(item.get("end", item.get("start", 0.0))),
            })
            text = self._join_tokens([word["word"] for word in current])
            duration = current[-1]["end"] - current[0]["start"]
            reached_sentence_end = bool(self.SENTENCE_END.search(token))
            reached_limit = (
                len(current) >= self.max_words
                or len(text) >= self.max_characters
                or duration >= self.max_duration_seconds
            )
            if reached_sentence_end or reached_limit:
                split_at = len(current)
                if reached_limit and not reached_sentence_end:
                    lower_bound = max(1, len(current) // 2)
                    for index in range(len(current) - 1, lower_bound - 1, -1):
                        if self.SOFT_BREAK.search(current[index]["word"]):
                            split_at = index + 1
                            break
                cue_words = current[:split_at]
                current = current[split_at:]
                cues.append(self._make_cue(cue_words))

        if current:
            cues.append(self._make_cue(current))

        for index, cue in enumerate(cues):
            cue["end"] = max(cue["end"], cue["start"] + 0.40)
            if index + 1 < len(cues):
                next_start = cues[index + 1]["start"]
                cue["end"] = min(cue["end"], max(cue["start"] + 0.40, next_start - 0.03))
        return cues

    def _make_cue(self, words: list[dict]) -> dict:
        text = self._join_tokens([word["word"] for word in words])
        cleaned = re.sub(r"\s+", " " if not self.is_cjk else "", text).strip()
        if self.is_cjk:
            cleaned = re.sub(r"[，、；：！？,.!?;:]+$", "。", cleaned)
            if not cleaned.endswith("。"):
                cleaned += "。"
        else:
            cleaned = re.sub(r"[,:;!?]+$", ".", cleaned)
            if not cleaned.endswith("."):
                cleaned += "."
        return {
            "start": float(words[0]["start"]),
            "end": float(words[-1]["end"]),
            "text": cleaned,
        }

    def _join_tokens(self, tokens: list[str]) -> str:
        if self.is_cjk:
            return "".join(tokens).strip()
        text = " ".join(tokens)
        return re.sub(r"\s+([,.;:!?])", r"\1", text).strip()

    @staticmethod
    def _format(seconds: float) -> str:
        milliseconds = max(0, round(seconds * 1000))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
