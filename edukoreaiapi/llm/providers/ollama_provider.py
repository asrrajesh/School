"""Local Ollama provider implementation (HTTP API, no vendor SDK required)."""

import base64

import httpx

from llm.base import ImageInput, LLMProvider
from llm.exceptions import LLMConnectionError, LLMResponseError


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, timeout: int = 120):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "ollama"

    def generate_text(
        self,
        prompt: str,
        *,
        images: list[ImageInput] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        message: dict = {"role": "user", "content": prompt}
        if images:
            message["images"] = [base64.b64encode(image.data).decode("ascii") for image in images]

        payload = {
            "model": self._model,
            "messages": [message],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            response = httpx.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMConnectionError(
                f"Could not reach Ollama at {self._base_url}. Is it running?"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMConnectionError("Ollama request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMResponseError(f"Ollama request failed ({exc.response.status_code}): {exc.response.text}") from exc

        data = response.json()
        text = (data.get("message", {}).get("content") or "").strip()
        if not text:
            raise LLMResponseError("Ollama returned an empty response.")
        return text
