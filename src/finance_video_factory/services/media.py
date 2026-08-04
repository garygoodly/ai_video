from __future__ import annotations
import os
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont

class MediaService:
    def __init__(self,width:int,height:int): self.width,self.height=width,height
    def acquire(self, query:str, title:str, output:Path) -> Path:
        key=os.getenv("PEXELS_API_KEY")
        if key:
            try:
                r=requests.get("https://api.pexels.com/v1/search",headers={"Authorization":key},params={"query":query,"per_page":1,"orientation":"landscape"},timeout=25)
                r.raise_for_status(); photos=r.json().get("photos",[])
                if photos:
                    img=requests.get(photos[0]["src"]["large2x"],timeout=30); img.raise_for_status()
                    output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(img.content); return output
            except Exception: pass
        return self._card(title,output)
    def _card(self,title:str,output:Path)->Path:
        output.parent.mkdir(parents=True,exist_ok=True)
        image=Image.new("RGB",(self.width,self.height),(15,20,30)); draw=ImageDraw.Draw(image)
        try: font=ImageFont.truetype("arial.ttf",72)
        except OSError: font=ImageFont.load_default()
        words=title.split(); lines=[]; current=[]
        for word in words:
            test=" ".join(current+[word])
            if draw.textlength(test,font=font)>self.width*.78 and current:
                lines.append(" ".join(current)); current=[word]
            else: current.append(word)
        if current: lines.append(" ".join(current))
        y=self.height/2-(len(lines)*90)/2
        for line in lines:
            box=draw.textbbox((0,0),line,font=font); x=(self.width-(box[2]-box[0]))/2
            draw.text((x,y),line,font=font,fill="white"); y+=90
        image.save(output,quality=92); return output
