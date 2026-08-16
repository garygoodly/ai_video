from pathlib import Path
import subprocess


class FFmpegProvider:
    WIDTH = 1920
    HEIGHT = 1080
    FPS = 30

    STYLE_PRESETS = {
        "Compact": {"font_size": 15, "outline": 2, "margin_v": 34},
        "Standard": {"font_size": 18, "outline": 2, "margin_v": 38},
        "Large": {"font_size": 22, "outline": 3, "margin_v": 42},
    }

    def render(
        self,
        media_dir: Path,
        audio: Path,
        subtitle: Path,
        output: Path,
        timeline,
        subtitle_style: dict | None = None,
    ) -> None:
        if not timeline.scenes:
            raise ValueError("Timeline contains no scenes.")
        if not audio.exists():
            raise FileNotFoundError(f"Narration audio not found: {audio}")
        # Subtitle burning is optional. An absent/empty SRT means narration-only video.

        output.parent.mkdir(parents=True, exist_ok=True)
        concat_file = output.parent / "scene_list.ffconcat"
        self._write_concat_file(concat_file, media_dir, timeline.scenes)

        style = dict(subtitle_style or {})
        preset_name = style.get("preset", "Compact")
        preset = self.STYLE_PRESETS.get(preset_name, self.STYLE_PRESETS["Compact"])
        font_name = str(style.get("font_name", "Arial")).replace("'", "")
        font_size = int(style.get("font_size", preset["font_size"]))
        margin_v = int(style.get("margin_v", preset["margin_v"]))
        outline = int(style.get("outline", preset["outline"]))

        filters = [
            f"scale={self.WIDTH}:{self.HEIGHT}:force_original_aspect_ratio=increase",
            f"crop={self.WIDTH}:{self.HEIGHT}",
            "setsar=1",
            f"fps={self.FPS}",
        ]
        if subtitle.exists() and subtitle.stat().st_size > 0:
            subtitle_filter_path = self._escape_filter_path(subtitle.resolve())
            force_style = (
                f"FontName={font_name},FontSize={font_size},"
                "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                f"BorderStyle=1,Outline={outline},Shadow=0,"
                f"Alignment=2,MarginV={margin_v}"
            )
            filters.append(
                f"subtitles='{subtitle_filter_path}':force_style='{force_style}'"
            )
        video_filter = ",".join(filters)

        command = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-i", str(audio), "-vf", video_filter,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-movflags", "+faststart", "-shortest", str(output),
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
                raise FileNotFoundError(f"Scene {scene.id} image not found: {image}")
            escaped = str(image.resolve()).replace("'", "'\\''")
            lines.append(f"file '{escaped}'")
            lines.append(f"duration {max(float(scene.duration_seconds), 0.1):.6f}")
            last_image = escaped
        lines.append(f"file '{last_image}'")
        concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _escape_filter_path(path: Path) -> str:
        value = path.as_posix()
        value = value.replace("\\", "\\\\")
        value = value.replace(":", "\\:")
        value = value.replace("'", "\\'")
        return value
