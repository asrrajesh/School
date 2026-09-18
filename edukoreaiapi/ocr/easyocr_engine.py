"""EasyOCR-based OCR engine — local, free, works regardless of the LLM provider."""

import io

import numpy as np
from PIL import Image

from ocr.base import OCRProvider


class EasyOCREngine(OCRProvider):
    def __init__(self, languages: list[str] | None = None, gpu: bool = False):
        import easyocr  # heavy import, deferred until this engine is actually used

        self._reader = easyocr.Reader(languages or ["en"], gpu=gpu)

    @property
    def name(self) -> str:
        return "easyocr"

    def extract_text(self, image_bytes: bytes, *, filename: str | None = None) -> str:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = self._reader.readtext(np.array(image), detail=0, paragraph=True)
        return "\n".join(results).strip()
