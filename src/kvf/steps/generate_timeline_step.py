import re

from kvf.models.application import Application
from kvf.models.timeline import Timeline
from kvf.models.timeline import TimelineScene
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.repositories.timeline_repository import TimelineRepository
from kvf.steps.base_step import BaseStep


class GenerateTimelineStep(BaseStep):

    def execute(
        self,
        application: Application,
    ):

        workspace = application.project.workspace

        output = (
            workspace
            / "timeline"
            / "timeline.json"
        )

        if output.exists():

            print(
                "Timeline already exists. [SKIP]"
            )

            return

        storyboard = StoryboardRepository().load(
            workspace
            / "storyboard"
            / "storyboard.json"
        )

        subtitle = (
            workspace
            / "subtitle"
            / "subtitle.srt"
        )

        timings = self._read_srt(
            subtitle
        )

        scenes = []

        total = 0.0

        for scene, timing in zip(
            storyboard.scenes,
            timings,
        ):

            duration = (
                timing["end"]
                - timing["start"]
            )

            total += duration

            scenes.append(

                TimelineScene(

                    id=scene.id,

                    image=f"{scene.id:04d}.jpg",

                    narration=scene.narration,

                    subtitle_start=timing["start"],

                    subtitle_end=timing["end"],

                    duration_seconds=duration,

                    camera_motion=scene.camera.motion,

                    transition=scene.transition.type,
                )

            )

        TimelineRepository().save(

            Timeline(

                total_duration_seconds=total,

                scenes=scenes,
            ),

            output,
        )

        print(
            f"Timeline generated: {output}"
        )

    def _read_srt(
        self,
        path,
    ):

        text = path.read_text(
            encoding="utf-8"
        )

        pattern = re.compile(

            r"(\d+)\n"
            r"(\d+:\d+:\d+,\d+)"
            r" --> "
            r"(\d+:\d+:\d+,\d+)",

            re.MULTILINE,
        )

        segments = []

        for match in pattern.finditer(
            text
        ):

            start = self._seconds(
                match.group(2)
            )

            end = self._seconds(
                match.group(3)
            )

            segments.append(

                {
                    "start": start,
                    "end": end,
                }

            )

        return segments

    def _seconds(
        self,
        timestamp,
    ):

        h, m, rest = timestamp.split(":")

        s, ms = rest.split(",")

        return (

            int(h) * 3600

            + int(m) * 60

            + int(s)

            + int(ms) / 1000

        )