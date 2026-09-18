"""OCR service: extracts text from scanned images via the configured OCR engine.

Depends only on the ``OCRProvider`` abstraction (dependency inversion) —
decoupled from the LLM layer so text-only LLMs (e.g. qwen3:8b on Ollama)
can still be used downstream for question generation.
"""

from ocr.base import OCRProvider
from ocr.factory import get_ocr_engine


def extract_text_from_images(image_files, engine: OCRProvider | None = None) -> str:
    """Extract readable text from images using the configured OCR engine.

    Each item in ``image_files`` must expose ``.name`` (str) and ``.bytes`` (bytes).
    """
    ocr = engine or get_ocr_engine()

    extracted_sections = []
    for image_file in image_files:
        if not image_file.bytes:
            raise ValueError(f"Could not read {image_file.name}.")

        text = ocr.extract_text(image_file.bytes, filename=image_file.name)
        extracted_sections.append(f"--- {image_file.name} ---\n{text}")

    return "\n\n".join(extracted_sections)

