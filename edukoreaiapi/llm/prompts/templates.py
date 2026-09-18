"""Prompt templates for OCR extraction and question generation/extraction.

Kept free of any provider-specific code so the same templates work
regardless of which ``LLMProvider`` is configured.
"""

OCR_EXTRACTION_PROMPT = (
    "Extract all text from this textbook page exactly as written. "
    "Preserve headings, numbered lists, paragraphs, and questions. "
    "Return only the extracted text, with no commentary."
)

COMPLEXITY_GUIDANCE = {
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

_QUESTION_JSON_SHAPE = """{
  "questions": [
    {
      "type": "mcq" | "short" | "long",
      "marks": <number>,
      "question": "<question text>",
      "options": ["A", "B", "C", "D"],  // only for MCQ
      "correctOption": "A",  // only for MCQ (e.g., "A", "B", "C", or "D")
      "answerKey": "<answer or explanation>"
    },
    ...
  ]
}"""


def resolve_complexity(complexity: str) -> tuple[str, str]:
    """Return (normalized_key, guidance_text) for a complexity level."""
    key = (complexity or "intermediate").strip().lower()
    return key, COMPLEXITY_GUIDANCE.get(key, COMPLEXITY_GUIDANCE["intermediate"])


def build_question_requirements(question_rows: list[dict]) -> list[str]:
    """Turn question-row configs into human-readable generation requirements."""
    requirements = []
    for row in question_rows:
        q_type = (row.get("questionType") or "").lower()
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
    return requirements


def build_question_generation_prompt(
    chapter_content: str,
    question_rows: list[dict],
    complexity: str,
) -> str:
    """Prompt for generating new questions from chapter content."""
    complexity_key, complexity_instruction = resolve_complexity(complexity)
    requirements = build_question_requirements(question_rows)

    return f"""You are an expert teacher. Generate questions based on the following chapter content.

CHAPTER CONTENT:
{chapter_content}

DIFFICULTY LEVEL FOR ALL QUESTIONS: {complexity_key.capitalize()}
{complexity_instruction}

QUESTIONS TO GENERATE:
{chr(10).join(requirements)}

Generate the questions in JSON format with the following structure:
{_QUESTION_JSON_SHAPE}

Guidelines:
- For MCQ: Include exactly 4 options (A, B, C, D). Indicate the correct option.
- For short/long answers: Provide clear, concise answer keys.
- Questions should be diverse and cover different parts of the chapter.
- Ensure questions test understanding, not just recall.
- Match the {complexity_key} difficulty level described above for every question.
- Make sure the total marks matches the configuration (count × marksPerQuestion).

Return ONLY valid JSON, no additional text."""


def build_paper_extraction_prompt(paper_text: str) -> str:
    """Prompt for extracting structured questions from an uploaded paper's text."""
    return f"""You are an expert teacher analyzing an uploaded question paper.
Extract all questions from the following paper text and identify:
1. Question type (MCQ, short-answer, or long-answer based on number of options and answer length)
2. Question text
3. Marks (if visible in the paper)
4. Options (for MCQ questions)
5. Correct answer/answer key (if present in the paper)

QUESTION PAPER TEXT:
{paper_text}

Extract the questions in JSON format with the following structure:
{_QUESTION_JSON_SHAPE}

Guidelines:
- If marks are not clearly visible, assign 1 mark for MCQ, 2 for short, 5 for long.
- For MCQ: Extract exactly 4 options if available, labeled A, B, C, D.
- Identify correct answer from the paper's answer key if present.
- Preserve the exact question text from the paper.
- If answerKey is not in the paper, leave it as empty string "".
- Be strict about identifying question types based on the actual format in the paper.

Return ONLY valid JSON, no additional text."""
