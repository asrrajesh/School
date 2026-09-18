"""Question generation/extraction service, backed by the configured LLM provider.

Depends only on the ``LLMProvider`` abstraction (dependency inversion) —
callers can inject any provider, or rely on the default from the factory.
"""

from llm.base import LLMProvider
from llm.factory import get_llm_provider
from llm.prompts.templates import build_paper_extraction_prompt, build_question_generation_prompt


def generate_questions_from_chapter(
    chapter_content: str,
    question_rows: list[dict],
    complexity: str = "intermediate",
    provider: LLMProvider | None = None,
) -> list[dict]:
    """
    Generate questions from chapter content using the configured LLM provider.

    Args:
        chapter_content: The textbook chapter content to base questions on.
        question_rows: List of dicts with questionType, questionCount, marksPerQuestion.
        complexity: Overall difficulty — "basic" | "intermediate" | "advanced".
        provider: Optional explicit provider (defaults to the configured one).

    Returns:
        List of generated questions with type, text, options (for MCQ), marks.
    """
    llm = provider or get_llm_provider()
    prompt = build_question_generation_prompt(chapter_content, question_rows, complexity)
    data = llm.generate_json(prompt, max_tokens=4096)
    return data.get("questions", [])


def extract_questions_from_paper(
    paper_text: str,
    complexity: str = "intermediate",
    provider: LLMProvider | None = None,
) -> list[dict]:
    """
    Extract questions from an uploaded question paper's text (from OCR).

    Args:
        paper_text: The extracted text from uploaded question paper images.
        complexity: The difficulty level to assign extracted questions.
        provider: Optional explicit provider (defaults to the configured one).

    Returns:
        List of extracted questions with type, text, options (for MCQ), marks.
    """
    llm = provider or get_llm_provider()
    prompt = build_paper_extraction_prompt(paper_text)
    data = llm.generate_json(prompt, max_tokens=4096)
    return data.get("questions", [])
