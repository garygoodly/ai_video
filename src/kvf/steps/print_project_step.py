from kvf.models.application import Application
from kvf.steps.base_step import BaseStep


class PrintProjectStep(BaseStep):

    def execute(self, application: Application) -> None:

        project = application.project

        print(f"Topic      : {project.topic.name}")
        print(f"Category   : {project.topic.category}")
        print(f"Blueprint  : {project.blueprint.title}")
        print(f"Workspace  : {project.workspace}")