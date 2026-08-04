from kvf.models.application import Application
from kvf.providers.ffmpeg_provider import FFmpegProvider
from kvf.repositories.timeline_repository import TimelineRepository
from kvf.steps.base_step import BaseStep


class GenerateVideoStep(BaseStep):
    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        output_dir = workspace / "video"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / "video.mp4"

        timeline = TimelineRepository().load(
            workspace / "timeline" / "timeline.json"
        )

        # Always overwrite the final render. This ensures sessions created by
        # older versions are repaired when resumed.
        FFmpegProvider().render(
            media_dir=workspace / "media",
            audio=workspace / "voice" / "narration.mp3",
            subtitle=workspace / "subtitle" / "subtitle.srt",
            output=output,
            timeline=timeline,
        )

        print(
            f"Video generated at 1920x1080 with {len(timeline.scenes)} "
            f"scenes and burned-in subtitles: {output}"
        )
