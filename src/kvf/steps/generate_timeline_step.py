import re
import subprocess

from kvf.models.application import Application
from kvf.models.timeline import Timeline, TimelineScene
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.repositories.timeline_repository import TimelineRepository
from kvf.steps.base_step import BaseStep


class GenerateTimelineStep(BaseStep):
    """Build the scene timeline from the actual narration duration.

    GPT-provided duration estimates are intentionally ignored. They are only
    editorial hints and are often inconsistent. The rendered narration is the
    authoritative clock. Scene shares are estimated from narration content so
    old and new storyboard JSON remain compatible even when duration fields are
    missing or malformed.
    """

    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        output = workspace / "timeline" / "timeline.json"

        storyboard = StoryboardRepository().load(
            application.project.source_dir / "storyboard.json"
        )
        audio = workspace / "voice" / "narration.mp3"
        total_audio_duration = self._probe_duration(audio)

        weights = [self._narration_weight(scene.narration) for scene in storyboard.scenes]
        weight_total = sum(weights)
        if weight_total <= 0:
            weights = [1.0 for _ in storyboard.scenes]
            weight_total = float(len(weights))
        if not weights:
            raise ValueError("Storyboard contains no scenes.")

        scenes = []
        cursor = 0.0
        for index, (scene, weight) in enumerate(zip(storyboard.scenes, weights)):
            if index == len(storyboard.scenes) - 1:
                duration = max(total_audio_duration - cursor, 0.1)
            else:
                duration = total_audio_duration * weight / weight_total

            start = cursor
            end = min(cursor + duration, total_audio_duration)
            cursor = end

            scenes.append(
                TimelineScene(
                    id=scene.id,
                    image=f"{scene.id:04d}.jpg",
                    narration=scene.narration,
                    subtitle_start=start,
                    subtitle_end=end,
                    duration_seconds=max(end - start, 0.1),
                    camera_motion=scene.camera.motion,
                    transition=scene.transition.type,
                )
            )

        output.parent.mkdir(parents=True, exist_ok=True)
        TimelineRepository().save(
            Timeline(total_duration_seconds=total_audio_duration, scenes=scenes),
            output,
        )
        print(
            f"Timeline generated with {len(scenes)} scenes from the actual "
            f"{total_audio_duration:.2f}s narration duration: {output}"
        )

    @staticmethod
    def _narration_weight(text: str) -> float:
        """Estimate relative speaking time without using GPT duration guesses.

        CJK characters are counted individually. Latin/number runs are counted
        as words. This is only used to distribute the *real* audio duration
        across storyboard scenes.
        """

        cjk_count = len(re.findall(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", text))
        latin_tokens = len(re.findall(r"[A-Za-z0-9]+(?:[.,:/%-][A-Za-z0-9]+)*", text))
        return max(float(cjk_count + latin_tokens), 1.0)

    @staticmethod
    def _probe_duration(audio) -> float:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio),
        ]
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        duration = float(result.stdout.strip())
        if duration <= 0:
            raise ValueError("Narration audio duration must be positive.")
        return duration
