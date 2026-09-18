"""Provider-based LLM service layer.

Exposes a common ``LLMProvider`` interface plus a ``get_llm_provider``
factory so callers never depend on a specific vendor SDK.
"""

from llm.base import ImageInput, LLMProvider
from llm.factory import get_llm_provider

__all__ = ["ImageInput", "LLMProvider", "get_llm_provider"]
