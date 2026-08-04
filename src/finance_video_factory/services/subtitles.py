from __future__ import annotations
from pathlib import Path
import whisper

class SubtitleService:
    def transcribe(self,audio:Path,output:Path,model_name:str)->Path:
        model=whisper.load_model(model_name)
        result=model.transcribe(str(audio),fp16=False)
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("w",encoding="utf-8") as f:
            for i,s in enumerate(result["segments"],1):
                f.write(f"{i}\n{self._ts(s['start'])} --> {self._ts(s['end'])}\n{s['text'].strip()}\n\n")
        return output
    def _ts(self,v:float)->str:
        ms=int(round(v*1000)); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
