# Add these functions to edukoreaiapi/database/db.py

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