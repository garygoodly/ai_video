import asyncio
from pathlib import Path

import edge_tts

from kvf.providers.tts_provider import TTSProvider


class EdgeTTSProvider(TTSProvider):
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
            text, self.voice, rate=self.rate, pitch=self.pitch
        )
        await communicate.save(str(output))

    def generate(self, text: str, output: Path):
        asyncio.run(self._generate(text, output))
