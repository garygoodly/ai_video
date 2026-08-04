from kvf.models.application import Application
from kvf.models.media import Media
from kvf.providers.resilient_media_provider import ResilientMediaProvider
from kvf.repositories.media_repository import MediaRepository
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.steps.base_step import BaseStep


class DownloadMediaStep(BaseStep):
    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        storyboard = StoryboardRepository().load(
            workspace / "storyboard" / "storyboard.json"
        )
        provider = ResilientMediaProvider()
        media_dir = workspace / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        media_json = media_dir / "media.json"

        existing_by_scene = {}
        if media_json.exists():
            existing_media = MediaRepository().load(media_json)
            existing_by_scene = {
                asset.scene: asset for asset in existing_media.assets
            }

        assets = []
        for scene in storyboard.scenes:
            output = media_dir / f"{scene.id:04}.jpg"
            existing_asset = existing_by_scene.get(scene.id)

            if output.exists() and existing_asset is not None:
                if provider.is_generated_fallback(existing_asset):
                    print(
                        f"Scene {scene.id} uses an old generated fallback; "
                        "searching online sources again."
                    )
                    output.unlink(missing_ok=True)
                elif provider.normalize_existing(output):
                    existing_asset.width = provider.TARGET_WIDTH
                    existing_asset.height = provider.TARGET_HEIGHT
                    assets.append(existing_asset)
                    print(
                        f"Scene {scene.id} cached image validated and "
                        "normalized to 1920x1080. [SKIP DOWNLOAD]"
                    )
                    continue

                print(
                    f"Scene {scene.id} cached image is invalid; "
                    "deleting and downloading a replacement."
                )
                output.unlink(missing_ok=True)

            asset = provider.download(scene, output)
            assets.append(asset)

            # Persist after every scene so an interrupted run can resume safely.
            MediaRepository().save(Media(assets=assets), media_json)

        media = Media(assets=assets)
        MediaRepository().save(media, media_json)
        print(
            f"Prepared {media.count} validated media assets at "
            "exactly 1920x1080."
        )
