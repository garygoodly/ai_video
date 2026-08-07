from __future__ import annotations

import shutil

from kvf.models.application import Application
from kvf.models.media import Media
from kvf.providers.market_chart_provider import MarketChartProvider
from kvf.providers.resilient_media_provider import ResilientMediaProvider
from kvf.repositories.media_repository import MediaRepository
from kvf.repositories.research_repository import ResearchRepository
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.services.session_service import SessionService
from kvf.steps.base_step import BaseStep


class DownloadMediaStep(BaseStep):
    """Prepare precise visuals, normally one stable visual per topic section."""

    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        storyboard = StoryboardRepository().load(
            workspace / "storyboard" / "storyboard.json"
        )
        research_sources = []
        research_path = workspace / "research" / "research.json"
        if research_path.exists():
            research_sources = ResearchRepository().load(research_path).sources

        metadata = SessionService._read_metadata(workspace)
        media_settings = metadata.get("media_settings", {})
        persistence = media_settings.get("visual_persistence", "topic")
        prefer_charts = bool(media_settings.get("prefer_market_charts", True))

        provider = ResilientMediaProvider(news_source_urls=research_sources)
        chart_provider = MarketChartProvider()
        media_dir = workspace / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        media_json = media_dir / "media.json"

        assets = []
        representative_by_topic: dict[str, tuple[object, object]] = {}
        for scene in storyboard.scenes:
            output = media_dir / f"{scene.id:04}.jpg"
            topic_key = scene.section.strip().casefold()

            # Keep one precise visual on screen while narration remains on the
            # same topic. A new topic/section triggers a new visual.
            if persistence == "topic" and topic_key in representative_by_topic:
                source_path, source_asset = representative_by_topic[topic_key]
                shutil.copy2(source_path, output)
                asset = source_asset.model_copy(
                    update={"scene": scene.id, "file": output.name}
                )
                assets.append(asset)
                MediaRepository().save(Media(assets=assets), media_json)
                print(f"Scene {scene.id}: reused topic visual for '{scene.section}'.")
                continue

            asset = None
            if prefer_charts:
                asset = chart_provider.create(scene, output)
                if asset is not None:
                    print(
                        f"Scene {scene.id}: generated a current, source-labelled "
                        f"market chart for '{scene.section}'."
                    )
            if asset is None:
                asset = provider.download(scene, output)

            assets.append(asset)
            if persistence == "topic":
                representative_by_topic[topic_key] = (output, asset)
            MediaRepository().save(Media(assets=assets), media_json)

        MediaRepository().save(Media(assets=assets), media_json)
        print(
            f"Prepared {len(assets)} validated 1920x1080 assets using "
            f"'{persistence}' visual persistence."
        )
