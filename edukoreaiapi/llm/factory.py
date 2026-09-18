"""Factory for constructing the configured ``LLMProvider``.

This is the single place that knows how to translate the
``LLM_PROVIDER`` setting (and each provider's own config) into a
concrete instance. Callers only depend on ``LLMProvider`` (see
``llm.base``), so adding a new backend or switching the active one
never requires touching services/routers.
"""

from functools import lru_cache

from config.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_REQUEST_TIMEOUT,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from llm.base import LLMProvider
from llm.exceptions import LLMConfigurationError

_BUILDERS = {}


def _build_claude() -> LLMProvider:
    from llm.providers.claude_provider import ClaudeProvider

    return ClaudeProvider(api_key=ANTHROPIC_API_KEY, model=ANTHROPIC_MODEL)


def _build_openai() -> LLMProvider:
    from llm.providers.openai_provider import OpenAIProvider

    return OpenAIProvider(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)


def _build_gemini() -> LLMProvider:
    from llm.providers.gemini_provider import GeminiProvider

    return GeminiProvider(api_key=GEMINI_API_KEY, model=GEMINI_MODEL)


def _build_ollama() -> LLMProvider:
    from llm.providers.ollama_provider import OllamaProvider

    return OllamaProvider(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, timeout=OLLAMA_REQUEST_TIMEOUT)


_BUILDERS = {
    "claude": _build_claude,
    "openai": _build_openai,
    "gemini": _build_gemini,
    "ollama": _build_ollama,
}


@lru_cache(maxsize=None)
def _build_provider(provider_name: str) -> LLMProvider:
    try:
        builder = _BUILDERS[provider_name]
    except KeyError:
        raise LLMConfigurationError(
            f"Unknown LLM_PROVIDER '{provider_name}'. Valid options: {', '.join(_BUILDERS)}."
        ) from None
    return builder()


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """Return the configured ``LLMProvider`` (cached per provider name).

    Pass ``provider_name`` to override ``LLM_PROVIDER`` (e.g. for tests).
    """
    return _build_provider((provider_name or LLM_PROVIDER).strip().lower())
