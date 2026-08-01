from pathlib import Path

from kvf.models.blueprint import Blueprint
from kvf.utils.yaml_loader import load_yaml


class BlueprintService:

    def __init__(self, blueprint_directory: str):

        self.blueprint_directory = Path(blueprint_directory)

    def load(self, blueprint_name: str) -> Blueprint:

        path = self.blueprint_directory / f"{blueprint_name}.yaml"

        data = load_yaml(path)

        return Blueprint.model_validate(data)