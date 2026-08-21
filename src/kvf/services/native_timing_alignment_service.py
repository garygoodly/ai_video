from __future__ import annotations

import re
from typing import Iterable


class NativeTimingAlignmentService:
    """Map approved text spans onto native TTS word-boundary timestamps."""

    @staticmethod
    def normalize(text: str) -> str:
        # Keep letters, numbers, CJK and percent/decimal content; punctuation
        # is not needed to locate a spoken span.
        return re.sub(
            r"[^0-9A-Za-z\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af%]+",
            "",
            text,
        ).casefold()

    def align_texts(
        self,
        texts: Iterable[str],
        words: list[dict],
        fallback_start: float,
        fallback_end: float,
    ) -> list[dict]:
        texts = [str(text).strip() for text in texts if str(text).strip()]
        if not texts:
            return []
        usable = [word for word in words if self.normalize(str(word.get("text", "")))]
        if not usable:
            return self._proportional(texts, fallback_start, fallback_end)

        stream = ""
        ranges = []
        for word in usable:
            token = self.normalize(str(word.get("text", "")))
            start_index = len(stream)
            stream += token
            ranges.append((start_index, len(stream), word))

        results = []
        search_cursor = 0
        for text in texts:
            target = self.normalize(text)
            if not target:
                continue
            found = stream.find(target, search_cursor)
            if found < 0:
                # TTS can normalize a number or abbreviation differently.
                # Use monotonic character coverage rather than resetting the
                # clock or using the displayed ASR/TTS token text.
                found = min(search_cursor, len(stream))
                target_end = min(len(stream), found + max(len(target), 1))
            else:
                target_end = found + len(target)

            overlapping = [
                word for left, right, word in ranges
                if right > found and left < target_end
            ]
            if overlapping:
                start = float(overlapping[0]["start"])
                end = float(overlapping[-1]["end"])
            else:
                start = results[-1]["end"] if results else fallback_start
                end = start
            results.append({"text": text, "start": start, "end": max(end, start + 0.03)})
            search_cursor = max(target_end, search_cursor)

        if not results:
            return self._proportional(texts, fallback_start, fallback_end)
        return results

    @staticmethod
    def _proportional(texts: list[str], start: float, end: float) -> list[dict]:
        weights = [max(len(text), 1) for text in texts]
        total = sum(weights) or 1
        cursor = start
        result = []
        for index, (text, weight) in enumerate(zip(texts, weights)):
            item_end = end if index == len(texts) - 1 else cursor + (end - start) * weight / total
            result.append({"text": text, "start": cursor, "end": max(item_end, cursor + 0.03)})
            cursor = item_end
        return result
