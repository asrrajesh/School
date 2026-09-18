"""Anthropic Claude provider implementation."""

import base64

import anthropic

from llm.base import ImageInput, LLMProvider
from llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMPermissionError,
    LLMResponseError,
)


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMConfigurationError("Anthropic API key is not configured.")
        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    @property
    def name(self) -> str:
        return "claude"

    def generate_text(
        self,
        prompt: str,
        *,
        images: list[ImageInput] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        content: list[dict] = []
        for image in images or []:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image.mime_type,
                        "data": base64.b64encode(image.data).decode("ascii"),
                    },
                }
            )
        content.append({"type": "text", "text": prompt})

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": content}],
            )
        except anthropic.AuthenticationError as exc:
            raise LLMAuthenticationError(
                "Claude denied the API key. Create an active Anthropic API key and update ANTHROPIC_API_KEY in .env."
            ) from exc
        except anthropic.PermissionDeniedError as exc:
            raise LLMPermissionError(
                "Claude denied access to the configured model. Check ANTHROPIC_MODEL and your Anthropic account permissions."
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise LLMConnectionError("Could not reach Claude. Check your internet connection.") from exc
        except anthropic.APIStatusError as exc:
            raise LLMResponseError(f"Claude request failed ({exc.status_code}): {exc.message}") from exc

        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if not text:
            raise LLMResponseError("Claude returned an empty response.")
        return text
