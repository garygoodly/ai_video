from pathlib import Path

from kvf.models.media import MediaAsset
from kvf.models.media_search_result import MediaSearchResult
from kvf.models.storyboard import StoryboardScene
from kvf.providers.media_provider import MediaProvider
from kvf.services.image_download_service import ImageDownloadService


class MediaSearchService:

    def __init__(
        self,
        provider: MediaProvider,
    ):
        self.provider = provider

    def download_scene(
        self,
        scene: StoryboardScene,
        output: Path,
    ) -> MediaAsset:

        result = self.provider.search(
            scene.visual.query
        )

        ImageDownloadService().download(
            result.url,
            output,
        )

        return MediaAsset(
            scene=scene.id,
            provider=result.provider,
            query=scene.visual.query,
            file=output.name,
            width=result.width,
            height=result.height,
            author=result.author,
            license=result.license,
            source_url=result.source_url
            or result.url,
        )