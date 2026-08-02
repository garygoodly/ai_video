from kvf.core.workflow import Workflow
from kvf.models.project import Project
from kvf.repositories.topic_repository import TopicRepository
from kvf.services.blueprint_service import BlueprintService
from kvf.steps.create_workspace_step import CreateWorkspaceStep
from kvf.steps.print_project_step import PrintProjectStep
from kvf.utils.yaml_loader import load_yaml
from kvf.models.application import Application

from kvf.steps.generate_research_prompt_step import GenerateResearchPromptStep
from kvf.steps.wait_for_research_step import WaitForResearchStep
from kvf.steps.validate_research_step import ValidateResearchStep

from kvf.steps.generate_script_prompt_step import GenerateScriptPromptStep
from kvf.steps.wait_for_script_step import WaitForScriptStep
from kvf.steps.validate_script_step import ValidateScriptStep

from kvf.steps.generate_storyboard_prompt_step import GenerateStoryboardPromptStep
from kvf.steps.wait_for_storyboard_step import WaitForStoryboardStep
from kvf.steps.validate_storyboard_step import ValidateStoryboardStep

from kvf.steps.download_media_step import DownloadMediaStep

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

workflow.add_step(GenerateResearchPromptStep())
workflow.add_step(WaitForResearchStep())
workflow.add_step(ValidateResearchStep())

workflow.add_step(GenerateScriptPromptStep())
workflow.add_step(WaitForScriptStep())
workflow.add_step(ValidateScriptStep())

workflow.add_step(GenerateStoryboardPromptStep())
workflow.add_step(WaitForStoryboardStep())
workflow.add_step(ValidateStoryboardStep())

workflow.add_step(DownloadMediaStep())

workflow.run()