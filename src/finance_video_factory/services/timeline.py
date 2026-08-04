from __future__ import annotations
import re
from pathlib import Path
from finance_video_factory.models import Scene

class TimelineService:
    def assign(self, scenes:list[Scene], srt:Path)->list[Scene]:
        text=srt.read_text(encoding="utf-8")
        stamps=re.findall(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})",text)
        total=self._sec(stamps[-1][1]) if stamps else sum(s.estimated_duration_seconds for s in scenes)
        weights=[max(len(s.narration.split()),1) for s in scenes]; denom=sum(weights)
        for scene,w in zip(scenes,weights): scene.duration_seconds=max(total*w/denom,1.0)
        return scenes
    def _sec(self,t:str)->float:
        h,m,rest=t.split(":"); s,ms=rest.split(","); return int(h)*3600+int(m)*60+int(s)+int(ms)/1000
