from abc import ABC
from abc import abstractmethod
from pathlib import Path


class SubtitleProvider(ABC):

    @abstractmethod
    def generate(
        self,
        audio: Path,
        output_dir: Path,
    ) -> None:
        pass