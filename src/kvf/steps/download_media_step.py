from __future__ import annotations

import shutil
from pathlib import Path

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
    """Prepare precise topic visuals in assets/rendered.

    Policy:
      1. Real market chart when the topic is a recognized instrument/index.
      2. Current research article hero image.
      3. Openverse/Wikimedia image.
      4. Reuse the last defensible real visual.

    The pipeline no longer manufactures decorative "illustrative" cards that
    look like editorial media but carry no real information.
    """

    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        storyboard = StoryboardRepository().load(application.project.source_dir / "storyboard.json")
        research_sources = []
        research_path = application.project.source_dir / "research.json"
        if research_path.exists():
            research_sources = ResearchRepository().load(research_path).sources

        metadata = SessionService._read_metadata(workspace)
        media_settings = metadata.get("media_settings", {})
        persistence = media_settings.get("visual_persistence", "topic")
        prefer_charts = bool(media_settings.get("prefer_market_charts", True))
        strict_precision = bool(media_settings.get("strict_precision", True))

        provider = ResilientMediaProvider(news_source_urls=research_sources)
        chart_provider = MarketChartProvider()
        source_dir = workspace / "assets" / "source"
        rendered_dir = workspace / "assets" / "rendered"
        source_dir.mkdir(parents=True, exist_ok=True)
        rendered_dir.mkdir(parents=True, exist_ok=True)
        media_json = workspace / "assets" / "media.json"

        assets = []
        representative_by_topic: dict[str, tuple[object, object]] = {}
        last_real: tuple[object, object] | None = None

        for scene in storyboard.scenes:
            output = rendered_dir / f"{scene.id:04}.jpg"
            topic_key = scene.section.strip().casefold()

            if persistence == "topic" and topic_key in representative_by_topic:
                source_path, source_asset = representative_by_topic[topic_key]
                shutil.copy2(source_path, output)
                source_original = source_dir / Path(source_path).name
                if source_original.exists():
                    shutil.copy2(source_original, source_dir / output.name)
                asset = source_asset.model_copy(update={"scene": scene.id, "file": output.name})
                assets.append(asset)
                MediaRepository().save(Media(assets=assets), media_json)
                print(f"Scene {scene.id}: reused precise topic visual for '{scene.section}'.")
                continue

            asset = None
            if prefer_charts:
                asset = chart_provider.create(scene, output)
                if asset is not None:
                    print(f"Scene {scene.id}: generated source-labelled market chart for '{scene.section}'.")

            if asset is None:
                try:
                    asset = provider.download(scene, output)
                except Exception as exc:
                    if last_real is not None:
                        previous_path, previous_asset = last_real
                        shutil.copy2(previous_path, output)
                        asset = previous_asset.model_copy(
                            update={
                                "scene": scene.id,
                                "file": output.name,
                                "query": f"Reused previous verified visual; no precise new asset for: {scene.visual.query}",
                            }
                        )
                        print(
                            f"Scene {scene.id}: no precise new visual ({exc}); "
                            "kept the previous verified visual instead."
                        )
                    elif strict_precision:
                        raise RuntimeError(
                            f"No defensible visual could be found for the first topic '{scene.section}'. "
                            "The pipeline stopped instead of inserting a synthetic placeholder. "
                            f"Details: {exc}"
                        ) from exc
                    else:
                        raise

            # Charts are generated locally, so preserve the exact chart in the
            # source review folder as well. Downloaded images are saved there by
            # ResilientMediaProvider before cropping.
            source_copy = source_dir / output.name
            if not source_copy.exists() and output.exists():
                shutil.copy2(output, source_copy)

            assets.append(asset)
            last_real = (output, asset)
            if persistence == "topic":
                representative_by_topic[topic_key] = (output, asset)
            MediaRepository().save(Media(assets=assets), media_json)

        MediaRepository().save(Media(assets=assets), media_json)
        print(
            f"Prepared {len(assets)} verified 1920x1080 assets in assets/rendered "
            f"using '{persistence}' visual persistence."
        )
