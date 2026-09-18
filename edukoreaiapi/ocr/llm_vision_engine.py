"""OCR engine that delegates to a vision-capable LLM provider.

Use this when OCR_ENGINE=llm_vision and LLM_PROVIDER points at a model
that can actually see images (claude, openai, gemini, or an Ollama
vision model like llava/qwen2-vl). Text-only models (e.g. qwen3:8b)
cannot be used here — pair those with the "easyocr" engine instead.
"""

import mimetypes

from llm.base import ImageInput, LLMProvider
from llm.prompts.templates import OCR_EXTRACTION_PROMPT
from ocr.base import OCRProvider


class LLMVisionEngine(OCRProvider):
    def __init__(self, provider: LLMProvider):
        self._provider = provider

    @property
    def name(self) -> str:
        return f"llm_vision:{self._provider.name}"

    def extract_text(self, image_bytes: bytes, *, filename: str | None = None) -> str:
        mime_type = (mimetypes.guess_type(filename)[0] if filename else None) or "image/jpeg"
        image = ImageInput(name=filename or "image", data=image_bytes, mime_type=mime_type)
        return self._provider.generate_text(
            OCR_EXTRACTION_PROMPT, images=[image], max_tokens=4096, temperature=0
        )
