from kvf.models.application import Application
from kvf.providers.ffmpeg_provider import FFmpegProvider
from kvf.repositories.timeline_repository import TimelineRepository
from kvf.steps.base_step import BaseStep


class GenerateVideoStep(BaseStep):

    def execute(
        self,
        application: Application,
    ):
        workspace = application.project.workspace

        output_dir = workspace / "video"
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output = output_dir / "video.mp4"

        timeline = TimelineRepository().load(
            workspace
            / "timeline"
            / "timeline.json"
        )

        provider = FFmpegProvider()
        provider.render(
            media_dir=workspace / "media",
            audio=workspace / "voice" / "narration.mp3",
            subtitle=workspace / "subtitle" / "subtitle.srt",
            output=output,
            timeline=timeline,
            width=1920,
            height=1080,
            fps=30,
        )

        print(
            f"Video generated: {output}"
        )
