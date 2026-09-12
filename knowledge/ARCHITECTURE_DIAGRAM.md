# AI Question Generation - Architecture Diagram

## System Architecture

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          USER INTERFACE (Flet)                          ┃
┃                                                                         ┃
┃  ┌───────────────────────────────────────────────────────────────┐   ┃
┃  │ Generate Questions Screen                                    │   ┃
┃  │                                                               │   ┃
┃  │  Class: [Class 10         ▼]  Subject: [Physics    ▼]        │   ┃
┃  │  Chapter: [Electricity    ▼]                                 │   ┃
┃  │                                                               │   ┃
┃  │  ┌─────────────────────────────────────────────────────┐   │   ┃
┃  │  │ Question Configuration Table (NEW LAYOUT)         │   │   ┃
┃  │  │                                                   │   │   ┃
┃  │  │ Question Type │ Count │ Marks │ Total │ Add │ Del│   │   ┃
┃  │  ├───────────────┼───────┼───────┼───────┼─────┼────┤   │   ┃
┃  │  │ MCQ       ▼   │   2   │  1.0  │  2.0  │ ⊕   │ ⊖  │   │   ┃
┃  │  ├───────────────┼───────┼───────┼───────┼─────┼────┤   │   ┃
┃  │  │ Short     ▼   │   2   │  2.0  │  4.0  │ ⊕   │ ⊖  │   │   ┃
┃  │  ├───────────────┼───────┼───────┼───────┼─────┼────┤   │   ┃
┃  │  │ Long      ▼   │   1   │  5.0  │  5.0  │ ⊕   │ ⊖  │   │   ┃
┃  │  └─────────────────────────────────────────────────────┘   │   ┃
┃  │                                                               │   ┃
┃  │  ┌──────────────────────────────────────────────────────┐  │   ┃
┃  │  │          [GENERATE QUESTIONS] Button               │  │   ┃
┃  │  │     (Shows loading spinner during generation)      │  │   ┃
┃  │  └──────────────────────────────────────────────────────┘  │   ┃
┃  │                                                               │   ┃
┃  │  Status: ✅ "Generated 5 questions successfully!"           │   ┃
┃  └───────────────────────────────────────────────────────────────┘   ┃
┃                                                                         ┃
┃  screens/generate_questions_screen.py                                  ┃
┃  ├── Async handler for button click                                    ┃
┃  ├── Form validation                                                   ┃
┃  ├── Calls api_client.generate_questions()                             ┃
┃  └── Displays success/error feedback                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                    │
                                    │ HTTP POST
                                    │ (JSON Payload)
                                    ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                         API CLIENT (Python)                            ┃
┃                                                                         ┃
┃  services/api_client.py                                                ┃
┃  ├── generate_questions(class, subject, chapter, rows, user)           ┃
┃  ├── Endpoint: POST /api/ebooks/generate-questions                     ┃
┃  ├── Timeout: 120 seconds (allows Claude processing)                   ┃
┃  └── Returns: {success, id, questions} | {success, error}              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                    │
                 ╔══════════════════╩══════════════════╗
                 │   HTTP OVER NETWORK (TCP/IP)       │
                 │        JSON Payload                │
                 ╚══════════════════╤══════════════════╝
                                    │
                                    ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                        BACKEND API (FastAPI)                           ┃
┃                                                                         ┃
┃  routers/ebooks.py                                                     ┃
┃  ┌───────────────────────────────────────────────────────────┐        ┃
┃  │ @router.post("/generate-questions")                       │        ┃
┃  │                                                            │        ┃
┃  │ 1. Parse & Validate Request Schema                        │        ┃
┃  │    ├── class_name ✓                                       │        ┃
┃  │    ├── subject ✓                                          │        ┃
┃  │    ├── chapter ✓                                          │        ┃
┃  │    ├── questionRows[] ✓                                   │        ┃
┃  │    └── username ✓                                         │        ┃
┃  │                                                            │        ┃
┃  │ 2. Fetch Chapter Content from MongoDB                    │        ┃
┃  └────────────────┬────────────────────────────────────────┘        ┃
┃                   │                                                   ┃
┃                   ▼                                                   ┃
┃  database/db.py                                                      ┃
┃  ┌───────────────────────────────────────────────────────────┐       ┃
┃  │ get_scanned_chapter(class, subject, chapter)              │       ┃
┃  │ → Query: db.scanned_chapters.find_one({...})              │       ┃
┃  │ → Return: {content: "Chapter text..."}                    │       ┃
┃  └────────────────┬────────────────────────────────────────┘        ┃
┃                   │                                                   ┃
┃                   ▼                                                   ┃
┃  routers/ebooks.py                                                   ┃
┃  ┌───────────────────────────────────────────────────────────┐       ┃
┃  │ 3. Generate Questions using Claude AI                     │       ┃
┃  └────────────────┬────────────────────────────────────────┘        ┃
┃                   │                                                   ┃
┃                   ▼                                                   ┃
┃  services/claude_questions.py                                        ┃
┃  ┌───────────────────────────────────────────────────────────┐       ┃
┃  │ generate_questions_from_chapter(content, question_rows)   │       ┃
┃  │                                                            │       ┃
┃  │ 1. Build Detailed Prompt                                  │       ┃
┃  │    ├── Chapter content as context                         │       ┃
┃  │    ├── Requirement: 2 MCQ (1 mark each)                  │       ┃
┃  │    ├── Requirement: 2 Short (2 marks each)               │       ┃
┃  │    ├── Requirement: 1 Long (5 marks each)                │       ┃
┃  │    ├── JSON schema for response                           │       ┃
┃  │    └── Quality guidelines                                │       ┃
┃  │                                                            │       ┃
┃  │ 2. Call Claude API                                        │       ┃
┃  └────────────────┬────────────────────────────────────────┘        ┃
┃                   │                                                   ┃
┃                   ├─────────────────────────────────┐                ┃
┃                   │                                 │                ┃
┃                   ▼                                 ▼                ┃
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  ┏━━━━━━━━━━━━━━━━━━━━━━━┓ ┃
┃      ANTHROPIC CLAUDE API              ┃  ┃   NETWORK REQUEST    ┃ ┃
┃                                         ┃  ┃   (HTTPS REST API)   ┃ ┃
┃  model: claude-sonnet-4-5-20250929      ┃  ┃                      ┃ ┃
┃  max_tokens: 4096                       ┃  ┃   Endpoint:          ┃ ┃
┃  temperature: 0 (deterministic)         ┃  ┃ api.anthropic.com    ┃ ┃
┃                                         ┃  ┃                      ┃ ┃
┃  Returns: JSON with questions           ┃  ┃   Authentication:    ┃ ┃
┃  ├── MCQ: options A,B,C,D               ┃  ┃   ANTHROPIC_API_KEY  ┃ ┃
┃  ├── Short: 1-2 sentence answers        ┃  ┗━━━━━━━━━━━━━━━━━━━━━━━┛ ┃
┃  └── Long: 3-5 sentence answers         ┃                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛                              ┃
                   │                                                   ┃
                   ▼                                                   ┃
┃  services/claude_questions.py                                        ┃
┃  ┌───────────────────────────────────────────────────────────┐       ┃
┃  │ 3. Parse & Validate JSON Response                         │       ┃
┃  │    ├── Extract questions array                            │       ┃
┃  │    ├── Validate structure                                 │       ┃
┃  │    ├── Ensure all types present                           │       ┃
┃  │    └── Return: [{type, marks, question, options, ...}]   │       ┃
┃  └────────────────┬────────────────────────────────────────┘        ┃
┃                   │                                                   ┃
┃                   ▼                                                   ┃
┃  routers/ebooks.py                                                   ┃
┃  ┌───────────────────────────────────────────────────────────┐       ┃
┃  │ 4. Save Questions to Database                             │       ┃
┃  └────────────────┬────────────────────────────────────────┘        ┃
┃                   │                                                   ┃
┃                   ▼                                                   ┃
┃  database/db.py                                                      ┃
┃  ┌───────────────────────────────────────────────────────────┐       ┃
┃  │ save_generated_questions(...)                              │       ┃
┃  │ → db.questions.insert_one({                              │       ┃
┃  │     class, subject, chapter,                              │       ┃
┃  │     questions: [...],                                     │       ┃
┃  │     configuration: [...],                                 │       ┃
┃  │     generated_by: username,                               │       ┃
┃  │     generated_at: timestamp                               │       ┃
┃  │   })                                                       │       ┃
┃  │ → Return: {success: true, id: '<mongodb_id>'}             │       ┃
┃  └────────────────┬────────────────────────────────────────┘        ┃
┃                   │                                                   ┃
┃                   ▼                                                   ┃
┃  routers/ebooks.py                                                   ┃
┃  ┌───────────────────────────────────────────────────────────┐       ┃
┃  │ 5. Return Success Response (200 OK)                       │       ┃
┃  │ {                                                          │       ┃
┃  │   "success": true,                                         │       ┃
┃  │   "id": "507f1f77bcf86cd799439011",                       │       ┃
┃  │   "questions": [                                           │       ┃
┃  │     {type, marks, question, options, ...},                │       ┃
┃  │     ...                                                    │       ┃
┃  │   ],                                                       │       ┃
┃  │   "message": "Generated 5 questions successfully."         │       ┃
┃  │ }                                                          │       ┃
┃  └───────────────────────────────────────────────────────────┘       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                    │
                 ╔══════════════════╩══════════════════╗
                 │   HTTP RESPONSE (200 OK)           │
                 │   JSON with questions             │
                 ╚══════════════════╤══════════════════╝
                                    │
                                    ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    API CLIENT & FRONTEND (Flet)                         ┃
┃                                                                         ┃
┃  api_client.py                                                          ┃
┃  ├── Receive response                                                   ┃
┃  ├── Parse JSON                                                         ┃
┃  └── Return to UI                                                       ┃
┃                                                                         ┃
┃  generate_questions_screen.py                                           ┃
┃  ├── Hide loading spinner                                               ┃
┃  ├── Check success flag                                                 ┃
┃  ├── Display: "✓ Generated 5 questions successfully!" (GREEN)           ┃
┃  ├── Re-enable button                                                   ┃
┃  └── Questions now available in MongoDB for future use                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                    │
                                    ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    DATA PERSISTENCE (MongoDB)                           ┃
┃                                                                         ┃
┃  Database: MySchool                                                     ┃
┃  │                                                                      ┃
┃  ├─ scanned_chapters (Existing)                                         ┃
┃  │  └─ Document: {class, subject, chapter, content, created_by, ...}   ┃
┃  │                                                                      ┃
┃  └─ questions (NEW)                                                     ┃
┃     └─ Document: {                                                      ┃
┃          class, subject, chapter,                                       ┃
┃          questions: [                                                   ┃
┃            {type: "mcq", marks: 1, question, options, correctOption},   ┃
┃            {type: "short", marks: 2, question, answerKey},              ┃
┃            {type: "long", marks: 5, question, answerKey},               ┃
┃            ...                                                          ┃
┃          ],                                                             ┃
┃          configuration: [{questionType, questionCount, marks}, ...],    ┃
┃          generated_by: "user@email.com",                                ┃
┃          generated_at: ISODate(...)                                     ┃
┃        }                                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION                               │
│                                                                         │
│  1. Configure questions in table                                       │
│  2. Click "GENERATE QUESTIONS"                                         │
│  3. See loading indicator                                              │
│  4. Receive success/error message                                      │
│  5. Check MongoDB for saved questions                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                  ┌───────────────┼───────────────┐
                  │               │               │
                  ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │   Frontend   │  │   Backend    │  │   Database   │
         │    (Flet)    │  │   (FastAPI)  │  │  (MongoDB)   │
         └──────────────┘  └──────────────┘  └──────────────┘
                  │               │               │
    ┌─────────────┼───────────────┼───────────────┼─────────────┐
    │             │               │               │             │
    │  ┌──────────▼────────┐      │      ┌────────▼──────────┐ │
    │  │  Screen Code      │      │      │  Database Access  │ │
    │  │                   │      │      │                   │ │
    │  │ • Validation      │      │      │ • Read chapter    │ │
    │  │ • User session    │      │      │ • Write questions │ │
    │  │ • UI updates      │      │      │ • Query results   │ │
    │  └────────┬──────────┘      │      └────────┬──────────┘ │
    │           │                 │               │             │
    │  ┌────────▼─────────────┐   │                              │
    │  │   API Client Code    │   │  ┌──────────────────────┐   │
    │  │                      │   │  │  Router Code         │   │
    │  │ • HTTP request       │   │  │  • Endpoint handler  │   │
    │  │ • JSON payload       │───┼──│  • Error handling    │   │
    │  │ • Timeout 120s       │   │  │  • Response format   │   │
    │  │ • Error handling     │   │  └────────┬──────────────┘  │
    │  └─────────────────────┘   │           │                  │
    │                             │  ┌────────▼──────────────┐  │
    │                             │  │  Service Code        │  │
    │                             │  │                      │  │
    │                             │  │ • Build prompt       │  │
    │                             │  │ • Call Claude API    │  │
    │                             │  │ • Parse response     │  │
    │                             │  │ • Validate JSON      │  │
    │                             │  └────────┬─────────────┘  │
    │                             │           │                 │
    │                             │  ┌────────▼──────────────┐  │
    │                             │  │  Claude API          │  │
    │                             │  │  (Anthropic)         │  │
    │                             │  │                      │  │
    │                             │  │ • Generate questions │  │
    │                             │  │ • Return JSON        │  │
    │                             │  └──────────────────────┘  │
    │                             │                             │
    └─────────────────────────────┴─────────────────────────────┘
```

---

## Request/Response Flow

```
┌──────────────┐
│ User Clicks  │
│   Button     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ Async Handler Called     │
│ • Validate form          │
│ • Get current user       │
│ • Show loading spinner   │
└──────┬───────────────────┘
       │
       │  POST JSON Request
       │  {class, subject, chapter, questionRows[], username}
       │
       ▼
┌──────────────────────────┐
│ Backend Receives Request │
│ • Validate schema        │
│ • Parse parameters       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Fetch Chapter Content    │
│ • Query MongoDB          │
│ • Get scanned chapter    │
│ • Return text content    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Generate Questions       │
│ • Call Claude API        │
│ • Send prompt + chapter  │
│ • Receive JSON response  │
│ • Parse questions array  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Save to Database         │
│ • Insert document        │
│ • Add metadata           │
│ • Return document ID     │
└──────┬───────────────────┘
       │
       │  HTTP 200 OK + JSON Response
       │  {success: true, id, questions[], message}
       │
       ▼
┌──────────────────────────┐
│ Frontend Receives        │
│ • Parse response         │
│ • Check success flag     │
│ • Hide loading spinner   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Display Feedback         │
│ • If success:            │
│   Show green message     │
│ • If error:              │
│   Show red error message │
│ • Re-enable button       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Complete                 │
│ Questions in MongoDB     │
│ Ready for future use     │
└──────────────────────────┘
```

---

## Database Schema Evolution

```
Before Implementation:
┌──────────────────────────────────────────┐
│ MySchool (MongoDB Database)              │
│                                          │
│ Collections:                             │
│ ├── users                                │
│ │   └── {username, password, created}   │
│ │                                        │
│ └── scanned_chapters                     │
│     └── {class, subject, chapter,        │
│         content, created_by, ...}        │
└──────────────────────────────────────────┘


After Implementation:
┌──────────────────────────────────────────┐
│ MySchool (MongoDB Database)              │
│                                          │
│ Collections:                             │
│ ├── users                                │
│ │   └── {username, password, created}   │
│ │                                        │
│ ├── scanned_chapters (unchanged)         │
│ │   └── {class, subject, chapter,        │
│ │       content, created_by, ...}        │
│ │                                        │
│ └── questions ✨ NEW!                    │
│     └── {class, subject, chapter,        │
│         questions: [                     │
│           {type, marks, question, ...},  │
│           ...                            │
│         ],                               │
│         configuration: [...],            │
│         generated_by, generated_at}      │
└──────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌─────────────────────────────────┐
│ User Clicks Generate Button     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Validation Checks               │ ─── No ──→ "Select class, subject, chapter"
│ ├─ Class selected?              │
│ ├─ Subject selected?            │
│ ├─ Chapter selected?            │
│ └─ Question row valid?          │
└────────┬────────────────────────┘
         │ Yes
         ▼
┌─────────────────────────────────┐
│ Call Backend API                │
└────────┬────────────────────────┘
         │
         ├─ Network Error ─────────→ "Cannot reach API server"
         │
         ├─ Invalid Chapter ───────→ "Chapter content not found"
         │
         ├─ Invalid API Key ───────→ "Claude denied the API key"
         │
         ├─ API Rate Limit ────────→ "Claude request failed (429)"
         │
         ├─ API Error ─────────────→ "Claude request failed (status)"
         │
         └─ Timeout ───────────────→ "Request timeout (120s)"
         │
         ▼ Success
┌─────────────────────────────────┐
│ ✓ Show Success Message          │
│ "Generated N questions!"         │
└─────────────────────────────────┘
```

---

## Performance Timeline

```
Time  │ Event
──────┼──────────────────────────────────────────────────────────
0ms   │ User clicks "GENERATE QUESTIONS"
      │ Loading indicator appears
      │
50ms  │ Request sent to backend API
      │
75ms  │ Backend receives request
      │ Validation + parsing (5ms)
      │ MongoDB query for chapter (20ms)
      │ Response received (10ms)
      │
100ms │ Prompt built and sent to Claude API
      │
200ms │ Claude API processes request
      │ (Network latency: 100-500ms)
      │
3000  │ Claude begins generating questions
      │ (Generation time: 5000-20000ms typical)
      │
15000 │ Claude completes generation
      │ JSON response received
      │
15050 │ Backend parses JSON
      │ MongoDB insert operation
      │ Response prepared (50ms)
      │
15100 │ Response sent to frontend API
      │
15150 │ Frontend receives response
      │ UI updates (50ms)
      │ "Generated N questions!" message shown
      │
15200 │ Complete - Button re-enabled
      │
      │ Total time: ~15 seconds (typical)
```

---

## Dependency Graph

```
Frontend Dependencies:
  flet ──────────────┐
  httpx ────────────┤
  asyncio ──────────┤
  pydantic ─────────┴──> generate_questions_screen.py
                          └──> api_client.py


Backend Dependencies:
  fastapi ───────────┐
  pymongo ───────────┤
  anthropic ─────────┤
  pydantic ──────────┴──> routers/ebooks.py
                            ├──> database/db.py
                            ├──> schemas.py
                            └──> services/claude_questions.py
                                  └──> anthropic.Anthropic()


External Services:
  MongoDB ← DB Storage
  Anthropic Claude API ← LLM
  Network ← Communication
```

---

## Security & Data Flow

```
USER DATA FLOW:
┌─────────────────────────────────────────────┐
│ Username (from session)                     │
│ Class/Subject/Chapter (from user selection) │
│ Question config (from form)                 │
└────────────────┬────────────────────────────┘
                 │ Validated by Pydantic
                 ▼
         ┌──────────────────┐
         │ HTTP Request     │
         │ (JSON over HTTPS)│
         └────────┬─────────┘
                  │ Parsed & Logged
                  ▼
         ┌──────────────────────────┐
         │ Backend Processing       │
         │ • Authenticated via API  │
         │ • User tracked          │
         │ • Audit trail recorded  │
         └────────┬─────────────────┘
                  │ Saved to MongoDB
                  ▼
         ┌──────────────────────────┐
         │ MongoDB Storage          │
         │ • Document stored        │
         │ • Timestamp recorded     │
         │ • User metadata saved    │
         └──────────────────────────┘


API KEY SECURITY:
┌─────────────────────────────────────────────┐
│ ANTHROPIC_API_KEY (in .env)                 │
│ • Never logged                              │
│ • Never sent to frontend                    │
│ • Only used in backend service              │
│ • Should be rotated periodically            │
└─────────────────────────────────────────────┘
```

---

## Scalability Considerations

```
Current Architecture:
  Single User: ✓ Works fine
  Multiple Users: ✓ Works (async requests)
  Concurrent Requests: ✓ Works (async/await)
  
Potential Bottlenecks:
  
  1. Claude API Rate Limit (tier dependent)
     Solution: Implement request queuing
  
  2. MongoDB Connection Pool
     Solution: Increase pool size in production
  
  3. Network Latency
     Solution: Deploy backend closer to Claude API
  
  4. Memory Usage (large chapters)
     Solution: Stream processing for huge texts
  
Recommended Improvements:
  • Add request queuing for rate limiting
  • Implement caching for frequently generated questions
  • Add database indexing on class+subject+chapter
  • Monitor API usage and costs
  • Set up alerts for errors/slowdowns
  • Implement pagination for large result sets
```

---

This diagram shows the complete architecture, data flow, error handling, and system interactions for the AI Question Generation feature.
