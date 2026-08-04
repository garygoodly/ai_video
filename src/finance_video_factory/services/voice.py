from __future__ import annotations
import asyncio
from pathlib import Path
import edge_tts

class VoiceService:
    def synthesize(self,text:str,output:Path,voice:str,rate:str)->Path:
        output.parent.mkdir(parents=True,exist_ok=True)
        asyncio.run(edge_tts.Communicate(text=text,voice=voice,rate=rate).save(str(output)))
        return output
