import subprocess

from kvf.models.application import Application
from kvf.models.timeline import Timeline, TimelineScene
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.repositories.timeline_repository import TimelineRepository
from kvf.steps.base_step import BaseStep


class GenerateTimelineStep(BaseStep):
    """Build one timeline entry for every storyboard scene.

    Scene timing is derived from the narration audio duration and distributed
    according to each scene's estimated duration. This avoids losing scenes
    when Whisper produces fewer subtitle segments than storyboard scenes.
    """

    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        output = workspace / "timeline" / "timeline.json"

        storyboard = StoryboardRepository().load(
            workspace / "storyboard" / "storyboard.json"
        )
        audio = workspace / "voice" / "narration.mp3"
        total_audio_duration = self._probe_duration(audio)

        estimates = [
            max(float(scene.estimated_duration_seconds), 0.1)
            for scene in storyboard.scenes
        ]
        estimate_total = sum(estimates)
        if estimate_total <= 0:
            raise ValueError("Storyboard has no usable scene durations.")

        scenes = []
        cursor = 0.0
        for index, (scene, estimate) in enumerate(
            zip(storyboard.scenes, estimates)
        ):
            if index == len(storyboard.scenes) - 1:
                duration = max(total_audio_duration - cursor, 0.1)
            else:
                duration = total_audio_duration * estimate / estimate_total

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
            Timeline(
                total_duration_seconds=total_audio_duration,
                scenes=scenes,
            ),
            output,
        )
        print(
            f"Timeline generated with {len(scenes)} scenes: {output}"
        )

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
