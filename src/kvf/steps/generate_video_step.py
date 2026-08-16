from kvf.models.application import Application
from kvf.providers.ffmpeg_provider import FFmpegProvider
from kvf.repositories.timeline_repository import TimelineRepository
from kvf.services.session_service import SessionService
from kvf.steps.base_step import BaseStep


class GenerateVideoStep(BaseStep):
    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        output_dir = workspace / "video"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / "video.mp4"
        timeline = TimelineRepository().load(workspace / "timeline" / "timeline.json")
        metadata = SessionService._read_metadata(workspace)

        FFmpegProvider().render(
            media_dir=workspace / "assets" / "rendered",
            audio=workspace / "voice" / "narration.mp3",
            subtitle=workspace / "subtitle" / "subtitle.srt",
            output=output,
            timeline=timeline,
            subtitle_style=metadata.get("subtitle_style", {}),
        )
        subtitle_state = "with subtitles" if metadata.get("subtitles_enabled", True) else "without subtitles"
        print(
            f"Video generated at 1920x1080 with {len(timeline.scenes)} scenes "
            f"{subtitle_state}: {output}"
        )
