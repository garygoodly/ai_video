from pathlib import Path

import yaml


def load_yaml(path: str) -> dict:
    """
    Load a YAML file.

    Parameters
    ----------
    path : str
        Path to yaml file.

    Returns
    -------
    dict
    """
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)