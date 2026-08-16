from kvf.models.application import Application
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.steps.base_step import BaseStep


class ValidateStoryboardStep(BaseStep):
    def execute(self, application: Application) -> None:
        path = application.project.source_dir / "storyboard.json"
        if not path.exists():
            raise FileNotFoundError(path)

        storyboard = StoryboardRepository().load(path)

        print()
        print("Storyboard validated.")
        print(f"Scenes: {storyboard.scene_count}")

        if storyboard.total_estimated_duration_seconds is not None:
            print(
                "GPT duration estimate: "
                f"{storyboard.total_estimated_duration_seconds:.1f}s "
                "(advisory only; actual narration duration controls timing)"
            )
        else:
            print(
                "GPT duration estimate: not provided "
                "(OK; actual narration duration controls timing)"
            )
