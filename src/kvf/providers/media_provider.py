from abc import ABC
from abc import abstractmethod
from pathlib import Path

from kvf.models.media import MediaAsset
from kvf.models.storyboard import StoryboardScene


class MediaProvider(ABC):

    @abstractmethod
    def download(
        self,
        scene: StoryboardScene,
        output_file: Path,
    ) -> MediaAsset:
        pass