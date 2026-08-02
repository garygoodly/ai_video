from kvf.models.application import Application
from kvf.models.subtitle import Subtitle
from kvf.providers.whisper_provider import WhisperProvider
from kvf.repositories.subtitle_repository import SubtitleRepository
from kvf.steps.base_step import BaseStep


class GenerateSubtitleStep(BaseStep):

    def execute(
        self,
        application: Application,
    ):

        workspace = application.project.workspace

        voice = (
            workspace
            / "voice"
            / "narration.mp3"
        )

        subtitle_dir = (
            workspace
            / "subtitle"
        )

        srt = (
            subtitle_dir
            / "subtitle.srt"
        )

        metadata = (
            subtitle_dir
            / "subtitle.json"
        )

        if (
            srt.exists()
            and metadata.exists()
        ):

            print(
                "Subtitle already exists. [SKIP]"
            )

            return

        provider = WhisperProvider()

        provider.generate(
            voice,
            subtitle_dir,
        )

        SubtitleRepository().save(

            Subtitle(
                provider="whisper",
                file="subtitle.srt",
            ),

            metadata,
        )

        print(
            f"Subtitle generated: {srt}"
        )