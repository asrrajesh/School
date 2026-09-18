"""Common interface every LLM provider must implement.

Following the dependency-inversion principle, services depend on this
abstraction (``LLMProvider``) rather than any concrete vendor SDK.
Switching providers is a configuration change (see ``llm.factory``),
not a code change.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from llm.json_utils import parse_json_response


@dataclass
class ImageInput:
    """A single image to ground a prompt on (e.g. for OCR)."""

    name: str
    data: bytes
    mime_type: str = "image/jpeg"


class LLMProvider(ABC):
    """Abstract base class for all LLM backends (Claude, OpenAI, Gemini, Ollama, ...)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for logging/diagnostics, e.g. 'claude'."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        *,
        images: list[ImageInput] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        """Generate free-form text, optionally grounded on one or more images."""

    def generate_json(
        self,
        prompt: str,
        *,
        images: list[ImageInput] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> dict:
        """Generate a JSON object. Providers may override for native JSON modes."""
        text = self.generate_text(
            prompt, images=images, max_tokens=max_tokens, temperature=temperature
        )
        return parse_json_response(text, source=self.name)
