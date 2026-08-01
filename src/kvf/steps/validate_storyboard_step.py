from kvf.models.application import Application
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.steps.base_step import BaseStep


class ValidateStoryboardStep(BaseStep):

    def execute(
        self,
        application: Application,
    ) -> None:

        path = (
            application.project.workspace
            / "storyboard"
            / "storyboard.json"
        )

        if not path.exists():
            raise FileNotFoundError(path)

        storyboard = StoryboardRepository().load(
            path
        )

        print()

        print("Storyboard validated.")

        print(
            f"Scenes: {storyboard.scene_count}"
        )

        print(
            "Estimated Duration: "
            f"{storyboard.total_estimated_duration_seconds:.1f}s"
        )