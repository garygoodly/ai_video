from pathlib import Path
import subprocess
import tempfile

from kvf.models.timeline import Timeline


class FFmpegProvider:

    def render(
        self,
        media_dir: Path,
        audio: Path,
        subtitle: Path,
        output: Path,
        timeline: Timeline,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> None:
        """Render all timeline images, narration, and burned-in subtitles."""

        self._validate_inputs(
            media_dir=media_dir,
            audio=audio,
            subtitle=subtitle,
            timeline=timeline,
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.TemporaryDirectory(
            prefix="kvf_ffmpeg_"
        ) as temporary_dir:
            concat_file = Path(temporary_dir) / "images.ffconcat"
            self._write_concat_file(
                concat_file=concat_file,
                media_dir=media_dir,
                timeline=timeline,
            )

            subtitle_filter_path = self._escape_filter_path(
                subtitle.resolve()
            )

            video_filter = (
                f"scale={width}:{height}:"
                "force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                "setsar=1,"
                f"subtitles='{subtitle_filter_path}':"
                "force_style='Alignment=2,MarginV=54,FontSize=24,"
                "Outline=2,Shadow=1'"
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
                "-r",
                str(fps),
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
                "128k",
                "-ar",
                "48000",
                "-movflags",
                "+faststart",
                "-shortest",
                str(output),
            ]

            subprocess.run(
                command,
                check=True,
            )

    def _validate_inputs(
        self,
        media_dir: Path,
        audio: Path,
        subtitle: Path,
        timeline: Timeline,
    ) -> None:
        if not audio.exists():
            raise FileNotFoundError(
                f"Narration audio not found: {audio}"
            )

        if not subtitle.exists():
            raise FileNotFoundError(
                f"Subtitle file not found: {subtitle}"
            )

        if not timeline.scenes:
            raise ValueError(
                "Timeline contains no scenes."
            )

        missing_images = [
            media_dir / scene.image
            for scene in timeline.scenes
            if not (media_dir / scene.image).exists()
        ]

        if missing_images:
            missing = "\n".join(
                str(path)
                for path in missing_images
            )
            raise FileNotFoundError(
                f"Timeline images not found:\n{missing}"
            )

    def _write_concat_file(
        self,
        concat_file: Path,
        media_dir: Path,
        timeline: Timeline,
    ) -> None:
        lines = [
            "ffconcat version 1.0"
        ]

        for scene in timeline.scenes:
            image = (media_dir / scene.image).resolve()
            escaped_image = self._escape_concat_path(image)
            duration = max(
                scene.duration_seconds,
                0.04,
            )

            lines.append(
                f"file '{escaped_image}'"
            )
            lines.append(
                f"duration {duration:.6f}"
            )

        # The concat demuxer requires the final file to be repeated so its
        # duration is honored instead of being treated as a single frame.
        final_image = (
            media_dir / timeline.scenes[-1].image
        ).resolve()
        lines.append(
            f"file '{self._escape_concat_path(final_image)}'"
        )

        concat_file.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    def _escape_concat_path(
        self,
        path: Path,
    ) -> str:
        return path.as_posix().replace(
            "'",
            "'\\''",
        )

    def _escape_filter_path(
        self,
        path: Path,
    ) -> str:
        value = path.as_posix()
        value = value.replace(
            "\\",
            "/",
        )
        value = value.replace(
            ":",
            "\\:",
        )
        value = value.replace(
            "'",
            "\\'",
        )
        value = value.replace(
            "[",
            "\\[",
        )
        value = value.replace(
            "]",
            "\\]",
        )
        return value
