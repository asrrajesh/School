"""Common interface for image-to-text OCR engines.

Kept separate from ``llm.base.LLMProvider`` so the OCR step never
depends on the LLM being vision-capable (e.g. text-only models like
qwen3:8b on Ollama can still be used for question generation while
EasyOCR handles the image step).
"""

from abc import ABC, abstractmethod


class OCRProvider(ABC):
    """Abstract base class for all OCR backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for logging/diagnostics, e.g. 'easyocr'."""

    @abstractmethod
    def extract_text(self, image_bytes: bytes, *, filename: str | None = None) -> str:
        """Extract raw text from a single image."""
