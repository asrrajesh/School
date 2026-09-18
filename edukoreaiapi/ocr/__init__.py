"""Standalone OCR layer, decoupled from the LLM service.

Exposes ``OCRProvider`` (see ``ocr.base``) plus ``get_ocr_engine`` so the
image-to-text step never has to depend on a vision-capable LLM.
"""

from ocr.base import OCRProvider
from ocr.factory import get_ocr_engine

__all__ = ["OCRProvider", "get_ocr_engine"]
