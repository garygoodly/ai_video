import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kvf.models.topic import Topic
from kvf.services.project_source_service import ProjectSourceService
from kvf.services.workspace_service import WorkspaceService


class SessionService:
    """Create, inspect, migrate, and update resumable video-generation sessions."""

    MANUAL_STAGES = ("research", "script", "storyboard")
    AUTOMATIC_OUTPUTS = (
        ("media", "assets/media.json"),
        ("voice", "voice/narration.mp3"),
        ("subtitle", "subtitle/subtitle.srt"),
        ("timeline", "timeline/timeline.json"),
        ("video", "video/video.mp4"),
    )

    def __init__(self, root: str | Path, projects_root: str | Path | None = None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.projects_root = Path(projects_root) if projects_root else self.root.parent / "projects"
        self.sources = ProjectSourceService(self.projects_root)
        self._migrate_legacy_sessions()

    def create(
        self,
        name: str,
        category: str = "finance",
        edition: str = "global",
        edition_profile: dict[str, Any] | None = None,
    ) -> Path:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("A project name is required.")

        base_id = self._slugify(clean_name)
        session_id = base_id
        suffix = 2
        while (self.root / session_id).exists() or self.sources.path(session_id).exists():
            session_id = f"{base_id}-{suffix}"
            suffix += 1

        topic = Topic(id=session_id, name=clean_name, category="finance")
        workspace = WorkspaceService(str(self.root)).create(topic)
        now = self._now()
        profile = dict(edition_profile or {})
        metadata = {
            "id": topic.id,
            "name": topic.name,
            "category": topic.category,
            "created_at": now,
            "updated_at": now,
            "status": "in_progress",
            "current_stage": "research",
            "reference_date": datetime.now().astimezone().date().isoformat(),
            "edition": edition,
            "edition_label": profile.get("label", edition.title()),
            "language_code": profile.get("language_code", "en-US"),
            "output_language": profile.get("output_language", "English"),
            "whisper_language": profile.get("whisper_language", "en"),
            "voice_engine": "edge",
            "voice": profile.get("default_voice", "en-US-AndrewNeural"),
            "voice_rate": "+0%",
            "voice_pitch": "+0Hz",
            "narration_mode": "continuous",
            "subtitles_enabled": False,
            "edition_profile": profile,
            "subtitle_settings": {
                "max_words": profile.get("subtitle_max_words", 10),
                "max_characters": profile.get("subtitle_max_characters", 58),
                "max_duration_seconds": 4.5,
                "min_characters": profile.get("subtitle_min_characters", 6),
                "source": "approved_script_exact",
            },
            "subtitle_style": {
                "preset": "Compact",
                "font_name": profile.get("default_subtitle_font", "Arial"),
            },
            "media_settings": {
                "visual_persistence": "topic",
                "prefer_market_charts": True,
                "strict_precision": True,
            },
        }
        project_dir = self.sources.create(session_id, metadata)
        self._write_workspace_pointer(workspace, project_dir)
        return workspace

    def list_sessions(self) -> list[dict[str, Any]]:
        self._migrate_legacy_sessions()
        sessions: list[dict[str, Any]] = []
        for project_dir in self.projects_root.iterdir():
            if not project_dir.is_dir() or not (project_dir / "project.json").exists():
                continue
            try:
                metadata = ProjectSourceService.read_metadata(project_dir)
                workspace = self._ensure_workspace(metadata, project_dir)
                progress = self.inspect(workspace)
            except (OSError, json.JSONDecodeError, KeyError):
                continue
            sessions.append({**metadata, **progress, "workspace": workspace, "source_dir": project_dir})

        return sorted(sessions, key=lambda item: item.get("updated_at", ""), reverse=True)

    def inspect(self, workspace: Path) -> dict[str, Any]:
        project_dir = self.project_dir_for(workspace)
        completed: list[str] = []
        for stage in self.MANUAL_STAGES:
            if ProjectSourceService.artifact(project_dir, stage).exists():
                completed.append(stage)

        old_media_placeholders = self._has_old_media_placeholders(workspace)
        for stage, relative_path in self.AUTOMATIC_OUTPUTS:
            if old_media_placeholders and stage in {"media", "voice", "subtitle", "timeline", "video"}:
                continue
            if (workspace / relative_path).exists():
                completed.append(stage)

        if "video" in completed:
            current_stage, status = "complete", "complete"
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

    def project_dir_for(self, workspace: Path) -> Path:
        pointer = workspace / "metadata.json"
        if pointer.exists():
            try:
                raw = json.loads(pointer.read_text(encoding="utf-8"))
                value = raw.get("project_source")
                if value:
                    candidate = Path(value)
                    if not candidate.is_absolute():
                        candidate = (workspace.parent.parent / candidate).resolve()
                    return candidate
            except (OSError, json.JSONDecodeError):
                pass
        return self.projects_root / workspace.name

    def touch(self, workspace: Path) -> None:
        metadata = self._read_metadata(workspace)
        metadata.update(self.inspect(workspace))
        metadata.pop("completed_stages", None)
        metadata.pop("progress_percent", None)
        metadata["updated_at"] = self._now()
        self._write_metadata(workspace, metadata)

    def _migrate_legacy_sessions(self) -> None:
        if not self.root.exists():
            return
        for workspace in self.root.iterdir():
            if not workspace.is_dir() or not (workspace / "metadata.json").exists():
                continue
            try:
                legacy = json.loads((workspace / "metadata.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            session_id = legacy.get("id", workspace.name)
            project_dir = self.sources.path(session_id)
            if not (project_dir / "project.json").exists():
                metadata = dict(legacy)
                metadata.setdefault("id", session_id)
                metadata.setdefault("name", session_id)
                metadata.setdefault("category", "finance")
                metadata.setdefault("created_at", self._now())
                metadata.setdefault("updated_at", self._now())
                self.sources.create(session_id, metadata)
            ProjectSourceService.migrate_from_workspace(workspace, project_dir)
            self._write_workspace_pointer(workspace, project_dir)

    def _ensure_workspace(self, metadata: dict[str, Any], project_dir: Path) -> Path:
        topic = Topic(
            id=metadata["id"],
            name=metadata.get("name", metadata["id"]),
            category=metadata.get("category", "finance"),
        )
        workspace = WorkspaceService(str(self.root)).create(topic)
        self._write_workspace_pointer(workspace, project_dir)
        return workspace

    @staticmethod
    def _has_old_media_placeholders(workspace: Path) -> bool:
        media_json = workspace / "assets" / "media.json"
        if not media_json.exists():
            return False
        try:
            payload = json.loads(media_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return True
        return any(
            asset.get("source_url") == "local://generated-placeholder"
            or asset.get("author") == "Local placeholder"
            for asset in payload.get("assets", [])
        )

    def _write_workspace_pointer(self, workspace: Path, project_dir: Path) -> None:
        relative = Path("projects") / project_dir.name
        (workspace / "metadata.json").write_text(
            json.dumps({"id": workspace.name, "project_source": relative.as_posix()}, indent=2),
            encoding="utf-8",
        )

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
    def _project_dir_from_workspace(workspace: Path) -> Path:
        pointer = workspace / "metadata.json"
        if pointer.exists():
            try:
                raw = json.loads(pointer.read_text(encoding="utf-8"))
                if raw.get("project_source"):
                    return workspace.parent.parent / raw["project_source"]
            except (OSError, json.JSONDecodeError):
                pass
        return workspace.parent.parent / "projects" / workspace.name

    @classmethod
    def _read_metadata(cls, workspace: Path) -> dict[str, Any]:
        project_dir = cls._project_dir_from_workspace(workspace)
        project_json = project_dir / "project.json"
        if project_json.exists():
            return json.loads(project_json.read_text(encoding="utf-8"))
        return json.loads((workspace / "metadata.json").read_text(encoding="utf-8"))

    @classmethod
    def _write_metadata(cls, workspace: Path, metadata: dict[str, Any]) -> None:
        project_dir = cls._project_dir_from_workspace(workspace)
        ProjectSourceService.write_metadata(project_dir, metadata)
        relative = Path("projects") / project_dir.name
        (workspace / "metadata.json").write_text(
            json.dumps({"id": metadata.get("id", workspace.name), "project_source": relative.as_posix()}, indent=2),
            encoding="utf-8",
        )
