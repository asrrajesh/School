"""OpenAI provider implementation (chat completions + vision)."""

import base64

import openai

from llm.base import ImageInput, LLMProvider
from llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMPermissionError,
    LLMResponseError,
)


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMConfigurationError("OpenAI API key is not configured.")
        self._model = model
        self._client = openai.OpenAI(api_key=api_key)

    @property
    def name(self) -> str:
        return "openai"

    def generate_text(
        self,
        prompt: str,
        *,
        images: list[ImageInput] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        content: list[dict] = [{"type": "text", "text": prompt}]
        for image in images or []:
            data_url = f"data:{image.mime_type};base64,{base64.b64encode(image.data).decode('ascii')}"
            content.append({"type": "image_url", "image_url": {"url": data_url}})

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": content}],
            )
        except openai.AuthenticationError as exc:
            raise LLMAuthenticationError(
                "OpenAI denied the API key. Update OPENAI_API_KEY in .env."
            ) from exc
        except openai.PermissionDeniedError as exc:
            raise LLMPermissionError(
                "OpenAI denied access to the configured model. Check OPENAI_MODEL."
            ) from exc
        except openai.APIConnectionError as exc:
            raise LLMConnectionError("Could not reach OpenAI. Check your internet connection.") from exc
        except openai.APIStatusError as exc:
            raise LLMResponseError(f"OpenAI request failed ({exc.status_code}): {exc.message}") from exc

        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise LLMResponseError("OpenAI returned an empty response.")
        return text
