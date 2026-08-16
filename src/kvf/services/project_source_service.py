from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class ProjectSourceService:
    """Manage Git-trackable source artifacts separately from build outputs."""

    SOURCE_FILES = {
        "research": "research.json",
        "script": "script.json",
        "storyboard": "storyboard.json",
        "subtitle": "subtitle.srt",
    }

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, session_id: str) -> Path:
        return self.root / session_id

    def create(self, session_id: str, metadata: dict[str, Any]) -> Path:
        project_dir = self.path(session_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        self.write_metadata(project_dir, metadata)
        return project_dir

    @staticmethod
    def metadata_path(project_dir: Path) -> Path:
        return project_dir / "project.json"

    @classmethod
    def read_metadata(cls, project_dir: Path) -> dict[str, Any]:
        return json.loads(cls.metadata_path(project_dir).read_text(encoding="utf-8"))

    @classmethod
    def write_metadata(cls, project_dir: Path, metadata: dict[str, Any]) -> None:
        project_dir.mkdir(parents=True, exist_ok=True)
        cls.metadata_path(project_dir).write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def artifact(cls, project_dir: Path, stage: str) -> Path:
        try:
            filename = cls.SOURCE_FILES[stage]
        except KeyError as exc:
            raise ValueError(f"Unknown project source stage: {stage}") from exc
        return project_dir / filename

    @staticmethod
    def prompt(project_dir: Path, stage: str) -> Path:
        return project_dir / f"{stage}_prompt.md"

    @classmethod
    def migrate_from_workspace(cls, workspace: Path, project_dir: Path) -> bool:
        """Copy authored artifacts from a legacy workspace into projects/ once."""
        changed = False
        project_dir.mkdir(parents=True, exist_ok=True)
        for stage, filename in cls.SOURCE_FILES.items():
            destination = project_dir / filename
            if destination.exists():
                continue
            legacy = workspace / stage / filename
            if legacy.exists() and legacy.is_file():
                shutil.copy2(legacy, destination)
                changed = True
        for stage in ("research", "script", "storyboard"):
            destination = cls.prompt(project_dir, stage)
            legacy = workspace / stage / "prompt.md"
            if not destination.exists() and legacy.exists():
                shutil.copy2(legacy, destination)
                changed = True
        return changed
