import base64
import mimetypes

import anthropic

from config.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

_EXTRACTION_PROMPT = (
    "Extract all text from this textbook page exactly as written. "
    "Preserve headings, numbered lists, paragraphs, and questions. "
    "Return only the extracted text, with no commentary."
)


def extract_text_from_images(image_files) -> str:
    """Extract readable text from images using Claude's vision API.

    Each item in image_files must expose ``.name`` (str) and ``.bytes`` (bytes).
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key is not configured.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    extracted_sections = []
    for image_file in image_files:
        if not image_file.bytes:
            raise ValueError(f"Could not read {image_file.name}.")

        image_type = mimetypes.guess_type(image_file.name)[0] or "image/jpeg"
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_type,
                                    "data": base64.b64encode(image_file.bytes).decode("ascii"),
                                },
                            },
                            {"type": "text", "text": _EXTRACTION_PROMPT},
                        ],
                    }
                ],
            )
        except anthropic.AuthenticationError as exc:
            raise RuntimeError(
                "Claude denied the API key. Create an active Anthropic API key and update ANTHROPIC_API_KEY in .env."
            ) from exc
        except anthropic.PermissionDeniedError as exc:
            raise RuntimeError(
                "Claude denied access to the configured model. Check ANTHROPIC_MODEL and your Anthropic account permissions."
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise RuntimeError("Could not reach Claude. Check your internet connection.") from exc
        except anthropic.APIStatusError as exc:
            raise RuntimeError(f"Claude request failed ({exc.status_code}): {exc.message}") from exc

        text = "".join(block.text for block in response.content if block.type == "text").strip()
        extracted_sections.append(f"--- {image_file.name} ---\n{text}")

    return "\n\n".join(extracted_sections)
