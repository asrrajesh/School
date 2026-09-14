from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from database.db import (
    get_scanned_chapter,
    get_scanned_chapters,
    get_scanned_classes,
    get_scanned_subjects,
    save_scanned_chapter,
    save_generated_questions,
    get_generated_questions,
    get_question_versions,
    #save_uploaded_questions,
)
from services.claude_ocr import extract_text_from_images
from services.claude_questions import generate_questions_from_chapter, extract_questions_from_paper
from services.paper_generator import generate_question_paper_docx
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
    chapters: str,
    assessment_category: str,
    assessment_number: int,
):
    """
    List every saved version number for a class/subject/chapters/assessment combo.
    Note: chapters is comma-separated (e.g., "Chapter1,Chapter2,Chapter3")
    """
    chapter_list = [ch.strip() for ch in chapters.split(",") if ch.strip()]
    versions = get_question_versions(
        class_name,
        subject,
        chapter_list,
        assessment_category,
        assessment_number,
    )
    return {"versions": versions}


@router.post("/generate-questions")
def generate_questions(payload: GenerateQuestionsRequest):
    """
    Generate questions using Claude AI based on chapter content and configuration.

    Fetches the chapter content, uses Claude to generate questions according to the
    user-configured question types/counts/marks/complexity, and saves them under
    the next version number for this class/subject/chapters/assessment.
    """
    try:
        # Fetch content from all selected chapters and concatenate
        chapter_contents = []
        for chapter in payload.chapters:
            chapter_record = get_scanned_chapter(payload.class_name, payload.subject, chapter)
            if chapter_record and chapter_record.get("content"):
                chapter_contents.append(f"--- {chapter} ---\n{chapter_record['content']}")

        if not chapter_contents:
            return {
                "success": False,
                "error": f"Chapter content not found. Please scan the e-books first.",
            }

        combined_chapter_content = "\n\n".join(chapter_contents)
        question_rows = [row.model_dump() for row in payload.questionRows]

        generated_questions = generate_questions_from_chapter(
            combined_chapter_content, question_rows, payload.complexity
        )

        db_result = save_generated_questions(
            payload.class_name,
            payload.subject,
            payload.chapters,
            payload.assessmentCategory,
            payload.assessmentNumber,
            payload.complexity,
            generated_questions,
            question_rows,
            payload.username,
            source="generated",
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


@router.post("/upload-questions")
async def upload_questions(
    class_name: str = Form(...),
    subject: str = Form(...),
    chapters: str = Form(...),
    assessment_category: str = Form(...),
    assessment_number: int = Form(...),
    complexity: str = Form(...),
    username: str = Form(...),
    images: list[UploadFile] = File(...),
):
    """
    Upload a question paper (as images) and extract questions using Claude AI.
    Saves extracted questions to MongoDB with source='uploaded'.

    Args:
        class_name: e.g., "Class 10"
        subject: e.g., "Physics"
        chapters: Comma-separated chapter names
        assessment_category: "fa" or "sa"
        assessment_number: 1 or 2
        complexity: "basic", "intermediate", or "advanced"
        username: Current user
        images: List of uploaded image files
    """
    try:
        # Step 1: Extract text from uploaded images
        uploaded = [_UploadedImage(image.filename, await image.read()) for image in images]
        paper_text = extract_text_from_images(uploaded)

        if not paper_text or not paper_text.strip():
            return {"success": False, "error": "Could not extract text from uploaded images."}

        # Step 2: Extract questions from the paper text using Claude
        extracted_questions = extract_questions_from_paper(paper_text, complexity)

        if not extracted_questions:
            return {
                "success": False,
                "error": "Could not extract questions from the paper. Please check the image quality.",
            }

        chapter_list = [ch.strip() for ch in chapters.split(",") if ch.strip()]

        # Step 3: Save extracted questions to MongoDB
        db_result = save_generated_questions(
            class_name,
            subject,
            chapter_list,
            assessment_category,
            assessment_number,
            complexity,
            extracted_questions,
            [],  # No configuration for uploaded questions
            username,
            source="uploaded",
            source_content=paper_text,
        )

        if not db_result.get("success"):
            return db_result

        return {
            "success": True,
            "id": db_result["id"],
            "version": db_result["version"],
            "questions": extracted_questions,
            "message": f"Uploaded and extracted {len(extracted_questions)} questions successfully (Version {db_result['version']}).",
        }

    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.get("/generate-questions/document")
def download_question_paper(
    class_name: str,
    subject: str,
    chapters: str,
    assessment_category: str,
    assessment_number: int,
    version: int,
):
    """
    Download a previously-generated or uploaded, saved version of a question paper as a
    formatted .docx file.

    This does NOT call Claude / any AI service -- it reads the already-saved
    questions for the given class/subject/chapters/assessment/version straight
    from MongoDB (via get_generated_questions) and renders them into a Word
    document. Returns 404 if that version doesn't exist.
    """
    chapter_list = [ch.strip() for ch in chapters.split(",") if ch.strip()]

    document = get_generated_questions(
        class_name, subject, chapter_list, assessment_category, assessment_number, version
    )
    if not document:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No saved questions found for {class_name} / {subject} / {', '.join(chapter_list)} "
                f"({assessment_category.upper()} {assessment_number}, Version {version})."
            ),
        )

    try:
        docx_bytes = generate_question_paper_docx(document)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    chapters_str = "-".join(chapter_list)
    safe_subject = subject.replace("/", "-")
    safe_chapters = chapters_str.replace("/", "-")
    filename = f"{assessment_category.upper()}{assessment_number} - {safe_subject} - {safe_chapters} - v{version}.docx"
    encoded_filename = quote(filename)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": (
                f"attachment; filename=\"{filename.encode('ascii', 'ignore').decode() or 'question_paper.docx'}\"; "
                f"filename*=UTF-8''{encoded_filename}"
            )
        },
    )
