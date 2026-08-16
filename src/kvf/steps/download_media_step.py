from __future__ import annotations

import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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
            topic_key = self._topic_key(scene)

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
        self._generate_section_cards(storyboard, rendered_dir)
        print(
            f"Prepared {len(assets)} verified 1920x1080 assets in assets/rendered "
            f"using '{persistence}' visual persistence."
        )


    @staticmethod
    def _topic_key(scene) -> str:
        """Use the actual market/entity topic, not the broad section title.

        Previously every scene in e.g. 美股盤勢 shared one key, causing an
        S&P visual to be reused for Nasdaq, SOX and unrelated sentences.
        """
        text = f"{scene.narration} {scene.visual.query}".casefold()
        topics = [
            ("sp500", r"s&p\s*500|sp500|標普"),
            ("nasdaq", r"nasdaq|那斯達克|納斯達克"),
            ("dow", r"dow jones|dow\b|道瓊"),
            ("sox", r"philadelphia semiconductor|\bsox\b|費城半導體"),
            ("taiex", r"taiex|加權指數|台股"),
            ("tsmc", r"tsmc|台積電"),
            ("nikkei", r"nikkei|日經"),
            ("topix", r"topix"),
            ("usdjpy", r"usd/jpy|usd jpy|美元.*日圓|日圓.*美元"),
            ("usdtwd", r"usd/twd|usd twd|新台幣|台幣"),
            ("dxy", r"\bdxy\b|dollar index|美元指數"),
            ("treasury10y", r"10年期.*美債|10-year treasury|10 year treasury"),
            ("oil", r"brent|wti|crude oil|原油|油價|荷莫茲"),
            ("gold", r"gold|黃金|金價"),
            ("bitcoin", r"bitcoin|btc|比特幣"),
        ]
        for key, pattern in topics:
            if re.search(pattern, text, re.I):
                return key
        # For non-market stories, a normalized visual query is more precise
        # than the whole section but still allows nearby scenes to reuse media.
        words = re.findall(r"[a-z0-9]+|[\u3400-\u9fff]+", scene.visual.query.casefold())
        return "query:" + " ".join(words[:5])

    @classmethod
    def _generate_section_cards(cls, storyboard, rendered_dir: Path) -> None:
        seen = []
        for scene in storyboard.scenes:
            if scene.section not in seen:
                seen.append(scene.section)
        for index, section in enumerate(seen, start=1):
            path = rendered_dir / f"section_{index:02d}.jpg"
            cls._draw_section_card(path, section)

    @staticmethod
    def _draw_section_card(path: Path, section: str) -> None:
        image = Image.new("RGB", (1920, 1080), (18, 31, 48))
        draw = ImageDraw.Draw(image)
        title = section.split("｜", 1)[0].strip()
        detail = section.split("｜", 1)[1].strip() if "｜" in section else ""
        font_candidates = ["msjhbd.ttc", "msjh.ttc", "Microsoft JhengHei Bold.ttf", "arialbd.ttf"]
        def font(size):
            for candidate in font_candidates:
                try:
                    return ImageFont.truetype(candidate, size)
                except OSError:
                    continue
            return ImageFont.load_default()
        title_font = font(92)
        detail_font = font(40)
        label_font = font(28)
        draw.text((160, 370), title, font=title_font, fill="white")
        if detail:
            draw.text((165, 505), detail, font=detail_font, fill=(205, 215, 225))
        draw.rectangle((160, 320, 360, 330), fill=(220, 220, 220))
        draw.text((165, 650), "MARKET BRIEFING", font=label_font, fill=(155, 170, 185))
        image.save(path, "JPEG", quality=94)
