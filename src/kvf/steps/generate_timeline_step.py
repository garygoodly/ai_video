from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict

from kvf.models.application import Application
from kvf.models.timeline import Timeline, TimelineScene
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.repositories.timeline_repository import TimelineRepository
from kvf.steps.base_step import BaseStep
from kvf.services.native_timing_alignment_service import NativeTimingAlignmentService


class GenerateTimelineStep(BaseStep):
    """Build a timeline using measured section card and narration boundaries."""

    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        output = workspace / "timeline" / "timeline.json"
        storyboard = StoryboardRepository().load(
            application.project.source_dir / "storyboard.json"
        )
        audio = workspace / "voice" / "narration.mp3"
        total_audio_duration = self._probe_duration(audio)
        timing_path = workspace / "voice" / "cue_timing.json"

        timing_payload = {}
        if timing_path.exists():
            try:
                timing_payload = json.loads(timing_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                timing_payload = {}

        section_timings = timing_payload.get("sections", []) if isinstance(timing_payload, dict) else []
        if section_timings:
            scenes = self._section_aware_scenes(storyboard, section_timings)
        else:
            scenes = self._legacy_scenes(storyboard, total_audio_duration)

        output.parent.mkdir(parents=True, exist_ok=True)
        TimelineRepository().save(
            Timeline(total_duration_seconds=total_audio_duration, scenes=scenes),
            output,
        )
        print(
            f"Timeline generated with {len(scenes)} scenes from the actual "
            f"{total_audio_duration:.2f}s narration duration: {output}"
        )

    def _section_aware_scenes(self, storyboard, section_timings: list[dict]) -> list[TimelineScene]:
        grouped = defaultdict(list)
        section_order = []
        for scene in storyboard.scenes:
            if scene.section not in grouped:
                section_order.append(scene.section)
            grouped[scene.section].append(scene)

        scenes: list[TimelineScene] = []
        timeline_id = 1
        for section_index, section_name in enumerate(section_order, start=1):
            source_scenes = grouped[section_name]
            timing = self._find_section_timing(section_name, section_index, section_timings)
            if timing is None:
                continue

            card_start = float(timing["card_start"])
            card_end = float(timing["card_end"])
            speech_start = float(timing["speech_start"])
            speech_end = float(timing["speech_end"])

            scenes.append(
                TimelineScene(
                    id=timeline_id,
                    image=f"section_{section_index:02d}.jpg",
                    narration="",
                    subtitle_start=card_start,
                    subtitle_end=card_end,
                    duration_seconds=max(card_end - card_start, 0.1),
                    camera_motion="static",
                    transition="fade",
                )
            )
            timeline_id += 1

            word_timings = timing.get("word_timings", [])
            if word_timings:
                aligned = NativeTimingAlignmentService().align_texts(
                    [scene.narration for scene in source_scenes],
                    word_timings,
                    speech_start,
                    speech_end,
                )
            else:
                weights = [self._narration_weight(scene.narration) for scene in source_scenes]
                total_weight = sum(weights) or float(len(weights)) or 1.0
                aligned = []
                cursor = speech_start
                for index, (scene, weight) in enumerate(zip(source_scenes, weights)):
                    end = (
                        speech_end
                        if index == len(source_scenes) - 1
                        else cursor + (speech_end - speech_start) * weight / total_weight
                    )
                    aligned.append({"start": cursor, "end": end})
                    cursor = end

            for scene, span in zip(source_scenes, aligned):
                start = float(span["start"])
                end = float(span["end"])
                scenes.append(
                    TimelineScene(
                        id=timeline_id,
                        image=f"{scene.id:04d}.jpg",
                        narration=scene.narration,
                        subtitle_start=start,
                        subtitle_end=end,
                        duration_seconds=max(end - start, 0.1),
                        camera_motion=scene.camera.motion,
                        transition=scene.transition.type,
                    )
                )
                timeline_id += 1
        return scenes

    @staticmethod
    def _find_section_timing(section_name: str, section_index: int, timings: list[dict]):
        for timing in timings:
            if str(timing.get("title", "")).strip() == section_name.strip():
                return timing
        if 0 < section_index <= len(timings):
            return timings[section_index - 1]
        return None

    def _legacy_scenes(self, storyboard, total_audio_duration: float) -> list[TimelineScene]:
        weights = [self._narration_weight(scene.narration) for scene in storyboard.scenes]
        weight_total = sum(weights) or float(len(weights)) or 1.0
        scenes = []
        cursor = 0.0
        for timeline_id, (scene, weight) in enumerate(zip(storyboard.scenes, weights), start=1):
            end = (
                total_audio_duration
                if timeline_id == len(storyboard.scenes)
                else cursor + total_audio_duration * weight / weight_total
            )
            scenes.append(
                TimelineScene(
                    id=timeline_id,
                    image=f"{scene.id:04d}.jpg",
                    narration=scene.narration,
                    subtitle_start=cursor,
                    subtitle_end=end,
                    duration_seconds=max(end - cursor, 0.1),
                    camera_motion=scene.camera.motion,
                    transition=scene.transition.type,
                )
            )
            cursor = end
        return scenes

    @staticmethod
    def _narration_weight(text: str) -> float:
        cjk_count = len(re.findall(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", text))
        latin_tokens = len(re.findall(r"[A-Za-z0-9]+(?:[.,:/%-][A-Za-z0-9]+)*", text))
        return max(float(cjk_count + latin_tokens), 1.0)

    @staticmethod
    def _probe_duration(audio) -> float:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(audio),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        duration = float(result.stdout.strip())
        if duration <= 0:
            raise ValueError("Narration audio duration must be positive.")
        return duration
