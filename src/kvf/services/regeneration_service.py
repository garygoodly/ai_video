from __future__ import annotations

from pathlib import Path

from kvf.services.session_service import SessionService


class RegenerationService:
    """Invalidate selected outputs and their downstream dependencies safely."""

    ORDER = ("media", "voice", "subtitle", "timeline", "video")
    FILES = {
        "media": ("assets/media.json", "assets/rendered/*.jpg", "assets/source/*"),
        "voice": ("voice/narration.mp3", "voice/voice.json", "voice/cue_timing.json"),
        "subtitle": ("subtitle/subtitle.srt", "subtitle/subtitle.json"),
        "timeline": ("timeline/timeline.json",),
        "video": ("video/video.mp4", "video/scene_list.ffconcat"),
    }
    DEPENDENCIES = {
        "media": {"media", "timeline", "video"},
        "voice": {"voice", "subtitle", "timeline", "video"},
        "subtitle": {"subtitle", "video"},
        "timeline": {"timeline", "video"},
        "video": {"video"},
    }

    @classmethod
    def invalidate(
        cls,
        workspace: Path,
        selected: set[str],
        voice: str | None = None,
        voice_engine: str | None = None,
        voice_rate: str | None = None,
        voice_pitch: str | None = None,
        subtitle_settings: dict | None = None,
        subtitle_style: dict | None = None,
        media_settings: dict | None = None,
    ) -> set[str]:
        expanded: set[str] = set()
        for stage in selected:
            expanded.update(cls.DEPENDENCIES.get(stage, {stage}))

        for stage in cls.ORDER:
            if stage not in expanded:
                continue
            for pattern in cls.FILES[stage]:
                for path in workspace.glob(pattern):
                    if path.is_file():
                        path.unlink(missing_ok=True)

        metadata = SessionService._read_metadata(workspace)
        if voice_engine:
            metadata["voice_engine"] = voice_engine
        if voice:
            metadata["voice"] = voice
        if voice_rate is not None:
            metadata["voice_rate"] = voice_rate
        if voice_pitch is not None:
            metadata["voice_pitch"] = voice_pitch
        if subtitle_settings is not None:
            metadata["subtitle_settings"] = subtitle_settings
        if subtitle_style is not None:
            metadata["subtitle_style"] = subtitle_style
        if media_settings is not None:
            metadata["media_settings"] = media_settings
        SessionService._write_metadata(workspace, metadata)
        return expanded
