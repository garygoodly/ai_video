from __future__ import annotations
import json, re, shutil, subprocess
from datetime import datetime
from pathlib import Path
import yaml

def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def ensure_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required executable not found on PATH: {name}")

def run(command: list[str]) -> None:
    subprocess.run(command, check=True)

def slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return value[:70] or datetime.now().strftime("run-%Y%m%d")
