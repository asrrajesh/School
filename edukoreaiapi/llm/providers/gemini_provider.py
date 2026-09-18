"""Google Gemini provider implementation."""

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from llm.base import ImageInput, LLMProvider
from llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMPermissionError,
    LLMResponseError,
)


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMConfigurationError("Gemini API key is not configured.")
        genai.configure(api_key=api_key)
        self._model_name = model
        self._model = genai.GenerativeModel(model)

    @property
    def name(self) -> str:
        return "gemini"

    def generate_text(
        self,
        prompt: str,
        *,
        images: list[ImageInput] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        parts: list = [prompt]
        for image in images or []:
            parts.append({"mime_type": image.mime_type, "data": image.data})

        try:
            response = self._model.generate_content(
                parts,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
        except google_exceptions.Unauthenticated as exc:
            raise LLMAuthenticationError(
                "Gemini denied the API key. Update GEMINI_API_KEY in .env."
            ) from exc
        except google_exceptions.PermissionDenied as exc:
            raise LLMPermissionError(
                "Gemini denied access to the configured model. Check GEMINI_MODEL."
            ) from exc
        except (google_exceptions.ServiceUnavailable, google_exceptions.DeadlineExceeded) as exc:
            raise LLMConnectionError("Could not reach Gemini. Check your internet connection.") from exc
        except google_exceptions.GoogleAPIError as exc:
            raise LLMResponseError(f"Gemini request failed: {exc}") from exc

        text = (getattr(response, "text", "") or "").strip()
        if not text:
            raise LLMResponseError("Gemini returned an empty response.")
        return text
