from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from kvf.models.script import Script
from kvf.models.storyboard import Storyboard


class StoryboardService:
    """
    Converts a Script into a validated Storyboard.

    Responsibilities
    ----------------
    - Load prompt template
    - Inject script JSON
    - Build LLM prompt
    - Parse returned JSON
    - Validate output
    """

    def __init__(self, prompt_path: Path):
        self.prompt_path = Path(prompt_path)

    @property
    def prompt_template(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8")

    def build_prompt(self, script: Script) -> str:
        """
        Build the final prompt sent to the LLM.
        """

        script_json = json.dumps(
            script.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        )

        return (
            self.prompt_template
            .replace("{{SCRIPT_JSON}}", script_json)
        )

    def parse_response(self, response: str) -> Storyboard:
        """
        Parse the LLM response into a Storyboard model.
        """

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError("LLM did not return valid JSON.") from e

        try:
            return Storyboard.model_validate(data)
        except ValidationError as e:
            raise ValueError(
                "Storyboard JSON failed validation."
            ) from e

    def create(
        self,
        script: Script,
        llm_response: str,
    ) -> Storyboard:
        """
        Complete pipeline after an LLM response has been received.
        """

        # Prompt generation is kept here so callers can save it.
        self.build_prompt(script)

        return self.parse_response(llm_response)