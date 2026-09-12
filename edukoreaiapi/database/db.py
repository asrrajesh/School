import re
import bcrypt
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from config.config import (
    MONGO_URI,
    DB_NAME,
    DB_CONNECTION_TIMEOUT,
    PASSWORD_MIN_LENGTH,
    EMAIL_PATTERN,
    MOBILE_PATTERN,
)

_client = None
_db = None


def get_db():
    """Return the database instance, creating the connection if needed."""
    global _client, _db
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=DB_CONNECTION_TIMEOUT)
        _db = _client[DB_NAME]
        # Ensure unique index on username
        _db.users.create_index("username", unique=True)
    return _db


def is_valid_email(value: str) -> bool:
    return bool(re.match(EMAIL_PATTERN, value))


def is_valid_mobile(value: str) -> bool:
    # Accept 10-15 digit numbers, optionally starting with +
    return bool(re.match(MOBILE_PATTERN, value))


def is_valid_username(value: str) -> bool:
    return is_valid_email(value) or is_valid_mobile(value)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (TypeError, ValueError):
        return False


def register_user(username: str, password: str) -> dict:
    """
    Register a new user.
    Returns {'success': True} or {'success': False, 'error': '<message>'}.
    """
    username = username.strip()
    if not is_valid_username(username):
        return {"success": False, "error": "Enter a valid email address or mobile number."}
    if len(password) < PASSWORD_MIN_LENGTH:
        return {"success": False, "error": f"Password must be at least {PASSWORD_MIN_LENGTH} characters."}

    try:
        db = get_db()
        db.users.insert_one({
            "username": username,
            "password": hash_password(password),
            "created_at": datetime.utcnow(),
        })
        return {"success": True}
    except DuplicateKeyError:
        return {"success": False, "error": "This email / mobile number is already registered."}
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def get_scanned_chapter(class_name: str, subject: str, chapter: str) -> dict | None:
    """Return the saved chapter content for the given class/subject/chapter, if any."""
    try:
        return get_db().scanned_chapters.find_one({
            "class": class_name,
            "subject": subject,
            "chapter": chapter,
        })
    except ConnectionFailure:
        return None
    except Exception:
        return None


def get_scanned_classes() -> list[str]:
    """Return distinct classes that have chapters previously scanned via Setup E-Books."""
    try:
        return sorted(get_db().scanned_chapters.distinct("class"))
    except ConnectionFailure:
        return []
    except Exception:
        return []


def get_scanned_subjects(class_name: str) -> list[str]:
    """Return distinct subjects scanned for the given class."""
    try:
        return sorted(get_db().scanned_chapters.distinct("subject", {"class": class_name}))
    except ConnectionFailure:
        return []
    except Exception:
        return []


def get_scanned_chapters(class_name: str, subject: str) -> list[str]:
    """Return distinct chapters scanned for the given class/subject."""
    try:
        return sorted(get_db().scanned_chapters.distinct("chapter", {"class": class_name, "subject": subject}))
    except ConnectionFailure:
        return []
    except Exception:
        return []


def save_scanned_chapter(class_name: str, subject: str, chapter: str, content: str, username: str) -> dict:
    """Create or update the chapter text and its metadata for a class/subject/chapter."""
    try:
        result = get_db().scanned_chapters.update_one(
            {"class": class_name, "subject": subject, "chapter": chapter},
            {
                "$set": {
                    "content": content,
                    "updated_by": username,
                    "updated_at": datetime.utcnow(),
                },
                "$setOnInsert": {
                    "class": class_name,
                    "subject": subject,
                    "chapter": chapter,
                    "created_by": username,
                    "created_at": datetime.utcnow(),
                },
            },
            upsert=True,
        )
        return {"success": True, "id": str(result.upserted_id) if result.upserted_id else None}
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def login_user(username: str, password: str) -> dict:
    """
    Authenticate a user.
    Returns {'success': True, 'user': {...}} or {'success': False, 'error': '<message>'}.
    """
    username = username.strip()
    try:
        db = get_db()
        user = db.users.find_one({"username": username})
        if user is None:
            return {"success": False, "error": "Account not found. Please sign up."}
        if not check_password(password, user["password"]):
            return {"success": False, "error": "Incorrect password. Please try again."}
        return {"success": True, "user": {"username": user["username"]}}
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def request_password_reset(username: str) -> dict:
    """
    Check if the user exists (stub for real reset logic).
    Returns {'success': True} or {'success': False, 'error': '<message>'}.
    """
    username = username.strip()
    if not is_valid_username(username):
        return {"success": False, "error": "Enter a valid email address or mobile number."}
    try:
        db = get_db()
        user = db.users.find_one({"username": username})
        if user is None:
            return {"success": False, "error": "No account found with that email / mobile number."}
        # In a real app, send reset link/OTP here.
        return {"success": True}
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def save_generated_questions(
    class_name: str,
    subject: str,
    chapter: str,
    assessment_category: str,
    assessment_number: int,
    questions: list[dict],
    question_configuration: list[dict],
    username: str,
) -> dict:
    """
    Save AI-generated questions to the 'questions' collection.
    Each question_configuration row becomes an order entry tracking the configuration.

    Args:
        class_name: Class name
        subject: Subject
        chapter: Chapter name
        assessment_category: "fa" (Formative) or "sa" (Summative)
        assessment_number: 1 or 2
        questions: List of generated question dicts
        question_configuration: List of dicts with questionType, questionCount, marksPerQuestion
        username: Username of the user who generated them

    Returns:
        {'success': True, 'id': '<document_id>'} or {'success': False, 'error': '<message>'}
    """
    try:
        db = get_db()
        document = {
            "class": class_name,
            "subject": subject,
            "chapter": chapter,
            "assessmentCategory": assessment_category,
            "assessmentNumber": assessment_number,
            "questions": questions,
            "configuration": question_configuration,
            "generated_by": username,
            "generated_at": datetime.utcnow(),
        }
        result = db.questions.insert_one(document)
        return {"success": True, "id": str(result.inserted_id)}
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def get_generated_questions(
    class_name: str,
    subject: str,
    chapter: str,
    assessment_category: str,
    assessment_number: int,
) -> dict | None:
    """Retrieve generated questions for a class/subject/chapter/assessment."""
    try:
        return get_db().questions.find_one({
            "class": class_name,
            "subject": subject,
            "chapter": chapter,
            "assessmentCategory": assessment_category,
            "assessmentNumber": assessment_number,
        })
    except ConnectionFailure:
        return None
    except Exception:
        return None