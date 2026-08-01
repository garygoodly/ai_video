from __future__ import annotations

from pathlib import Path

from kvf.models.storyboard import Storyboard
from kvf.repositories.script_repository import ScriptRepository
from kvf.repositories.storyboard_repository import StoryboardRepository
from kvf.services.storyboard_service import StoryboardService
from kvf.providers.llm_provider import LLMProvider


class StoryboardStep:
    """
    Generate storyboard.json from script.json.

    Responsibilities
    ----------------
    1. Load Script
    2. Build prompt
    3. Save prompt.md
    4. Call LLM
    5. Validate response
    6. Save storyboard.json
    """

    PROMPT_FILE = "prompt.md"

    def __init__(
        self,
        workspace: Path,
        llm_provider: LLMProvider,
        prompt_template: Path,
    ):
        self.workspace = Path(workspace)

        self.script_repository = ScriptRepository(self.workspace)
        self.storyboard_repository = StoryboardRepository(self.workspace)

        self.service = StoryboardService(prompt_template)

        self.llm = llm_provider

    @property
    def storyboard_directory(self) -> Path:
        return self.workspace / "storyboard"

    @property
    def prompt_path(self) -> Path:
        return self.storyboard_directory / self.PROMPT_FILE

    def execute(self) -> Storyboard:
        """
        Execute the storyboard generation pipeline.
        """

        # Load validated script
        script = self.script_repository.load()

        # Build prompt
        prompt = self.service.build_prompt(script)

        # Save prompt for manual/API usage
        self.storyboard_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.prompt_path.write_text(
            prompt,
            encoding="utf-8",
        )

        # Generate response
        response = self.llm.generate(prompt)

        # Validate response
        storyboard = self.service.parse_response(response)

        # Save storyboard
        self.storyboard_repository.save(storyboard)

        return storyboard