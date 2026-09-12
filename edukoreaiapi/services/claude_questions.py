"""Generate questions using Claude AI based on chapter content and configuration."""

import json
import anthropic

from config.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

_COMPLEXITY_GUIDANCE = {
    "basic": (
        "Basic — test direct recall and simple definitions straight from the "
        "chapter. Keep language simple and avoid multi-step reasoning."
    ),
    "intermediate": (
        "Intermediate — mix recall with 'why' and 'how' questions that require "
        "understanding and applying a concept, not just repeating it."
    ),
    "advanced": (
        "Advanced — favor higher-order thinking: analysis, comparison, or "
        "connecting multiple concepts from the chapter. Avoid pure recall."
    ),
}


def generate_questions_from_chapter(
    chapter_content: str,
    question_rows: list[dict],
    complexity: str = "intermediate",
) -> list[dict]:
    """
    Generate questions using Claude AI.

    Args:
        chapter_content: The textbook chapter content to base questions on.
        question_rows: List of dicts with:
            - questionType: "mcq" | "short" | "long"
            - questionCount: number of questions
            - marksPerQuestion: marks per question
        complexity: Overall difficulty for every question generated —
            "basic" | "intermediate" | "advanced".

    Returns:
        List of generated questions with type, text, options (for MCQ), marks.
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key is not configured.")

    requirements = []
    for row in question_rows:
        q_type = row.get("questionType", "").lower()
        count = row.get("questionCount", 0)
        marks = row.get("marksPerQuestion", 0)

        if q_type == "mcq":
            requirements.append(
                f"- {count} multiple-choice questions ({marks} marks each) "
                f"with 4 options and one correct answer"
            )
        elif q_type == "short":
            requirements.append(
                f"- {count} short-answer questions ({marks} marks each) "
                f"with a brief answer key (1-2 sentences)"
            )
        elif q_type == "long":
            requirements.append(
                f"- {count} long-answer questions ({marks} marks each) "
                f"with a detailed answer key (3-5 sentences)"
            )

    complexity_key = (complexity or "intermediate").strip().lower()
    complexity_instruction = _COMPLEXITY_GUIDANCE.get(
        complexity_key, _COMPLEXITY_GUIDANCE["intermediate"]
    )

    prompt = f"""You are an expert teacher. Generate questions based on the following chapter content.

CHAPTER CONTENT:
{chapter_content}

DIFFICULTY LEVEL FOR ALL QUESTIONS: {complexity_key.capitalize()}
{complexity_instruction}

QUESTIONS TO GENERATE:
{chr(10).join(requirements)}

Generate the questions in JSON format with the following structure:
{{
  "questions": [
    {{
      "type": "mcq" | "short" | "long",
      "marks": <number>,
      "question": "<question text>",
      "options": ["A", "B", "C", "D"],  // only for MCQ
      "correctOption": "A",  // only for MCQ (e.g., "A", "B", "C", or "D")
      "answerKey": "<answer or explanation>"
    }},
    ...
  ]
}}

Guidelines:
- For MCQ: Include exactly 4 options (A, B, C, D). Indicate the correct option.
- For short/long answers: Provide clear, concise answer keys.
- Questions should be diverse and cover different parts of the chapter.
- Ensure questions test understanding, not just recall.
- Match the {complexity_key} difficulty level described above for every question.
- Make sure the total marks matches the configuration (count × marksPerQuestion).

Return ONLY valid JSON, no additional text."""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
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

    response_text = "".join(block.text for block in response.content if block.type == "text").strip()

    if not response_text:
        raise RuntimeError("Claude returned an empty response. Check chapter content and try again.")

    if response_text.startswith("```"):
        response_text = response_text.strip("`").strip()
        if response_text.startswith("json"):
            response_text = response_text[4:].strip()

    try:
        data = json.loads(response_text)
        questions = data.get("questions", [])
        return questions
    except json.JSONDecodeError as exc:
        preview = response_text[:500] if len(response_text) > 500 else response_text
        raise RuntimeError(
            f"Failed to parse Claude's response as JSON: {exc}\n"
            f"Response preview: {preview}"
        ) from exc