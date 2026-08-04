import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kvf.models.topic import Topic
from kvf.services.workspace_service import WorkspaceService


class SessionService:
    """Create, inspect, and update resumable video-generation sessions."""

    MANUAL_STAGES = ("research", "script", "storyboard")
    AUTOMATIC_OUTPUTS = (
        ("media", "media/media.json"),
        ("voice", "voice/narration.mp3"),
        ("subtitle", "subtitle/subtitle.srt"),
        ("timeline", "timeline/timeline.json"),
        ("video", "video/video.mp4"),
    )

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, name: str, category: str = "finance") -> Path:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("A project name is required.")

        base_id = self._slugify(clean_name)
        session_id = base_id
        suffix = 2
        while (self.root / session_id).exists():
            session_id = f"{base_id}-{suffix}"
            suffix += 1

        topic = Topic(id=session_id, name=clean_name, category="finance")
        workspace = WorkspaceService(str(self.root)).create(topic)
        now = self._now()
        metadata = self._read_metadata(workspace)
        metadata.update(
            {
                "created_at": now,
                "updated_at": now,
                "status": "in_progress",
                "current_stage": "research",
                "reference_date": datetime.now().astimezone().date().isoformat(),
            }
        )
        self._write_metadata(workspace, metadata)
        return workspace

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions: list[dict[str, Any]] = []
        for workspace in self.root.iterdir():
            if not workspace.is_dir():
                continue
            metadata_path = workspace / "metadata.json"
            if not metadata_path.exists():
                continue
            try:
                metadata = self._read_metadata(workspace)
                progress = self.inspect(workspace)
            except (OSError, json.JSONDecodeError):
                continue
            sessions.append({**metadata, **progress, "workspace": workspace})

        return sorted(
            sessions,
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )

    def inspect(self, workspace: Path) -> dict[str, Any]:
        completed: list[str] = []
        for stage in self.MANUAL_STAGES:
            if (workspace / stage / f"{stage}.json").exists():
                completed.append(stage)

        old_media_placeholders = self._has_old_media_placeholders(workspace)
        for stage, relative_path in self.AUTOMATIC_OUTPUTS:
            if old_media_placeholders and stage in {
                "media", "voice", "subtitle", "timeline", "video"
            }:
                continue
            if (workspace / relative_path).exists():
                completed.append(stage)

        if "video" in completed:
            current_stage = "complete"
            status = "complete"
        else:
            current_stage = "research"
            for stage in self.MANUAL_STAGES:
                if stage not in completed:
                    current_stage = stage
                    break
            else:
                current_stage = next(
                    (stage for stage, _ in self.AUTOMATIC_OUTPUTS if stage not in completed),
                    "complete",
                )
            status = "in_progress"

        return {
            "completed_stages": completed,
            "current_stage": current_stage,
            "status": status,
            "progress_percent": round(len(completed) / 8 * 100),
        }


    @staticmethod
    def _has_old_media_placeholders(workspace: Path) -> bool:
        media_json = workspace / "media" / "media.json"
        if not media_json.exists():
            return False
        try:
            payload = json.loads(media_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return True

        for asset in payload.get("assets", []):
            if (
                asset.get("source_url") == "local://generated-placeholder"
                or asset.get("author") == "Local placeholder"
            ):
                return True
        return False

    def touch(self, workspace: Path) -> None:
        metadata = self._read_metadata(workspace)
        metadata.update(self.inspect(workspace))
        metadata.pop("completed_stages", None)
        metadata.pop("progress_percent", None)
        metadata["updated_at"] = self._now()
        self._write_metadata(workspace, metadata)

    @staticmethod
    def extract_json(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        data = json.loads(cleaned)
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
        return slug[:60] or datetime.now().strftime("session-%Y%m%d-%H%M%S")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _read_metadata(workspace: Path) -> dict[str, Any]:
        return json.loads((workspace / "metadata.json").read_text(encoding="utf-8"))

    @staticmethod
    def _write_metadata(workspace: Path, metadata: dict[str, Any]) -> None:
        (workspace / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
