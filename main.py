from kvf.core.workflow import Workflow
from kvf.models.project import Project
from kvf.repositories.topic_repository import TopicRepository
from kvf.services.blueprint_service import BlueprintService
from kvf.steps.create_workspace_step import CreateWorkspaceStep
from kvf.steps.print_project_step import PrintProjectStep
from kvf.utils.yaml_loader import load_yaml
from kvf.models.application import Application

settings = load_yaml("config/settings.yaml")

topic_repository = TopicRepository(
    "plugins/countries/countries.csv"
)

blueprint_service = BlueprintService(
    "config/blueprints"
)

topic = topic_repository.get_first()

blueprint = blueprint_service.load("country")

project = Project(
    topic=topic,
    blueprint=blueprint,
)

application = Application(
    settings=settings,
    project=project,
)

workflow = Workflow(application)

workflow.add_step(CreateWorkspaceStep())
workflow.add_step(PrintProjectStep())

workflow.run()