from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract interface for all LLM providers.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.

        Parameters
        ----------
        prompt
            Complete prompt string.

        Returns
        -------
        str
            Raw response from the LLM.
        """
        raise NotImplementedError