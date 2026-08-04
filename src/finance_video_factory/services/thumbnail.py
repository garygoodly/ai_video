from __future__ import annotations
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
class ThumbnailService:
    def create(self,title:str,output:Path)->Path:
        im=Image.new("RGB",(1280,720),(10,18,32)); d=ImageDraw.Draw(im)
        try: font=ImageFont.truetype("arialbd.ttf",76)
        except OSError: font=ImageFont.load_default()
        words=title.upper().split(); lines=[]; cur=[]
        for w in words:
            if d.textlength(" ".join(cur+[w]),font=font)>1050 and cur: lines.append(" ".join(cur)); cur=[w]
            else: cur.append(w)
        if cur: lines.append(" ".join(cur))
        y=150
        for line in lines[:4]: d.text((95,y),line,font=font,fill="white",stroke_width=3,stroke_fill="black"); y+=105
        d.rectangle((95,590,690,645),fill=(190,30,45)); d.text((115,596),"DAILY MARKET BRIEF",font=font,fill="white")
        output.parent.mkdir(parents=True,exist_ok=True); im.save(output,quality=95); return output
