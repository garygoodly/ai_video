from pathlib import Path
import subprocess


class FFmpegProvider:
    WIDTH = 1920
    HEIGHT = 1080
    FPS = 30

    def render(
        self,
        media_dir: Path,
        audio: Path,
        subtitle: Path,
        output: Path,
        timeline,
    ) -> None:
        if not timeline.scenes:
            raise ValueError("Timeline contains no scenes.")
        if not audio.exists():
            raise FileNotFoundError(f"Narration audio not found: {audio}")
        if not subtitle.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle}")

        output.parent.mkdir(parents=True, exist_ok=True)
        concat_file = output.parent / "scene_list.ffconcat"
        self._write_concat_file(concat_file, media_dir, timeline.scenes)

        subtitle_filter_path = self._escape_filter_path(subtitle.resolve())
        video_filter = (
            f"scale={self.WIDTH}:{self.HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={self.WIDTH}:{self.HEIGHT},"
            "setsar=1,"
            f"fps={self.FPS},"
            f"subtitles='{subtitle_filter_path}':"
            "force_style='FontName=Arial,FontSize=22,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "BorderStyle=1,Outline=2,Shadow=1,"
            "Alignment=2,MarginV=48'"
        )

        command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-i",
            str(audio),
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output),
        ]

        try:
            subprocess.run(command, check=True)
        finally:
            concat_file.unlink(missing_ok=True)

    @staticmethod
    def _write_concat_file(concat_file: Path, media_dir: Path, scenes) -> None:
        lines = ["ffconcat version 1.0"]
        last_image = None

        for scene in scenes:
            image = media_dir / scene.image
            if not image.exists():
                raise FileNotFoundError(
                    f"Scene {scene.id} image not found: {image}"
                )
            escaped = str(image.resolve()).replace("'", "'\\''")
            lines.append(f"file '{escaped}'")
            lines.append(f"duration {max(float(scene.duration_seconds), 0.1):.6f}")
            last_image = escaped

        # The concat demuxer requires the final file to be repeated so its
        # duration directive is honored.
        lines.append(f"file '{last_image}'")
        concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _escape_filter_path(path: Path) -> str:
        # FFmpeg filter syntax treats backslashes, colons and quotes specially.
        value = path.as_posix()
        value = value.replace("\\", "\\\\")
        value = value.replace(":", "\\:")
        value = value.replace("'", "\\'")
        return value
