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

        output_dir = (
            workspace
            / "video"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output = (
            output_dir
            / "video.mp4"
        )

        if output.exists():

            print(
                "Video already exists. [SKIP]"
            )

            return

        timeline = TimelineRepository().load(

            workspace

            / "timeline"

            / "timeline.json"

        )

        provider = FFmpegProvider()

        provider.render(

            workspace / "media",

            workspace / "voice" / "narration.mp3",

            output,

            timeline.total_duration_seconds,

        )

        print(
            f"Video generated: {output}"
        )