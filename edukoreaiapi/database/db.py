import re
import uuid
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
        # Partial unique indexes (only enforce when field exists)
        _db.users.create_index(
            "email",
            unique=True,
            partialFilterExpression={"email": {"$exists": True}}
        )
        _db.users.create_index(
            "mobile",
            unique=True,
            partialFilterExpression={"mobile": {"$exists": True}}
        )
        # Unique index on google_id (only enforce when field exists)
        _db.users.create_index(
            "google_id",
            unique=True,
            partialFilterExpression={"google_id": {"$exists": True}}
        )
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
    Register a new user with email or mobile.
    Returns {'success': True} or {'success': False, 'error': '<message>'}.
    """
    username = username.strip()
    if not is_valid_username(username):
        return {"success": False, "error": "Enter a valid email address or mobile number."}
    if len(password) < PASSWORD_MIN_LENGTH:
        return {"success": False, "error": f"Password must be at least {PASSWORD_MIN_LENGTH} characters."}

    try:
        db = get_db()
        user_doc = {
            "_id": str(uuid.uuid4()),
            "password": hash_password(password),
            "created_at": datetime.utcnow(),
        }

        # Determine if it's email or mobile
        if is_valid_email(username):
            user_doc["email"] = username
        else:
            user_doc["mobile"] = username

        db.users.insert_one(user_doc)
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
    Authenticate a user by email or mobile.
    Returns {'success': True, 'user': {...}} or {'success': False, 'error': '<message>'}.
    """
    username = username.strip()
    try:
        db = get_db()
        # Search by email or mobile
        if is_valid_email(username):
            user = db.users.find_one({"email": username})
        else:
            user = db.users.find_one({"mobile": username})

        if user is None:
            return {"success": False, "error": "Account not found. Please sign up."}
        if not check_password(password, user["password"]):
            return {"success": False, "error": "Incorrect password. Please try again."}
        return {"success": True, "user": {"_id": user["_id"], "email": user.get("email"), "mobile": user.get("mobile")}}
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def get_user_by_id(user_id: str) -> dict:
    """
    Look up a user by their _id.
    Returns {'success': True, 'user': {...}} or {'success': False, 'error': '<message>'}.
    """
    try:
        db = get_db()
        user = db.users.find_one({"_id": user_id})
        if user is None:
            return {"success": False, "error": "User not found."}
        return {
            "success": True,
            "user": {
                "_id": user["_id"],
                "email": user.get("email"),
                "mobile": user.get("mobile"),
                "name": user.get("name"),
            },
        }
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def request_password_reset(username: str) -> dict:
    """
    Check if the user exists by email or mobile (stub for real reset logic).
    Returns {'success': True} or {'success': False, 'error': '<message>'}.
    """
    username = username.strip()
    if not is_valid_username(username):
        return {"success": False, "error": "Enter a valid email address or mobile number."}
    try:
        db = get_db()
        # Search by email or mobile
        if is_valid_email(username):
            user = db.users.find_one({"email": username})
        else:
            user = db.users.find_one({"mobile": username})

        if user is None:
            return {"success": False, "error": "No account found with that email / mobile number."}
        # In a real app, send reset link/OTP here.
        return {"success": True}
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def get_next_question_version(
    class_name: str,
    subject: str,
    chapters: list[str],
    assessment_category: str,
    assessment_number: int,
) -> int:
    """Return the version number the next generated-questions document should use."""
    try:
        chapters_query = {"$in": chapters} if chapters else {}
        pipeline = [
            {
                "$match": {
                    "class": class_name,
                    "subject": subject,
                    "chapters": chapters_query if chapters else {"$exists": True},
                    "assessmentCategory": assessment_category,
                    "assessmentNumber": assessment_number,
                }
            },
            {"$group": {"_id": None, "maxVersion": {"$max": "$version"}}},
        ]
        result = list(get_db().questions.aggregate(pipeline))
        max_version = result[0]["maxVersion"] if result else None
        return (max_version or 0) + 1
    except ConnectionFailure:
        return 1
    except Exception:
        return 1


def get_question_versions(
    class_name: str,
    subject: str,
    chapters: list[str],
    assessment_category: str,
    assessment_number: int,
) -> list[int]:
    """Return every saved version number for this combo, ascending (Version 1 first)."""
    try:
        versions = get_db().questions.distinct(
            "version",
            {
                "class": class_name,
                "subject": subject,
                "chapters": {"$in": chapters},
                "assessmentCategory": assessment_category,
                "assessmentNumber": assessment_number,
            },
        )
        return sorted(v for v in versions if isinstance(v, int))
    except ConnectionFailure:
        return []
    except Exception:
        return []


def save_generated_questions(
    class_name: str,
    subject: str,
    chapters: list[str],
    assessment_category: str,
    assessment_number: int,
    complexity: str,
    questions: list[dict],
    question_configuration: list[dict],
    username: str,
    source: str = "generated",
    source_content: str = "",
) -> dict:
    """
    Save AI-generated or extracted questions to the 'questions' collection,
    auto-assigning the next version number for this class/subject/chapters/assessment combo.

    Args:
        class_name: e.g., "Class 10"
        subject: e.g., "Physics"
        chapters: List of chapter names
        assessment_category: "fa" or "sa"
        assessment_number: 1 or 2
        complexity: "basic", "intermediate", or "advanced"
        questions: List of question dicts
        question_configuration: List of configuration rows (empty for uploaded)
        username: Current user
        source: "generated" or "uploaded"
        source_content: Original paper text (for uploaded only)

    Returns:
        {'success': True, 'id': '<document_id>', 'version': <int>}
        or {'success': False, 'error': '<message>'}
    """
    try:
        db = get_db()
        version = get_next_question_version(
            class_name, subject, chapters, assessment_category, assessment_number
        )
        document = {
            "class": class_name,
            "subject": subject,
            "chapters": chapters,
            "assessmentCategory": assessment_category,
            "assessmentNumber": assessment_number,
            "version": version,
            "complexity": complexity,
            "questions": questions,
            "configuration": question_configuration,
            "source": source,
            "generated_by": username,
            "generated_at": datetime.utcnow(),
        }
        
        # Add source content if uploaded
        if source == "uploaded" and source_content:
            document["sourceContent"] = source_content

        result = db.questions.insert_one(document)
        return {"success": True, "id": str(result.inserted_id), "version": version}
    except ConnectionFailure:
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def get_generated_questions(
    class_name: str,
    subject: str,
    chapters: list[str],
    assessment_category: str,
    assessment_number: int,
    version: int | None = None,
) -> dict | None:
    """Retrieve a generated-questions document. Pass `version` for a specific
    version, or omit it to get the latest one for this combo."""
    try:
        query = {
            "class": class_name,
            "subject": subject,
            "chapters": {"$in": chapters},
            "assessmentCategory": assessment_category,
            "assessmentNumber": assessment_number,
        }
        if version is not None:
            query["version"] = version
            return get_db().questions.find_one(query)
        return get_db().questions.find_one(query, sort=[("version", -1)])
    except ConnectionFailure:
        return None
    except Exception:
        return None


def login_or_create_google_user(google_id: str, email: str, name: str) -> dict:
    """
    Handle Google OAuth login: return existing user or create new one.
    If Google ID already linked, return user.
    If email matches existing user, link Google ID to that user.
    Otherwise create new user with Google ID.

    Returns {'success': True, 'user': {...}} or {'success': False, 'error': '<message>'}.
    """
    try:
        db = get_db()

        # Check if Google ID already linked
        user = db.users.find_one({"google_id": google_id})
        if user:
            return {"success": True, "user": {"_id": user["_id"], "email": user.get("email")}}

        # Check if email exists (link Google ID to existing user)
        if email:
            user = db.users.find_one({"email": email})
            if user:
                # Link Google ID to existing user
                db.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "google_id": google_id,
                            "auth_method": "google",  # Mark as Google-authenticated
                            "linked_at": datetime.utcnow(),
                        }
                    }
                )
                return {"success": True, "user": {"_id": user["_id"], "email": email}}

        # Create new user with Google ID
        user_doc = {
            "_id": str(uuid.uuid4()),
            "google_id": google_id,
            "email": email,
            "auth_method": "google",
            "linked_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        db.users.insert_one(user_doc)
        return {"success": True, "user": {"_id": user_doc["_id"], "email": email}}
    except ConnectionFailure:
        import sys
        print(f"[DEBUG] Connection failure in login_or_create_google_user", file=sys.stderr)
        return {"success": False, "error": "Cannot connect to database. Please try again."}
    except Exception as exc:
        import sys
        import traceback
        print(f"[DEBUG] Error in login_or_create_google_user: {exc}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return {"success": False, "error": str(exc)}