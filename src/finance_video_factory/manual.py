from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ManualActionRequired(RuntimeError):
    """Raised when the user must answer a generated ChatGPT prompt."""

    def __init__(self, stage: str, prompt_path: Path, response_path: Path, workspace: Path):
        self.stage = stage
        self.prompt_path = prompt_path
        self.response_path = response_path
        self.workspace = workspace
        super().__init__(f"Manual ChatGPT response required for {stage}")


def load_and_validate_json(path: Path, required_keys: set[str]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ValueError(f"Response file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")

    missing = sorted(required_keys - set(data))
    if missing:
        raise ValueError(f"Missing required key(s) in {path}: {', '.join(missing)}")
    return data


def strip_markdown_fence(text: str) -> str:
    """Convert a copied ```json ... ``` response into plain JSON when possible."""
    value = text.strip()
    if not value.startswith("```"):
        return value
    lines = value.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def normalize_response_file(path: Path) -> None:
    if not path.exists():
        return
    original = path.read_text(encoding="utf-8-sig")
    cleaned = strip_markdown_fence(original)
    if cleaned != original:
        path.write_text(cleaned + "\n", encoding="utf-8")
