# Enhanced Generate Questions Feature - Implementation Guide

## Overview

This guide provides step-by-step instructions to implement the enhanced Generate Questions feature with the following improvements:

1. **Dropdown Selectors** for Class, Subject, Assessment Category, Assessment Number, Complexity
2. **MultiSelect for Chapters** (select multiple chapters at once)
3. **Downloads Dropdown** positioned next to Complexity
4. **Tab View Control** with two tabs:
   - **Generate Questions**: Existing question generation logic
   - **Upload Questions**: New feature to upload question papers and extract questions
5. **Both tabs can independently save** questions to MongoDB

---

## Files to Update/Create

### Backend (edukoreaiapi)

1. **`routers/ebooks.py`** - REPLACE with `ebooks_enhanced.py`
2. **`schemas.py`** - REPLACE with `schemas_enhanced.py`
3. **`services/claude_questions.py`** - REPLACE with `claude_questions_enhanced.py`
4. **`database/db.py`** - ADD the functions from `db_enhancements.py`

### Frontend (edukoreaiui)

1. **`screens/generate_questions_screen.py`** - REPLACE with `generate_questions_screen_enhanced.py`
2. **`services/api_client.py`** - REPLACE with `api_client_enhanced.py`

---

## Step-by-Step Implementation

### Step 1: Backend Database Updates

**File: `edukoreaiapi/database/db.py`**

Add these functions at the end of the file:

```python
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
    """Retrieve a generated-questions document."""
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
```

### Step 2: Update Schemas

**File: `edukoreaiapi/schemas.py`**

Replace the entire file with the content from `schemas_enhanced.py`.

**Key Changes:**
- `chapters: list[str]` instead of single chapter
- Assessment category and number are now request fields

### Step 3: Update Claude Questions Service

**File: `edukoreaiapi/services/claude_questions.py`**

Replace the entire file with `claude_questions_enhanced.py`.

**New Function Added:**
- `extract_questions_from_paper(paper_text, complexity)` - Extracts questions from uploaded paper text

### Step 4: Update Ebooks Router

**File: `edukoreaiapi/routers/ebooks.py`**

Replace the entire file with `ebooks_enhanced.py`.

**New Endpoint Added:**
- `POST /api/ebooks/upload-questions` - Upload and extract questions from paper images

**Modified Endpoints:**
- `POST /api/ebooks/generate-questions` - Now accepts list of chapters
- `GET /api/ebooks/question-versions` - Now accepts chapters as comma-separated string
- `GET /api/ebooks/generate-questions/document` - Now accepts chapters as comma-separated string

### Step 5: Update API Client

**File: `edukoreaiui/services/api_client.py`**

Replace the entire file with `api_client_enhanced.py`.

**New Function Added:**
- `upload_questions(class_name, subject, chapters, assessment_category, assessment_number, complexity, username, image_files)` - Upload and extract questions

**Modified Functions:**
- `generate_questions()` - Now accepts `chapters: list[str]`
- `get_question_versions()` - Now accepts `chapters: str` (comma-separated)
- `download_question_paper()` - Now accepts `chapters: str` (comma-separated)

### Step 6: Update Frontend Screen

**File: `edukoreaiui/screens/generate_questions_screen.py`**

Replace the entire file with `generate_questions_screen_enhanced.py`.

**Key Changes:**
- All dropdowns converted to `ft.Dropdown` (Class, Subject, Assessment Category, Assessment Number, Complexity, Downloads)
- Chapters converted to `ft.MultiSelect`
- Downloads dropdown positioned next to Complexity
- Tab view with two tabs: "Generate Questions" and "Upload Questions"
- Each tab has independent functionality but both save to MongoDB

---

## Feature Details

### Tab 1: Generate Questions

**Layout:**
- Question Configuration table (Question Type, Count, Marks, Total, Add, Delete)
- GENERATE QUESTIONS button

**Functionality:**
- Same as before, but now supports multiple chapters
- Auto-increments version for each class/subject/chapters/assessment combination
- Saves to MongoDB with `source: "generated"`

### Tab 2: Upload Questions

**Layout:**
- Attach Images button + label
- SCAN button
- Question paper content text field
- SUBMIT button

**Functionality:**
- Upload images of question paper
- Claude extracts text from images
- Claude analyzes extracted text to identify and extract questions
- Saves extracted questions to MongoDB with `source: "uploaded"`
- Uses same versioning logic as "Generate Questions"

### Common Features

**Selectors:**
- **Class**: Standard dropdown (populated from scanned chapters)
- **Subject**: Standard dropdown (populated based on selected class)
- **Chapters**: MultiSelect (can select multiple chapters, comma-separated in API calls)
- **Assessment Category**: Standard dropdown (FA/SA)
- **Assessment Number**: Standard dropdown (1/2)
- **Complexity**: Standard dropdown (Basic/Intermediate/Advanced)
- **Downloads**: Standard dropdown (populated with saved versions for the selection)

**Downloads Feature:**
- Shows all saved versions for the current class/subject/chapters/assessment combination
- Click on a version to download as formatted .docx
- Disabled until all required selectors are filled

---

## MongoDB Schema Changes

### Updated `questions` Collection Schema

```json
{
  "_id": ObjectId,
  "class": "Class 10",
  "subject": "Physics",
  "chapters": ["Electricity", "Magnetism"],  // Now an array
  "assessmentCategory": "fa",
  "assessmentNumber": 1,
  "version": 2,
  "complexity": "intermediate",
  "questions": [
    {
      "type": "mcq",
      "marks": 1,
      "question": "What is...",
      "options": ["A", "B", "C", "D"],
      "correctOption": "A",
      "answerKey": "..."
    },
    ...
  ],
  "configuration": [
    {
      "questionType": "mcq",
      "questionCount": 2,
      "marksPerQuestion": 1
    },
    ...
  ],
  "source": "generated",  // or "uploaded"
  "sourceContent": "...",  // Only for uploaded
  "generated_by": "user@email.com",
  "generated_at": ISODate()
}
```

---

## API Endpoint Changes

### POST /api/ebooks/generate-questions

**Request:**
```json
{
  "class_name": "Class 10",
  "subject": "Physics",
  "chapters": ["Electricity", "Magnetism"],
  "assessmentCategory": "fa",
  "assessmentNumber": 1,
  "complexity": "intermediate",
  "questionRows": [
    {
      "questionType": "mcq",
      "questionCount": 2,
      "marksPerQuestion": 1
    }
  ],
  "username": "user@email.com"
}
```

**Response:**
```json
{
  "success": true,
  "id": "507f1f77bcf86cd799439011",
  "version": 2,
  "questions": [...],
  "message": "Generated 4 questions successfully (Version 2)."
}
```

### POST /api/ebooks/upload-questions

**Request:** (multipart/form-data)
```
class_name: "Class 10"
subject: "Physics"
chapters: "Electricity,Magnetism"
assessment_category: "fa"
assessment_number: "1"
complexity: "intermediate"
username: "user@email.com"
images: [file1.jpg, file2.jpg, ...]
```

**Response:**
```json
{
  "success": true,
  "id": "507f1f77bcf86cd799439012",
  "version": 3,
  "questions": [...],
  "message": "Uploaded and extracted 5 questions successfully (Version 3)."
}
```

### GET /api/ebooks/question-versions

**Query Parameters:**
```
class_name=Class 10
subject=Physics
chapters=Electricity,Magnetism
assessment_category=fa
assessment_number=1
```

**Response:**
```json
{
  "versions": [1, 2, 3]
}
```

### GET /api/ebooks/generate-questions/document

**Query Parameters:**
```
class_name=Class 10
subject=Physics
chapters=Electricity,Magnetism
assessment_category=fa
assessment_number=1
version=2
```

**Response:**
Binary .docx file

---

## Testing Checklist

- [ ] Class dropdown populates from database
- [ ] Subject dropdown populates based on selected class
- [ ] Chapter multiselect populates based on selected subject
- [ ] Assessment category and number dropdowns work
- [ ] Complexity dropdown works
- [ ] Downloads dropdown appears only when all required fields selected
- [ ] Generate Questions tab:
  - [ ] Add/Delete buttons work for question rows
  - [ ] Total calculation works
  - [ ] Generate button calls API
  - [ ] Success/error messages display
  - [ ] Downloads populate after generation
- [ ] Upload Questions tab:
  - [ ] Attach images button works
  - [ ] Scan button extracts text from images
  - [ ] Submit button calls API
  - [ ] Success/error messages display
  - [ ] Downloads populate after upload
- [ ] Download functionality works
- [ ] MongoDB documents have correct schema
- [ ] Version numbering increments correctly

---

## Troubleshooting

### Issue: Chapters not showing in MultiSelect

**Solution:** Ensure chapters are scanned first via Setup E-Books

### Issue: Upload fails with "Could not extract text"

**Solution:** Ensure image quality is good, try scanning with better lighting

### Issue: API returns "chapters not found"

**Solution:** Check MongoDB has the chapters in scanned_chapters collection

### Issue: Downloads dropdown doesn't populate

**Solution:** Ensure all required fields are selected, check MongoDB for saved versions

---

## Performance Considerations

- **MultiSelect chapters**: Each additional chapter adds ~100-200ms to API response
- **Upload processing**: Typically 15-30 seconds depending on paper complexity and image count
- **Generation processing**: Same as before (10-30 seconds typical)

---

## Security Notes

- API credentials (ANTHROPIC_API_KEY) still protected via environment variables
- No changes to authentication/authorization
- Uploaded images processed server-side only
- Question extraction uses same Claude API as generation

---

## Version Numbering

The versioning system auto-increments based on class/subject/chapters/assessment combination:

- Class 10, Physics, [Electricity], FA 1 → versions 1, 2, 3...
- Class 10, Physics, [Electricity, Magnetism], FA 1 → separate versioning (versions 1, 2, 3...)
- Class 10, Physics, [Electricity], SA 1 → separate versioning

This allows independent question tracking for each unique combination.

---

## Next Steps

After implementation:

1. Test basic workflows (Generate and Upload)
2. Test multi-chapter scenarios
3. Test downloads with multiple chapters
4. Gather user feedback on UI/UX
5. Monitor API usage and performance
6. Consider adding question editing/review before submission

---

## Support

For issues or questions:
1. Check the Testing Checklist
2. Review troubleshooting section
3. Check MongoDB schema matches
4. Verify API endpoints are correctly updated
5. Check browser/application logs for errors
