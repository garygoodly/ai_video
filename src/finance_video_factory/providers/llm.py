"""LLM provider boundary.

Version 0.2 uses manual ChatGPT prompt/response files and intentionally has no
paid API dependency. A future API provider can implement the same three stage
contracts without changing the rendering pipeline.
"""

from __future__ import annotations


class LLMProviderNotConfigured(RuntimeError):
    pass
