"""Factory for constructing the configured ``OCRProvider``.

Mirrors ``llm.factory`` — the single place that knows how to translate
``OCR_ENGINE`` into a concrete instance, so switching between EasyOCR
and LLM-vision OCR is a config change, not a code change.
"""

from functools import lru_cache

from config.config import OCR_ENGINE, OCR_LANGUAGES, OCR_USE_GPU
from ocr.base import OCRProvider


def _build_easyocr() -> OCRProvider:
    from ocr.easyocr_engine import EasyOCREngine

    return EasyOCREngine(languages=OCR_LANGUAGES, gpu=OCR_USE_GPU)


def _build_llm_vision() -> OCRProvider:
    from llm.factory import get_llm_provider
    from ocr.llm_vision_engine import LLMVisionEngine

    return LLMVisionEngine(get_llm_provider())


_BUILDERS = {
    "easyocr": _build_easyocr,
    "llm_vision": _build_llm_vision,
}


@lru_cache(maxsize=None)
def _build_engine(engine_name: str) -> OCRProvider:
    try:
        builder = _BUILDERS[engine_name]
    except KeyError:
        raise ValueError(
            f"Unknown OCR_ENGINE '{engine_name}'. Valid options: {', '.join(_BUILDERS)}."
        ) from None
    return builder()


def get_ocr_engine(engine_name: str | None = None) -> OCRProvider:
    """Return the configured ``OCRProvider`` (cached per engine name)."""
    return _build_engine((engine_name or OCR_ENGINE).strip().lower())
