from pathlib import Path

from kvf.models.application import Application
from kvf.models.media import Media
from kvf.providers.wikimedia_provider import WikimediaProvider
from kvf.repositories.media_repository import MediaRepository
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.steps.base_step import BaseStep


class DownloadMediaStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        workspace = application.project.workspace

        storyboard = StoryboardRepository().load(
            workspace
            / "storyboard"
            / "storyboard.json"
        )

        provider = WikimediaProvider()

        assets = []

        media_dir = workspace / "media"

        media_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for scene in storyboard.scenes:

            filename = f"{scene.id:04}.jpg"

            output = media_dir / filename

            if output.exists():
                print(
                    f"Scene {scene.id} already downloaded. [SKIP]"
                )

                continue

            asset = provider.download(
                scene,
                output,
            )

            assets.append(asset)

        media = Media(
            assets=assets,
        )

        MediaRepository().save(
            media,
            media_dir / "media.json",
        )

        print(
            f"Downloaded {media.count} media assets."
        )