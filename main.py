from kvf.repositories.topic_repository import TopicRepository
from kvf.services.blueprint_service import BlueprintService
from kvf.services.workspace_service import WorkspaceService
from kvf.utils.yaml_loader import load_yaml
from kvf.models.project import Project

settings = load_yaml("config/settings.yaml")

blueprint_service = BlueprintService(
    "config/blueprints"
)

topic_repository = TopicRepository(
    "plugins/countries/countries.csv"
)

workspace_service = WorkspaceService(
    settings["workspace"]["root"]
)


topic = topic_repository.get_first()

blueprint = blueprint_service.load("country")

workspace = workspace_service.create(topic)

project = Project(
    topic=topic,
    blueprint=blueprint,
    workspace=workspace,
)


print("=" * 60)
print(settings["project"]["name"])
print("=" * 60)
print(f"Topic      : {project.topic.name}")
print(f"Blueprint  : {project.blueprint.title}")
print(f"Workspace  : {project.workspace}")