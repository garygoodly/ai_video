from abc import ABC, abstractmethod

from kvf.models.application import Application


class BaseStep(ABC):

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def execute(self, application: Application) -> None:
        pass