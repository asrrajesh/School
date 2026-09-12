# Quick Start: AI Question Generation Feature

## 🚀 What Was Added

The "Generate Questions" button in the Question Configuration screen now:
- ✅ Fetches chapter content from MongoDB
- ✅ Uses Claude AI to generate questions
- ✅ Saves questions to `questions` collection
- ✅ Provides real-time feedback to users

## 📋 Prerequisites Checklist

Before testing, ensure:
- [ ] Backend `.env` has `ANTHROPIC_API_KEY` set
- [ ] Backend `.env` has `ANTHROPIC_MODEL=claude-sonnet-4-5-20250929`
- [ ] MongoDB is running (`mongodb://localhost:27017/`)
- [ ] At least one chapter is scanned via "Setup E-Books"

## 🔧 Installation & Setup

### 1. Backend Dependencies
Already installed via `requirements.txt`:
- `anthropic>=0.18.0` - Claude API
- `pymongo>=4.0` - MongoDB
- `fastapi` - API framework
- `pydantic` - Request validation

### 2. Verify Installation
```bash
cd edukoreaiapi
source .venv/Scripts/activate
python -c "from services.claude_questions import generate_questions_from_chapter; print('OK')"
```

### 3. Start Services

**Terminal 1 - Backend API:**
```bash
cd edukoreaiapi
source .venv/Scripts/activate
python main.py
# Should output: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - MongoDB (if local):**
```bash
mongod
# Should output: waiting for connections on port 27017
```

**Terminal 3 - Frontend UI:**
```bash
cd edukoreaiui
source .venv/Scripts/activate
python main.py
# Should show: Flet server started on http://localhost:8550
```

## 📱 Using the Feature

### Step 1: Login
```
Username: any@email.com (or phone number)
Password: any password (8+ chars)
```

### Step 2: Navigate
```
Menu ☰ → Academics → Generate Questions
```

### Step 3: Select Chapter
```
Class: [Select]
Subject: [Select]
Chapter: [Select]  ← Must be pre-scanned via Setup E-Books
```

### Step 4: Configure Questions
```
Row 1: Question Type: MCQ, Count: 2, Marks: 1
       Total: 2 (auto-calculated)
       
[Click Add button to add more rows]

Row 2: Question Type: Short Answer, Count: 3, Marks: 2
       Total: 6 (auto-calculated)
       
[Click Add button to add more rows]

Row 3: Question Type: Long Answer, Count: 1, Marks: 5
       Total: 5 (auto-calculated)
```

### Step 5: Generate
```
[Click GENERATE QUESTIONS button]

⏳ Loading... (shows spinning circle + "Generating...")

✅ Success! "✓ Generated 6 questions successfully!"
```

### Step 6: Verify (MongoDB)
```bash
# In terminal, connect to MongoDB
mongosh
use MySchool
db.questions.find().pretty()

# Should see document with:
{
  "_id": ObjectId(...),
  "class": "Class 10",
  "subject": "Physics",
  "chapter": "Electricity",
  "questions": [ ... ],
  "configuration": [ ... ],
  "generated_by": "user@email.com",
  "generated_at": ISODate(...)
}
```

## 🛠️ Architecture Overview

```
User Interface (Flet)
    ↓
[Question Config Table] ← User fills in questions
    ↓ [GENERATE QUESTIONS click]
    ↓
api_client.generate_questions()
    ↓ [HTTP POST to backend]
    ↓
FastAPI Endpoint: POST /api/ebooks/generate-questions
    ↓
Backend Processing:
  1. Fetch chapter from db.scanned_chapters
  2. Build prompt with requirements
  3. Call Claude API (Anthropic SDK)
  4. Parse JSON response → Questions
  5. Save to db.questions collection
  6. Return success + questions
    ↓ [HTTP 200 + JSON]
    ↓
UI receives response
    ↓
Show success/error message
```

## 📁 Modified Files

### Backend (edukoreaiapi)
1. **NEW:** `services/claude_questions.py`
   - Generates questions using Claude AI
   - Handles all LLM interaction & error handling

2. **UPDATED:** `database/db.py`
   - Added: `save_generated_questions()`
   - Added: `get_generated_questions()`

3. **UPDATED:** `schemas.py`
   - Added: `QuestionRowConfig`
   - Added: `GenerateQuestionsRequest`

4. **UPDATED:** `routers/ebooks.py`
   - Added: `POST /api/ebooks/generate-questions` endpoint
   - Added imports for new service & DB functions

### Frontend (edukoreaiui)
1. **UPDATED:** `services/api_client.py`
   - Added: `generate_questions()` function
   - 120-second timeout for API call

2. **UPDATED:** `screens/generate_questions_screen.py`
   - Changed button handler to async
   - Shows loading indicator during generation
   - Calls API client function
   - Displays success/error messages

## ⚙️ Configuration

### Environment Variables (.env)
```
# Required - Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Database
MONGO_URI=mongodb://localhost:27017/
DB_NAME=MySchool

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

### Key Settings
- Question Generation Timeout: **120 seconds** (allows Claude to respond)
- Max Question Types: **3** (MCQ, Short, Long)
- Min Rows: **1**, Max Rows: **3**

## 🧪 Basic Test

```bash
# 1. Start backend & MongoDB
# 2. Create test chapter in MongoDB:

mongosh
use MySchool
db.scanned_chapters.insertOne({
  class: "Test Class",
  subject: "Test Subject", 
  chapter: "Test Chapter",
  content: "This is a test chapter about electricity. Electricity is the flow of electrons. There are various types of circuits..."
})

# 3. Login to UI with any credentials
# 4. Go to Generate Questions
# 5. Select Test Class, Test Subject, Test Chapter
# 6. Add one question row: MCQ, Count: 1, Marks: 1
# 7. Click GENERATE QUESTIONS
# 8. Wait for success message
# 9. Verify in MongoDB:

db.questions.find()
```

## ❌ Troubleshooting

### "Cannot reach the API server"
```
❌ Backend not running
✅ Start backend: python main.py
✅ Check port 8000 is open
```

### "Claude denied the API key"
```
❌ ANTHROPIC_API_KEY is invalid/not set
✅ Update .env with valid key from https://console.anthropic.com
✅ Restart backend
```

### "Chapter content not found"
```
❌ Chapter not scanned or doesn't exist
✅ Go to Setup E-Books and scan the chapter
✅ Verify in MongoDB: db.scanned_chapters.find()
```

### "Loading spinner never stops"
```
❌ API taking too long or backend error
✅ Check backend logs for errors
✅ Verify ANTHROPIC_API_KEY is valid
✅ Check internet connection
```

### "Questions not saving to database"
```
❌ MongoDB not running
✅ Start MongoDB: mongod
✅ Verify connection: mongosh
```

## 🚀 Production Checklist

- [ ] API key secured in environment
- [ ] MongoDB credentials set correctly
- [ ] API timeout appropriate for your network
- [ ] Error messages clear to users
- [ ] Logging enabled for debugging
- [ ] Database backups configured
- [ ] Rate limiting considered for Claude API
- [ ] CORS settings configured if needed
- [ ] SSL/HTTPS enabled for production
- [ ] User session management validated

## 📊 Monitoring

### Check if Feature is Working
```bash
# 1. View recent generations
mongosh
use MySchool
db.questions.find().sort({ generated_at: -1 }).limit(5)

# 2. Count total questions generated
db.questions.countDocuments({})

# 3. See unique users
db.questions.distinct("generated_by")

# 4. Check for errors in recent generations
db.questions.find({}, { questions: 1 }).hint({ generated_at: -1 }).limit(1)
```

### Backend Logs
```bash
# Watch backend output for generation activity
# Should see:
# - POST /api/ebooks/generate-questions 200
# - Generated N questions
# - Saved to database
```

## 📚 Next Steps

1. **Test Basic Workflow** (follows Quick Start above)
2. **Test Error Scenarios** (see TESTING_GUIDE.md)
3. **Deploy to Production** (follow IMPLEMENTATION_SUMMARY.md)
4. **Monitor Questions** (use MongoDB queries above)
5. **Gather Feedback** (user experience, question quality)

## 🎯 Success Criteria

Feature is working if:
- ✅ Questions generate in 10-30 seconds
- ✅ Success message shows correct count
- ✅ Questions saved to MongoDB
- ✅ All question types (MCQ, Short, Long) generate correctly
- ✅ Error messages help users troubleshoot
- ✅ No double-click issues (button disabled during generation)
- ✅ User metadata (username, timestamp) captured
- ✅ Configuration saved alongside questions

## 📞 Support

### API Endpoint Status
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}
```

### Database Connection
```bash
mongosh
show dbs
use MySchool
db.questions.find().count()
```

### Claude API Status
Check: https://status.anthropic.com

---

## 🎉 You're All Set!

The AI Question Generation feature is now ready to use. Follow the steps above and you should see:
- Questions generating with Claude AI ✨
- Proper validation and error handling
- Questions saved to MongoDB for future use
- Real-time feedback to users

Happy generating! 🚀
