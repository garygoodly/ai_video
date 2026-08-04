from __future__ import annotations
import tempfile
from pathlib import Path
from finance_video_factory.models import Scene
from finance_video_factory.utils import ensure_binary, run

class RenderService:
    def render(self,scenes:list[Scene],audio:Path,subtitle:Path,output:Path,width:int,height:int,fps:int,crf:int,font_size:int)->Path:
        ensure_binary("ffmpeg"); output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="fvf_") as td:
            concat=Path(td)/"images.ffconcat"; lines=["ffconcat version 1.0"]
            for scene in scenes:
                image=Path(scene.image).resolve().as_posix().replace("'","'\''")
                lines += [f"file '{image}'",f"duration {max(scene.duration_seconds or 1,.04):.6f}"]
            image=Path(scenes[-1].image).resolve().as_posix().replace("'","'\''"); lines.append(f"file '{image}'")
            concat.write_text("\n".join(lines)+"\n",encoding="utf-8")
            sub=subtitle.resolve().as_posix().replace(":", "\\:").replace("'", "\\'")
            vf=(f"scale={width}:{height}:force_original_aspect_ratio=decrease," f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1," f"subtitles='{sub}':force_style='Alignment=2,MarginV=48,FontSize={font_size},Outline=2,Shadow=1'")
            run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(audio),"-vf",vf,"-r",str(fps),"-c:v","libx264","-preset","medium","-crf",str(crf),"-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-ar","48000","-movflags","+faststart","-shortest",str(output)])
        return output
