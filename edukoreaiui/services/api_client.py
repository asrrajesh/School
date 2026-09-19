"""
Thin HTTP client used by the UI to talk to the edukoreaiapi backend.
Function names/signatures mirror the previous direct-database calls so the
screen modules only need to change their import.
"""

import httpx

from config.config import API_BASE_URL

_TIMEOUT = httpx.Timeout(30.0)


def _connection_error(exc: Exception) -> dict:
    return {"success": False, "error": f"Cannot reach the API server at {API_BASE_URL}. ({exc})"}


def login_user(username: str, password: str) -> dict:
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)


def register_user(username: str, password: str) -> dict:
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/auth/signup",
            json={"username": username, "password": password},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)


def request_password_reset(username: str) -> dict:
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/auth/forgot-password",
            json={"username": username},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)


def google_callback(code: str) -> dict:
    """Send Google auth code to backend for secure token exchange and user creation/login."""
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/auth/google-callback",
            params={"code": code},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)


def get_scanned_chapter(class_name: str, subject: str, chapter: str) -> dict | None:
    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/ebooks/chapter",
            params={"class_name": class_name, "subject": subject, "chapter": chapter},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        content = response.json().get("content")
        return {"content": content} if content is not None else None
    except httpx.HTTPError:
        return None


def save_scanned_chapter(class_name: str, subject: str, chapter: str, content: str, username: str) -> dict:
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/ebooks/chapter",
            json={
                "class_name": class_name,
                "subject": subject,
                "chapter": chapter,
                "content": content,
                "username": username,
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)


def get_classes() -> list[str]:
    try:
        response = httpx.get(f"{API_BASE_URL}/api/ebooks/classes", timeout=_TIMEOUT)
        response.raise_for_status()
        return response.json().get("classes", [])
    except httpx.HTTPError:
        return []


def get_subjects(class_name: str) -> list[str]:
    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/ebooks/subjects",
            params={"class_name": class_name},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("subjects", [])
    except httpx.HTTPError:
        return []


def get_chapters(class_name: str, subject: str) -> list[str]:
    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/ebooks/chapters",
            params={"class_name": class_name, "subject": subject},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("chapters", [])
    except httpx.HTTPError:
        return []


def scan_images(image_files) -> str:
    """Upload images to the API and return the extracted text."""
    files = [
        ("images", (image_file.name, image_file.bytes, "application/octet-stream"))
        for image_file in image_files
    ]
    # OCR (EasyOCR model load on first run, or LLM vision) can take well over 30s.
    response = httpx.post(f"{API_BASE_URL}/api/ebooks/scan", files=files, timeout=httpx.Timeout(300.0))
    response.raise_for_status()
    result = response.json()
    if not result.get("success"):
        raise RuntimeError(result.get("error", "Scan failed."))
    return result["content"]


def generate_questions(
    class_name: str,
    subject: str,
    chapters: list[str],
    assessment_category: str,
    assessment_number: int,
    complexity: str,
    question_rows: list[dict],
    username: str,
) -> dict:
    """
    Generate questions using Claude AI based on chapter content and configuration.

    Returns:
        {'success': True, 'id': '<id>', 'version': <int>, 'questions': [...]}
        or {'success': False, 'error': '...'}
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/ebooks/generate-questions",
            json={
                "class_name": class_name,
                "subject": subject,
                "chapters": chapters,
                "assessmentCategory": assessment_category,
                "assessmentNumber": assessment_number,
                "complexity": complexity,
                "questionRows": question_rows,
                "username": username,
            },
            timeout=httpx.Timeout(120.0),  # Question generation may take longer
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)


def upload_questions(
    class_name: str,
    subject: str,
    chapters: list[str],
    assessment_category: str,
    assessment_number: int,
    complexity: str,
    username: str,
    image_files,
) -> dict:
    """
    Upload a question paper (as images) and extract questions using Claude AI.

    Returns:
        {'success': True, 'id': '<id>', 'version': <int>, 'questions': [...]}
        or {'success': False, 'error': '...'}
    """
    try:
        files = [
            ("images", (image_file.name, image_file.bytes, "application/octet-stream"))
            for image_file in image_files
        ]
        
        data = {
            "class_name": class_name,
            "subject": subject,
            "chapters": ",".join(chapters),
            "assessment_category": assessment_category,
            "assessment_number": str(assessment_number),
            "complexity": complexity,
            "username": username,
        }
        
        response = httpx.post(
            f"{API_BASE_URL}/api/ebooks/upload-questions",
            data=data,
            files=files,
            timeout=httpx.Timeout(300.0),  # OCR + question extraction may take longer
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)


def save_uploaded_questions(
    class_name: str,
    subject: str,
    chapters: list[str],
    assessment_category: str,
    assessment_number: int,
    complexity: str,
    paper_content: str,
    question_rows: list[dict],
    username: str,
) -> dict:
    """
    Convert already-scanned question paper text into structured questions
    (via Claude AI) mapped to the selected configuration, and save them.

    Returns:
        {'success': True, 'id': '<id>', 'version': <int>, 'questions': [...]}
        or {'success': False, 'error': '...'}
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/ebooks/save-uploaded-questions",
            json={
                "class_name": class_name,
                "subject": subject,
                "chapters": chapters,
                "assessmentCategory": assessment_category,
                "assessmentNumber": assessment_number,
                "complexity": complexity,
                "paperContent": paper_content,
                "questionRows": question_rows,
                "username": username,
            },
            timeout=httpx.Timeout(120.0),
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)


def get_question_versions(
    class_name: str,
    subject: str,
    chapters: str,
    assessment_category: str,
    assessment_number: int,
) -> list[int]:
    """Return every saved version number for this class/subject/chapters/assessment combo."""
    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/ebooks/question-versions",
            params={
                "class_name": class_name,
                "subject": subject,
                "chapters": chapters,
                "assessment_category": assessment_category,
                "assessment_number": assessment_number,
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("versions", [])
    except httpx.HTTPError:
        return []


def download_question_paper(
    class_name: str,
    subject: str,
    chapters: str,
    assessment_category: str,
    assessment_number: int,
    version: int,
) -> bytes:
    """
    Download a previously-generated or uploaded, saved version of a question paper as a
    formatted .docx file.

    Returns the raw .docx bytes on success. Raises RuntimeError on failure.
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/ebooks/generate-questions/document",
            params={
                "class_name": class_name,
                "subject": subject,
                "chapters": chapters,
                "assessment_category": assessment_category,
                "assessment_number": assessment_number,
                "version": version,
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.content
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except ValueError:
            detail = exc.response.text
        raise RuntimeError(detail or f"Download failed ({exc.response.status_code}).") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Cannot reach the API server at {API_BASE_URL}. ({exc})") from exc
