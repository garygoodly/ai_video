import asyncio
from pathlib import Path

import edge_tts

from kvf.providers.tts_provider import TTSProvider


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS provider with explicit native word timing support."""

    def __init__(
        self,
        voice: str = "en-US-AndrewNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def _generate(self, text: str, output: Path):
        communicate = edge_tts.Communicate(
            text,
            self.voice,
            rate=self.rate,
            pitch=self.pitch,
        )
        await communicate.save(str(output))

    async def _generate_with_boundaries(self, text: str, output: Path):
        """Generate audio and capture Edge's native WordBoundary events.

        Newer edge-tts versions default to SentenceBoundary. We explicitly
        request WordBoundary because subtitle and storyboard synchronization
        require fine-grained anchors inside each long narration section.
        """
        communicate = edge_tts.Communicate(
            text,
            self.voice,
            rate=self.rate,
            pitch=self.pitch,
            boundary="WordBoundary",
        )

        boundaries = []
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("wb") as audio_file:
            async for chunk in communicate.stream():
                chunk_type = chunk.get("type")

                if chunk_type == "audio":
                    audio_file.write(chunk["data"])

                elif chunk_type == "WordBoundary":
                    start = float(chunk.get("offset", 0)) / 10_000_000.0
                    duration = float(chunk.get("duration", 0)) / 10_000_000.0
                    text_value = str(chunk.get("text", "")).strip()

                    if not text_value:
                        continue

                    boundaries.append(
                        {
                            "text": text_value,
                            "start": start,
                            "end": start + max(duration, 0.0),
                        }
                    )

        if not boundaries:
            raise RuntimeError(
                "Edge TTS generated audio but returned zero WordBoundary "
                "events. Native timing cannot be used safely."
            )

        return boundaries

    def generate(self, text: str, output: Path):
        asyncio.run(self._generate(text, output))

    def generate_with_boundaries(self, text: str, output: Path):
        return asyncio.run(self._generate_with_boundaries(text, output))
