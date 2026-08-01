from kvf.models.application import Application
from kvf.services.workspace_service import WorkspaceService
from kvf.steps.base_step import BaseStep


class CreateWorkspaceStep(BaseStep):

    def execute(self, application: Application) -> None:

        workspace_root = application.settings["workspace"]["root"]

        service = WorkspaceService(workspace_root)

        workspace = service.create(
            application.project.topic
        )

        application.project.workspace = workspace

        print(f"Workspace created: {workspace}")