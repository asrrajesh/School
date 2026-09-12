# AI Question Generation Implementation Summary

## Overview
This implementation adds AI-powered question generation to the EduKoreAI platform. When users configure questions via the "Generate Questions" screen and click the button, the system now:

1. **Fetches** the chapter content from MongoDB
2. **Generates** questions using Claude AI based on the configured types/counts/marks
3. **Saves** the generated questions to a new MongoDB collection
4. **Returns** the questions to the user with success confirmation

---

## Architecture & Data Flow

```
USER INTERFACE (edukoreaiui)
    ↓
[Generate Questions Screen] ← User configures questions
    ↓ [GENERATE QUESTIONS button clicked]
    ↓ Gets current username from session
    ↓ Validates configuration
    ↓ Shows loading indicator
    ↓
API CLIENT (services/api_client.py)
    ↓ generate_questions() [HTTP POST]
    ↓
BACKEND API (edukoreaiapi)
    ↓
[POST /api/ebooks/generate-questions]
    ↓
Question Generation Service (services/claude_questions.py)
    ├→ Fetch chapter content from DB
    ├→ Build prompt with configuration requirements
    ├→ Call Claude AI (via Anthropic SDK)
    ├→ Parse JSON response
    └→ Return structured questions
    ↓
Database (database/db.py)
    ├→ save_generated_questions() - Insert to "questions" collection
    └→ Returns document ID
    ↓
RESPONSE (JSON with generated questions)
    ↓
USER INTERFACE
    └→ Display success message with question count
```

---

## Backend Changes

### 1. New Service: `edukoreaiapi/services/claude_questions.py`
**Purpose:** Generate questions using Claude AI

**Key Function:** `generate_questions_from_chapter(chapter_content, question_rows)`
- Accepts chapter text and question configuration
- Builds a detailed prompt with specific requirements (MCQ, short-answer, long-answer)
- Calls Claude API with proper error handling
- Returns parsed list of questions with:
  - `type`: "mcq", "short", or "long"
  - `marks`: marks per question
  - `question`: question text
  - `options`: [A, B, C, D] for MCQ only
  - `correctOption`: for MCQ only
  - `answerKey`: answer or explanation

**Features:**
- Type-specific question generation (MCQ with options, short/long answers with keys)
- Proper error handling for API authentication, permissions, and connectivity
- JSON response validation

### 2. Database Functions: `edukoreaiapi/database/db.py` (NEW)
Added two new functions:

```python
save_generated_questions(class_name, subject, chapter, questions, 
                         question_configuration, username)
# Saves to MongoDB "questions" collection
# Returns: {'success': True, 'id': '<document_id>'}

get_generated_questions(class_name, subject, chapter)
# Retrieves questions for a class/subject/chapter
# Returns: Document dict or None
```

**MongoDB Collection: "questions"**
```json
{
  "_id": ObjectId,
  "class": "Class Name",
  "subject": "Subject",
  "chapter": "Chapter Name",
  "questions": [
    {
      "type": "mcq",
      "marks": 1,
      "question": "Which is...?",
      "options": ["A", "B", "C", "D"],
      "correctOption": "A",
      "answerKey": "The answer is A because..."
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
  "generated_by": "username",
  "generated_at": "2026-09-09T10:30:00"
}
```

### 3. API Schemas: `edukoreaiapi/schemas.py` (UPDATED)
Added new request/response models:

```python
class QuestionRowConfig(BaseModel):
    questionType: str      # "mcq", "short", "long"
    questionCount: int
    marksPerQuestion: float

class GenerateQuestionsRequest(BaseModel):
    class_name: str
    subject: str
    chapter: str
    questionRows: list[QuestionRowConfig]
    username: str
```

### 4. API Endpoint: `edukoreaiapi/routers/ebooks.py` (UPDATED)

**New Endpoint:** `POST /api/ebooks/generate-questions`

```python
@router.post("/generate-questions")
def generate_questions(payload: GenerateQuestionsRequest):
    # 1. Fetch chapter content from DB
    # 2. Generate questions using Claude
    # 3. Save to "questions" collection
    # 4. Return success + questions
```

**Request Body:**
```json
{
  "class_name": "Class 10",
  "subject": "Physics",
  "chapter": "Electricity",
  "questionRows": [
    {
      "questionType": "mcq",
      "questionCount": 2,
      "marksPerQuestion": 1
    },
    {
      "questionType": "short",
      "questionCount": 2,
      "marksPerQuestion": 2
    }
  ],
  "username": "user@example.com"
}
```

**Response (Success):**
```json
{
  "success": true,
  "id": "507f1f77bcf86cd799439011",
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
  "message": "Generated 4 questions successfully."
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Chapter content not found for Electricity. Please scan the e-book first."
}
```

---

## Frontend Changes

### 1. UI Screen: `edukoreaiui/screens/generate_questions_screen.py` (UPDATED)

#### Table Layout (from previous task)
The question configuration rows are now displayed in a clean single-row table:
- **Column 1:** Question Type (dropdown)
- **Column 2:** Question Count (number input)
- **Column 3:** Marks Per Question (decimal input)
- **Column 4:** Total (calculated display)
- **Column 5:** Add (icon button)
- **Column 6:** Delete (icon button)

#### Generate Questions Button (NEW ASYNC HANDLER)
Previously: Just printed configuration to console
Now: Performs full question generation workflow

**New Async Function: `generate_questions_async(e)`**
1. **Validation**
   - Checks class/subject/chapter selection
   - Checks at least one question row exists
   - Validates each row (type, count, marks)

2. **UI Feedback**
   - Disables button
   - Shows loading indicator (spinning circle + "Generating...")
   - Updates page

3. **API Call**
   - Gets current user from `page.session.store.get("current_user")`
   - Builds question rows array from table
   - Calls `api_generate_questions()` (30s timeout extended to 120s)

4. **Response Handling**
   - Success: Shows green message with question count
   - Error: Shows red message with error details
   - Always: Re-enables button, restores original text

### 2. API Client: `edukoreaiui/services/api_client.py` (UPDATED)

**New Function: `generate_questions(class_name, subject, chapter, question_rows, username)`**
- Sends POST request to `/api/ebooks/generate-questions`
- Uses 120-second timeout (generation can take time)
- Returns full response dict with questions
- Includes connection error handling

```python
def generate_questions(class_name, subject, chapter, question_rows, username):
    # Makes HTTP POST to backend
    # Returns: {'success': True, 'id': '...', 'questions': [...]}
    #       or: {'success': False, 'error': '...'}
```

---

## Configuration & Environment

**Required .env Variables (already present):**
```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
MONGO_URI=mongodb://localhost:27017/
DB_NAME=MySchool
```

**Database Collections Used:**
- `scanned_chapters` (existing - source of chapter content)
- `questions` (new - destination for generated questions)
- `users` (existing - for user tracking)

---

## User Experience Flow

### Step 1: Navigate to "Generate Questions"
- Select from drawer menu → Academics → Generate Questions

### Step 2: Configure Questions
- **Select Class** → Choose from available scanned classes
- **Select Subject** → Choose from available subjects in that class
- **Select Chapter** → Choose from available chapters in that subject
- Question configuration table appears

### Step 3: Configure Question Types
For each row:
1. **Question Type** → Select from dropdown
   - Choose the correct answer (MCQ)
   - Answer the following questions (Short)
   - Answer the following questions (Long)

2. **Question Count** → Enter number (e.g., 2)

3. **Marks Per Question** → Enter marks (e.g., 1.5)

4. **Total** → Auto-calculated (count × marks)

Add/remove rows as needed using the Add/Delete buttons

### Step 4: Generate
- Click **GENERATE QUESTIONS** button
- See loading spinner
- On success:
  - Green message: "✓ Generated 4 questions successfully!"
  - Questions saved to database

### Step 5: Use Generated Questions
- Questions are stored in MongoDB "questions" collection
- Can be retrieved/edited in future features

---

## Error Handling

### Validation Errors
- "Select class, subject, and chapter."
- "Add at least one question row."
- "Select a question type for every row."
- "Question count must be a positive whole number."
- "Marks per question must be a positive number."

### API Errors
- "Chapter content not found for [Chapter]. Please scan the e-book first."
- "Claude denied the API key..." (ANTHROPIC_API_KEY invalid)
- "Claude denied access to the configured model..." (ANTHROPIC_MODEL permissions)
- "Could not reach Claude..." (Network error)
- "Claude request failed (429): ..." (Rate limit or other API error)

### Database Errors
- "Cannot connect to database. Please try again." (MongoDB connection)
- JSON parsing errors from Claude response

---

## Testing Checklist

### Backend Testing
- [ ] Verify MongoDB "questions" collection is created
- [ ] Test with valid chapter content
- [ ] Test with different question configurations
- [ ] Verify JSON parsing of Claude response
- [ ] Test error handling (invalid API key, network issues)
- [ ] Check database insertion with proper metadata

### Frontend Testing
- [ ] Configure questions and click "GENERATE QUESTIONS"
- [ ] Verify loading indicator appears
- [ ] Verify success message appears with correct count
- [ ] Verify button returns to normal after completion
- [ ] Test error scenarios (invalid config, missing chapter)
- [ ] Verify questions are saved (query MongoDB)

### Integration Testing
- [ ] Generate questions multiple times for same chapter
- [ ] Generate questions for different chapters
- [ ] Verify user metadata is stored
- [ ] Check that timestamps are recorded

---

## Implementation Notes

### Claude Prompting Strategy
- Specifies exact requirements per question type
- Lists specific question requirements (count, marks, format)
- Provides JSON schema for response
- Includes guidelines for quality
- Requests only JSON (no extra text)

### Performance Considerations
- Question generation can take 10-30 seconds (Claude processing)
- Frontend timeout extended to 120 seconds to allow for this
- Loading indicator keeps user informed
- Button disabled during processing prevents double-clicks

### Security & Data Integrity
- Username tracked for audit trail
- Timestamps recorded for all generations
- Configuration saved alongside questions for reference
- Questions stored in separate collection from chapter content

---

## Files Modified/Created

### Created
- `edukoreaiapi/services/claude_questions.py` - Question generation service

### Modified
- `edukoreaiapi/database/db.py` - Added save_generated_questions, get_generated_questions
- `edukoreaiapi/schemas.py` - Added QuestionRowConfig, GenerateQuestionsRequest
- `edukoreaiapi/routers/ebooks.py` - Added /api/ebooks/generate-questions endpoint
- `edukoreaiui/services/api_client.py` - Added generate_questions function
- `edukoreaiui/screens/generate_questions_screen.py` - Updated button handler to async, integrated API call

### Unchanged (Already Integrated)
- Claude API integration (existing via `claude_ocr.py`)
- MongoDB integration (existing via `db.py`)
- FastAPI setup (existing)
- Flet UI framework (existing)

---

## Next Steps (Future Enhancements)

1. **Question Review & Editing**
   - UI to view/edit generated questions before saving
   - Option to regenerate specific questions

2. **Question Export**
   - Export to PDF, DOCX, or other formats
   - Print-friendly layout

3. **Analytics**
   - Track question generation history
   - Monitor which question types work best

4. **Customization**
   - User-defined question templates
   - Custom answer key formats

5. **Batch Generation**
   - Generate questions for multiple chapters at once
   - Schedule automatic generation

---

## Troubleshooting

### "Chapter content not found"
- Make sure to scan the e-book first via "Setup E-Books"
- Verify chapter is in MongoDB `scanned_chapters` collection

### "Claude denied the API key"
- Check `.env` file has valid `ANTHROPIC_API_KEY`
- Verify API key is active on Anthropic console

### Questions not appearing in response
- Check MongoDB connection
- Verify Anthropic API key and rate limits
- Check API logs for Claude errors

### Loading spinner never disappears
- Check browser console for errors
- Verify backend API is responding
- Check network tab for failed requests

---

## Configuration Reference

### Claude Model
Current: `claude-sonnet-4-5-20250929`
- Latest Claude Sonnet model
- Good balance of speed and quality
- Can handle complex prompting

### Timeout Settings
- API Client: 120 seconds (question generation)
- Previous calls: 30 seconds (faster operations)
- MongoDB: Default 5000ms

### Question Type Mappings
```
"mcq" → Multiple Choice (4 options, 1 correct)
"short" → Short Answer (1-2 sentence answer key)
"long" → Long Answer (3-5 sentence answer key)
```

---

## API Documentation

### POST /api/ebooks/generate-questions

**Purpose:** Generate questions using Claude AI

**Authentication:** None (currently)

**Request Headers:** Content-Type: application/json

**Request Body:**
```json
{
  "class_name": "Class 10",
  "subject": "Physics",
  "chapter": "Electricity",
  "questionRows": [
    {
      "questionType": "mcq",
      "questionCount": 2,
      "marksPerQuestion": 1
    },
    {
      "questionType": "short",
      "questionCount": 2,
      "marksPerQuestion": 2
    },
    {
      "questionType": "long",
      "questionCount": 1,
      "marksPerQuestion": 5
    }
  ],
  "username": "user@example.com"
}
```

**Response: 200 OK (Success)**
```json
{
  "success": true,
  "id": "507f1f77bcf86cd799439011",
  "questions": [
    {
      "type": "mcq",
      "marks": 1,
      "question": "What is electrical current?",
      "options": [
        "Flow of electrons",
        "Flow of protons",
        "Potential difference",
        "Resistance"
      ],
      "correctOption": "A",
      "answerKey": "The correct answer is A. Electrical current is the flow of electrons through a conductor."
    },
    {
      "type": "short",
      "marks": 2,
      "question": "Define resistance.",
      "answerKey": "Resistance is the opposition offered by a conductor to the flow of electric current. It is measured in ohms."
    },
    {
      "type": "long",
      "marks": 5,
      "question": "Explain Ohm's Law and its applications.",
      "answerKey": "Ohm's Law states that V = IR, where voltage is directly proportional to current and resistance. It applies to ohmic conductors at constant temperature. Applications include circuit analysis, determining safe operating ranges, and designing electrical devices. It forms the basis for understanding electrical networks."
    }
  ],
  "message": "Generated 5 questions successfully."
}
```

**Response: 400 Bad Request (Error)**
```json
{
  "success": false,
  "error": "Chapter content not found for Electricity. Please scan the e-book first."
}
```

---

## Summary

This implementation successfully adds AI-powered question generation to EduKoreAI, leveraging Claude's advanced capabilities to create diverse, well-formed questions across multiple types (MCQ, short-answer, long-answer) based on chapter content and user configuration. The system maintains data integrity, provides user feedback, and integrates seamlessly with the existing Flet UI and FastAPI backend.
