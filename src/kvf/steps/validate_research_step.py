from kvf.models.application import Application
from kvf.repositories.research_repository import ResearchRepository
from kvf.steps.base_step import BaseStep


class ValidateResearchStep(BaseStep):

    def execute(self, application: Application) -> None:

        path = (
            application.project.workspace
            / "research"
            / "research.json"
        )

        repository = ResearchRepository()

        research = repository.load(path)

        print()

        print("Research validated.")

        print(f"Topic: {research.topic}")

        print(f"Sections: {len(research.sections)}")

        print(f"Sources: {len(research.sources)}")