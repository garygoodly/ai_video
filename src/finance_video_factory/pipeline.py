from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from finance_video_factory.collectors.markets import MarketCollector
from finance_video_factory.collectors.rss import RSSCollector
from finance_video_factory.manual import (
    ManualActionRequired,
    load_and_validate_json,
    normalize_response_file,
)
from finance_video_factory.models import (
    Article,
    MarketSnapshot,
    PipelineContext,
    RankedEvent,
    Scene,
)
from finance_video_factory.providers.youtube import YouTubeUploader
from finance_video_factory.services.charts import ChartService
from finance_video_factory.services.media import MediaService
from finance_video_factory.services.ranking import EventRanker
from finance_video_factory.services.render import RenderService
from finance_video_factory.services.subtitles import SubtitleService
from finance_video_factory.services.thumbnail import ThumbnailService
from finance_video_factory.services.timeline import TimelineService
from finance_video_factory.services.voice import VoiceService
from finance_video_factory.utils import read_json, write_json


class FinanceVideoPipeline:
    def __init__(self, settings: dict, root: Path, project_dir: Path):
        self.s = settings
        self.root = root
        self.project_dir = project_dir

    def run(self, upload: bool = False, workspace: Path | None = None) -> Path:
        ws = workspace.resolve() if workspace else self._new_workspace()
        self._create_directories(ws)
        ctx = PipelineContext(run_id=ws.name, workspace=ws, settings=self.s)

        try:
            self._load_or_collect(ctx)
            self._load_or_rank(ctx)
            self._load_or_request_research(ctx)
            self._load_or_request_script(ctx)
            self._load_or_request_storyboard(ctx)
            self._load_or_create_media(ctx)
            self._load_or_create_voice(ctx)
            self._load_or_create_subtitles(ctx)
            self._load_or_create_timeline(ctx)
            video = self._load_or_render(ctx)
            self._load_or_create_publish_assets(ctx)
            if upload or self.s["youtube"].get("enabled", False):
                self._upload(ctx, video)
        except ManualActionRequired:
            raise

        print(f"\nCompleted: {video}")
        return video

    def _new_workspace(self) -> Path:
        run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return (self.root / run_id).resolve()

    @staticmethod
    def _create_directories(ws: Path) -> None:
        for name in (
            "input",
            "manual",
            "research",
            "script",
            "storyboard",
            "media",
            "charts",
            "voice",
            "subtitle",
            "timeline",
            "video",
            "publish",
        ):
            (ws / name).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _step(name: str) -> None:
        print(f">>> {name}")

    def _load_or_collect(self, ctx: PipelineContext) -> None:
        articles_path = ctx.workspace / "input/articles.json"
        markets_path = ctx.workspace / "input/markets.json"
        if articles_path.exists() and markets_path.exists():
            ctx.articles = [Article.model_validate(x) for x in read_json(articles_path)]
            ctx.markets = [MarketSnapshot.model_validate(x) for x in read_json(markets_path)]
            return

        self._step("Collect news and market data")
        cfg = self.s["content"]
        ctx.articles = RSSCollector().collect(
            self.s["news"]["rss_feeds"],
            cfg["lookback_hours"],
            cfg["max_articles"],
        )
        ctx.markets = MarketCollector().collect(self.s["markets"]["symbols"])
        write_json(articles_path, [x.model_dump() for x in ctx.articles])
        write_json(markets_path, [x.model_dump() for x in ctx.markets])

    def _load_or_rank(self, ctx: PipelineContext) -> None:
        path = ctx.workspace / "research/ranked_events.json"
        if path.exists():
            ctx.ranked_events = [RankedEvent.model_validate(x) for x in read_json(path)]
            return

        self._step("Rank events")
        ctx.ranked_events = EventRanker().rank(
            ctx.articles, self.s["content"]["top_events"]
        )
        write_json(path, [x.model_dump() for x in ctx.ranked_events])

    def _load_or_request_research(self, ctx: PipelineContext) -> None:
        final_path = ctx.workspace / "research/research.json"
        response_path = ctx.workspace / "manual/research_response.json"
        prompt_path = ctx.workspace / "manual/research_prompt.txt"
        if final_path.exists():
            ctx.research = read_json(final_path)
            return

        if not response_path.exists():
            evidence = {
                "report_date": datetime.now().astimezone().isoformat(),
                "markets": [x.model_dump() for x in ctx.markets],
                "events": [
                    {
                        "ranking": event.model_dump(),
                        "articles": [
                            ctx.articles[i].model_dump()
                            for i in event.article_indexes
                            if i < len(ctx.articles)
                        ],
                    }
                    for event in ctx.ranked_events
                ],
            }
            template = self._prompt("research.md")
            prompt = (
                template
                + "\n\n# Evidence collected by the pipeline\n"
                + json.dumps(evidence, ensure_ascii=False, indent=2, default=str)
                + "\n\nReturn ONLY valid JSON. Do not wrap it in markdown fences.\n"
            )
            prompt_path.write_text(prompt, encoding="utf-8")
            raise ManualActionRequired("research", prompt_path, response_path, ctx.workspace)

        self._step("Validate manual research response")
        normalize_response_file(response_path)
        ctx.research = load_and_validate_json(
            response_path,
            {"executive_summary", "market_snapshot", "events", "scenarios", "watch_list", "sources"},
        )
        write_json(final_path, ctx.research)

    def _load_or_request_script(self, ctx: PipelineContext) -> None:
        final_path = ctx.workspace / "script/script.json"
        response_path = ctx.workspace / "manual/script_response.json"
        prompt_path = ctx.workspace / "manual/script_prompt.txt"
        if final_path.exists():
            ctx.script = read_json(final_path)
            return

        if not response_path.exists():
            prompt = (
                self._prompt("script.md")
                + f"\n\nTarget length: {self.s['content']['target_minutes']} minutes.\n"
                + f"Channel name: {self.s['content']['channel_name']}\n"
                + f"Disclaimer: {self.s['content']['disclaimer']}\n\n"
                + "# Validated research\n"
                + json.dumps(ctx.research, ensure_ascii=False, indent=2)
                + "\n\nReturn ONLY valid JSON. Do not wrap it in markdown fences.\n"
            )
            prompt_path.write_text(prompt, encoding="utf-8")
            raise ManualActionRequired("script", prompt_path, response_path, ctx.workspace)

        self._step("Validate manual script response")
        normalize_response_file(response_path)
        ctx.script = load_and_validate_json(
            response_path,
            {"title", "hook", "sections", "closing", "full_narration"},
        )
        if not isinstance(ctx.script["full_narration"], str) or not ctx.script["full_narration"].strip():
            raise ValueError("script_response.json: full_narration must be a non-empty string")
        write_json(final_path, ctx.script)
        (ctx.workspace / "script/narration.txt").write_text(
            ctx.script["full_narration"], encoding="utf-8"
        )

    def _load_or_request_storyboard(self, ctx: PipelineContext) -> None:
        final_path = ctx.workspace / "storyboard/storyboard.json"
        response_path = ctx.workspace / "manual/storyboard_response.json"
        prompt_path = ctx.workspace / "manual/storyboard_prompt.txt"
        if final_path.exists():
            ctx.scenes = [Scene.model_validate(x) for x in read_json(final_path)]
            return

        if not response_path.exists():
            prompt = (
                self._prompt("storyboard.md")
                + "\n\n# Final script\n"
                + json.dumps(ctx.script, ensure_ascii=False, indent=2)
                + "\n\nReturn ONLY valid JSON. Do not wrap it in markdown fences.\n"
            )
            prompt_path.write_text(prompt, encoding="utf-8")
            raise ManualActionRequired("storyboard", prompt_path, response_path, ctx.workspace)

        self._step("Validate manual storyboard response")
        normalize_response_file(response_path)
        data = load_and_validate_json(response_path, {"scenes"})
        if not isinstance(data["scenes"], list) or not data["scenes"]:
            raise ValueError("storyboard_response.json: scenes must be a non-empty array")
        ctx.scenes = []
        for index, scene in enumerate(data["scenes"], 1):
            if not isinstance(scene, dict):
                raise ValueError(f"storyboard scene {index} must be a JSON object")
            scene = {**scene, "index": index}
            ctx.scenes.append(Scene.model_validate(scene))
        write_json(final_path, [x.model_dump() for x in ctx.scenes])

    def _load_or_create_media(self, ctx: PipelineContext) -> None:
        resolved = ctx.workspace / "storyboard/storyboard_resolved.json"
        if resolved.exists() and all(Path(x.get("image", "")).exists() for x in read_json(resolved)):
            ctx.scenes = [Scene.model_validate(x) for x in read_json(resolved)]
            return

        self._step("Acquire media and generate charts")
        media = MediaService(self.s["video"]["width"], self.s["video"]["height"])
        charts = ChartService()
        for scene in ctx.scenes:
            if scene.visual_type == "chart" and scene.chart_symbol:
                output = ctx.workspace / "charts" / f"{scene.index:04}.png"
                charts.create(
                    scene.chart_symbol,
                    scene.on_screen_text or scene.chart_symbol,
                    output,
                )
            else:
                output = ctx.workspace / "media" / f"{scene.index:04}.jpg"
                media.acquire(
                    scene.search_query,
                    scene.on_screen_text or scene.narration[:80],
                    output,
                )
            scene.image = str(output.resolve())
        write_json(resolved, [x.model_dump() for x in ctx.scenes])

    def _load_or_create_voice(self, ctx: PipelineContext) -> None:
        output = ctx.workspace / "voice/narration.mp3"
        if output.exists() and output.stat().st_size > 0:
            return
        self._step("Generate voice")
        voice = self.s["voice"]
        VoiceService().synthesize(
            ctx.script["full_narration"], output, voice["voice"], voice["rate"]
        )

    def _load_or_create_subtitles(self, ctx: PipelineContext) -> None:
        output = ctx.workspace / "subtitle/subtitle.srt"
        if output.exists() and output.stat().st_size > 0:
            return
        self._step("Generate subtitles")
        SubtitleService().transcribe(
            ctx.workspace / "voice/narration.mp3",
            output,
            self.s["subtitle"]["whisper_model"],
        )

    def _load_or_create_timeline(self, ctx: PipelineContext) -> None:
        output = ctx.workspace / "timeline/timeline.json"
        if output.exists():
            ctx.scenes = [Scene.model_validate(x) for x in read_json(output)]
            return
        self._step("Generate timeline")
        ctx.scenes = TimelineService().assign(
            ctx.scenes, ctx.workspace / "subtitle/subtitle.srt"
        )
        write_json(output, [x.model_dump() for x in ctx.scenes])

    def _load_or_render(self, ctx: PipelineContext) -> Path:
        output = ctx.workspace / "video/video.mp4"
        if output.exists() and output.stat().st_size > 0:
            return output
        self._step("Render 1920x1080 video")
        video = self.s["video"]
        return RenderService().render(
            ctx.scenes,
            ctx.workspace / "voice/narration.mp3",
            ctx.workspace / "subtitle/subtitle.srt",
            output,
            video["width"],
            video["height"],
            video["fps"],
            video["crf"],
            video["font_size"],
        )

    def _load_or_create_publish_assets(self, ctx: PipelineContext) -> None:
        metadata_path = ctx.workspace / "publish/youtube_metadata.json"
        thumbnail_path = ctx.workspace / "publish/thumbnail.jpg"
        if metadata_path.exists() and thumbnail_path.exists():
            return
        self._step("Create thumbnail and YouTube metadata")
        title = ctx.script.get("title", "Daily Finance Brief")
        ThumbnailService().create(title, thumbnail_path)
        description = (
            ctx.script.get("closing", "")
            + "\n\n"
            + self.s["content"]["disclaimer"]
            + "\n\nSources:\n"
            + "\n".join(str(x) for x in ctx.research.get("sources", []))
        )
        write_json(
            metadata_path,
            {
                "title": title,
                "description": description,
                "tags": ["finance", "markets", "stock market", "macro", "financial news"],
            },
        )

    def _upload(self, ctx: PipelineContext, video: Path) -> None:
        self._step("Upload to YouTube")
        metadata = read_json(ctx.workspace / "publish/youtube_metadata.json")
        video_id = YouTubeUploader().upload(
            video,
            ctx.workspace / "publish/thumbnail.jpg",
            metadata,
            self.s["youtube"],
        )
        print(f"Uploaded YouTube video ID: {video_id}")

    def _prompt(self, name: str) -> str:
        return (self.project_dir / "prompts" / name).read_text(encoding="utf-8")
