from pathlib import Path
import subprocess


class FFmpegProvider:

    def render(
        self,
        media_dir: Path,
        audio: Path,
        output: Path,
        duration: float,
    ):

        image = media_dir / "0001.jpg"

        command = [

            "ffmpeg",

            "-y",

            "-loop", "1",

            "-i", str(image),

            "-i", str(audio),

            "-c:v", "libx264",

            "-t", str(duration),

            "-pix_fmt", "yuv420p",

            "-c:a", "aac",

            "-shortest",

            str(output),
        ]

        subprocess.run(
            command,
            check=True,
        )