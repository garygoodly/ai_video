from __future__ import annotations

from pathlib import Path

from kvf.providers.llm_provider import LLMProvider


class ManualProvider(LLMProvider):
    """
    Manual copy/paste provider.

    Workflow

    1. Generate prompt.md

    2. User copies prompt into ChatGPT.

    3. User pastes JSON into response.json.

    4. Continue workflow.
    """

    RESPONSE_FILE = "response.json"

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)

    @property
    def response_path(self) -> Path:
        return self.workspace / self.RESPONSE_FILE

    def generate(self, prompt: str) -> str:
        print()
        print("=" * 60)
        print("Manual LLM Provider")
        print("=" * 60)
        print()
        print("Prompt has been generated.")
        print()
        print("Copy prompt.md into ChatGPT.")
        print()
        print(
            f"Save the JSON response to:\n\n{self.response_path}"
        )
        print()

        while True:
            input("Press ENTER after response.json has been saved...")

            if self.response_path.exists():
                break

            print("response.json not found.")
            print()

        return self.response_path.read_text(
            encoding="utf-8"
        )