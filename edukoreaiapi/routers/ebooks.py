from fastapi import APIRouter, File, Form, UploadFile

from database.db import (
    get_scanned_chapter,
    get_scanned_chapters,
    get_scanned_classes,
    get_scanned_subjects,
    save_scanned_chapter,
    save_generated_questions,
    get_generated_questions,
    get_question_versions,
)
from services.claude_ocr import extract_text_from_images
from services.claude_questions import generate_questions_from_chapter
from schemas import SaveChapterRequest, GenerateQuestionsRequest

router = APIRouter(prefix="/api/ebooks", tags=["ebooks"])


@router.get("/classes")
def list_classes():
    return {"classes": get_scanned_classes()}


@router.get("/subjects")
def list_subjects(class_name: str):
    return {"subjects": get_scanned_subjects(class_name)}


@router.get("/chapters")
def list_chapters(class_name: str, subject: str):
    return {"chapters": get_scanned_chapters(class_name, subject)}


class _UploadedImage:
    """Adapts a FastAPI UploadFile to the (name, bytes) shape claude_ocr expects."""

    def __init__(self, name: str, data: bytes):
        self.name = name
        self.bytes = data


@router.get("/chapter")
def get_chapter(class_name: str, subject: str, chapter: str):
    record = get_scanned_chapter(class_name, subject, chapter)
    return {"content": record["content"] if record else None}


@router.post("/chapter")
def save_chapter(payload: SaveChapterRequest):
    return save_scanned_chapter(
        payload.class_name,
        payload.subject,
        payload.chapter,
        payload.content,
        payload.username,
    )


@router.post("/scan")
async def scan(images: list[UploadFile] = File(...)):
    uploaded = [_UploadedImage(image.filename, await image.read()) for image in images]
    try:
        content = extract_text_from_images(uploaded)
        return {"success": True, "content": content}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.get("/question-versions")
def list_question_versions(
    class_name: str,
    subject: str,
    chapter: str,
    assessment_category: str,
    assessment_number: int,
):
    """List every saved version number for a class/subject/chapter/assessment combo."""
    versions = get_question_versions(class_name, subject, chapter, assessment_category, assessment_number)
    return {"versions": versions}


@router.post("/generate-questions")
def generate_questions(payload: GenerateQuestionsRequest):
    """
    Generate questions using Claude AI based on chapter content and configuration.

    Fetches the chapter content, uses Claude to generate questions according to the
    user-configured question types/counts/marks/complexity, and saves them under
    the next version number for this class/subject/chapter/assessment.
    """
    try:
        chapter_record = get_scanned_chapter(payload.class_name, payload.subject, payload.chapter)
        if not chapter_record or not chapter_record.get("content"):
            return {
                "success": False,
                "error": f"Chapter content not found for {payload.chapter}. Please scan the e-book first.",
            }

        chapter_content = chapter_record["content"]
        question_rows = [row.model_dump() for row in payload.questionRows]

        generated_questions = generate_questions_from_chapter(
            chapter_content, question_rows, payload.complexity
        )

        db_result = save_generated_questions(
            payload.class_name,
            payload.subject,
            payload.chapter,
            payload.assessmentCategory,
            payload.assessmentNumber,
            payload.complexity,
            generated_questions,
            question_rows,
            payload.username,
        )

        if not db_result.get("success"):
            return db_result

        return {
            "success": True,
            "id": db_result["id"],
            "version": db_result["version"],
            "questions": generated_questions,
            "message": f"Generated {len(generated_questions)} questions successfully (Version {db_result['version']}).",
        }

    except Exception as exc:
        return {"success": False, "error": str(exc)}