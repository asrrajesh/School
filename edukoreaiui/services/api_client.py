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
    response = httpx.post(f"{API_BASE_URL}/api/ebooks/scan", files=files, timeout=_TIMEOUT)
    response.raise_for_status()
    result = response.json()
    if not result.get("success"):
        raise RuntimeError(result.get("error", "Scan failed."))
    return result["content"]


def generate_questions(
    class_name: str,
    subject: str,
    chapter: str,
    question_rows: list[dict],
    username: str,
) -> dict:
    """
    Generate questions using Claude AI based on chapter content and configuration.

    Args:
        class_name: Class name
        subject: Subject
        chapter: Chapter name
        question_rows: List of dicts with questionType, questionCount, marksPerQuestion
        username: Current user's username

    Returns:
        {'success': True, 'id': '<id>', 'questions': [...]} or {'success': False, 'error': '...'}
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/ebooks/generate-questions",
            json={
                "class_name": class_name,
                "subject": subject,
                "chapter": chapter,
                "questionRows": question_rows,
                "username": username,
            },
            timeout=httpx.Timeout(120.0),  # Question generation may take longer
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return _connection_error(exc)
