from pathlib import Path


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()