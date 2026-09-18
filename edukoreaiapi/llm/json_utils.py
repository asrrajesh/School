"""Helpers for parsing JSON out of raw LLM text responses.

LLMs frequently wrap JSON in markdown code fences or add stray
whitespace/commentary; this centralizes the cleanup so every provider
and service can rely on the same parsing behaviour.
"""

import json

from llm.exceptions import LLMResponseError


def strip_code_fence(text: str) -> str:
    """Remove a leading/trailing ``` or ```json fence, if present."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return cleaned


def parse_json_response(text: str, *, source: str = "LLM") -> dict:
    """Parse ``text`` as JSON, raising ``LLMResponseError`` with context on failure."""
    if not text or not text.strip():
        raise LLMResponseError(f"{source} returned an empty response.")

    cleaned = strip_code_fence(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        preview = cleaned[:500]
        raise LLMResponseError(
            f"Failed to parse {source}'s response as JSON: {exc}\nResponse preview: {preview}"
        ) from exc
