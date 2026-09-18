# EduKoreAI System Specification

**Last Updated:** 2026-09-18 (Updated: Icon & config refactoring)  
**Status:** Production-Ready  
**Version:** 1.0

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Data Model](#data-model)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Frontend Screens](#frontend-screens)
8. [AI Integration](#ai-integration)
9. [Development](#development)
10. [Deployment](#deployment)
11. [Known Gaps & Follow-Ups](#known-gaps--follow-ups)

---

## System Overview

**EduKoreAI** is a school management application that helps educators create assessment materials by scanning textbooks and generating exam questions using AI.

### Core Value Proposition

Users scan photos of textbook pages → Claude reads the text → Claude generates multiple-choice exam questions with various complexity levels → Export questions as formatted Word documents.

### Project Structure

```
edukoreaiapi/          FastAPI backend (Python) → handles auth, OCR, AI, database
edukoreaiui/           Flet desktop UI (Flutter-based) → login, ebook setup, question generation
knowledge/             This directory (consolidated specs & reference docs)
```

The two projects communicate **only over HTTP**. There is no shared code, no direct database access from the UI, and no shared Python modules.

---

## Architecture

### High-Level Design

```
┌─────────────────────────┐
│   edukoreaiui           │ (Flet Desktop App)
│ ┌─────────────────────┐ │
│ │ Login/Signup/Auth   │ │
│ │ Setup E-Books (OCR) │ │─────────┐
│ │ Generate Questions  │ │         │ HTTP/JSON
│ └─────────────────────┘ │         │
└─────────────────────────┘         │
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │    edukoreaiapi              │ (FastAPI)
                    │ ┌────────────────────────┐   │
                    │ │ /api/auth/*            │   │
                    │ │ /api/ebooks/*          │   │
                    │ ├────────────────────────┤   │
                    │ │ Config & Schemas       │   │
                    │ ├────────────────────────┤   │
                    │ │ LLM Provider (Claude)  │   │◄─── Anthropic API
                    │ │ OCR Provider (Claude)  │   │
                    │ ├────────────────────────┤   │
                    │ │ Database (MongoDB)     │   │
                    │ └────────────────────────┘   │
                    └──────────────────────────────┘
```

### Technology Stack

**Backend**
- Framework: FastAPI 0.115.6
- Server: Uvicorn with standard extras
- Database: MongoDB (PyMongo 4.17.0)
- Auth: bcrypt for password hashing
- LLM: Anthropic SDK (claude-3-5-sonnet or configured model)
- OCR: EasyOCR (vision) or Claude Vision API
- Export: python-docx for .docx generation

**Frontend**
- Framework: Flet 0.86.5 (Flutter-based, cross-platform)
- HTTP Client: httpx
- Config: python-dotenv

---

## Features

### 1. Authentication (edukoreaiapi/routers/auth.py)

**Endpoints:**
- `POST /api/auth/login` — username/password → access
- `POST /api/auth/signup` — create new account
- `POST /api/auth/forgot-password` — username existence check only (no email sending implemented)

**Username Format:** Email OR mobile number (validated by regex, configurable)
**Password:** Minimum 8 chars (default, configurable), hashed with bcrypt

**⚠️ Notable Limitation:** Forgot-password does not send emails/SMS — only validates account exists. Guest login is client-side only (sets `current_user = "Guest"` in Flet session, no backend record).

---

### 2. E-Book Scanning / OCR (Setup E-Books)

**User Workflow:**
1. Menu → Academics → Setup E-Books
2. Select Class / Subject / Chapter (fixed dropdown lists in `setup_ebooks_screen.py`)
3. Upload one or more images (PNG/JPG)
4. Click **SCAN** → Claude extracts text from images
5. Review/edit extracted text in text field
6. Click **SUBMIT** → save to MongoDB

**Key Points:**
- **Dropdown lists are hardcoded** — not database-driven. Classes: I–X, Subjects: Science/English/Computer Science/Math, Chapters: 1–50
- **OCR Provider:** Configurable — EasyOCR (local) or Claude Vision API (remote)
- **Content History:** Not kept — re-submitting overwrites previous text
- **Multi-image handling:** Sequential calls (one Claude call per image), not batched
- **Auto-load:** Revisiting an already-scanned chapter loads existing content

**Backend Routes:**
- `POST /api/ebooks/scan` — Accept multipart images, extract text via Claude
- `GET /api/ebooks/chapter?class_name=&subject=&chapter=` — Fetch saved content
- `POST /api/ebooks/chapter` — Save content

---

### 3. Question Generation

**User Workflow:**
1. Menu → Academics → Generate Questions
2. Select Class → Subject → Chapter(s) (multiselect, populated from saved chapters)
3. Select Assessment Category, Assessment Number, Complexity
4. Click **GENERATE** → Claude generates questions from chapter text
5. Questions saved to MongoDB with version number
6. Can **DOWNLOAD** as formatted .docx file

**Features:**
- **Multi-chapter support:** Select multiple chapters, questions generated from combined content
- **Version tracking:** Auto-incrementing version per (class/subject/chapter/category/number/complexity) combination
- **Source tracking:** Questions marked as "generated" (via API) or "uploaded" (via image OCR)
- **Export:** .docx with formatted questions, answers, options

**Backend Routes:**
- `GET /api/ebooks/classes` — Distinct class values from saved chapters
- `GET /api/ebooks/subjects?class_name=` — Subjects for a class
- `GET /api/ebooks/chapters?class_name=&subject=` — Chapters for class+subject
- `POST /api/ebooks/generate-questions` — Generate questions from chapter
- `GET /api/ebooks/question-versions` — List saved question sets
- `POST /api/ebooks/upload-questions` — OCR images of question papers + extract questions
- `POST /api/ebooks/save-uploaded-questions` — Save pre-extracted questions from upload
- `GET /api/ebooks/generate-questions/document` — Download questions as .docx

**Prompt Handling:** Prompts are in `edukoreaiapi/llm/prompts/templates.py`, substituting chapter content + configuration. Model defaults to `claude-sonnet-4-5-20250929` (configurable via `ANTHROPIC_MODEL` env var).

---

## Data Model

### Collection: `users`

```json
{
  "_id": ObjectId,
  "username": "user@example.com",      // or +1234567890
  "password": "$2b$12$...",            // bcrypt hash
  "created_at": ISODate()
}
```

**Unique Index:** `username` (created on first `get_db()` call)

### Collection: `scanned_chapters`

```json
{
  "_id": ObjectId,
  "class": "X",
  "subject": "Science",
  "chapter": "1",
  "content": "Chapter text extracted via OCR...",
  "created_by": "username",
  "created_at": ISODate(),
  "updated_by": "username",
  "updated_at": ISODate()
}
```

### Collection: `generated_questions`

```json
{
  "_id": ObjectId,
  "class": "X",
  "subject": "Science",
  "chapter": ["1", "2"],               // array of chapters
  "assessment_category": "Short Answer",
  "assessment_number": "1",
  "complexity": "Medium",
  "version": 1,
  "questions": [
    {
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "answer": "B"
    }
  ],
  "source": "generated",               // or "uploaded"
  "generated_by": "username",
  "generated_at": ISODate()
}
```

---

## Configuration

### Environment Variables (edukoreaiapi/.env)

```
# MongoDB
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/?appName=Cluster0
DB_NAME=MySchool
DB_CONNECTION_TIMEOUT=10

# LLM Provider
LLM_PROVIDER=claude|openai|gemini|ollama
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929  (or any supported Claude model)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_REQUEST_TIMEOUT=120

# OCR Provider
OCR_ENGINE=easyocr|llm_vision
OCR_LANGUAGES=en
OCR_USE_GPU=true

# Security
PASSWORD_MIN_LENGTH=8
EMAIL_PATTERN=^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$
MOBILE_PATTERN=^\+?[0-9]{10,15}$

# Server
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:*,https://yourdomain.com
```

### Environment Variables (edukoreaiui/.env)

```
API_BASE_URL=http://localhost:8000
APP_TITLE=EduKoreAI
APP_LOGO=resources/edukoreai-logo.ico
THEME_COLOR=#3949AB
WINDOW_WIDTH=400
WINDOW_HEIGHT=780
WINDOW_RESIZABLE=true
BACKGROUND_COLOR=#F5F5F5
```

---

## API Reference

All endpoints return JSON. See `edukoreaiapi/schemas.py` for request/response models.

### Auth Endpoints

| Method | Path | Auth Required | Request | Response |
|--------|------|---------------|---------|----------|
| POST | `/api/auth/signup` | No | `{username, password}` | `{success, user or error}` |
| POST | `/api/auth/login` | No | `{username, password}` | `{success, user or error}` |
| POST | `/api/auth/forgot-password` | No | `{username}` | `{success or error}` |

### E-Book Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/ebooks/scan` | multipart `images` | `{success, text or error}` |
| GET | `/api/ebooks/chapter` | query: `class_name, subject, chapter` | `{success, content or error}` |
| POST | `/api/ebooks/chapter` | `{class_name, subject, chapter, content}` | `{success or error}` |
| GET | `/api/ebooks/classes` | — | `{success, classes: []}` |
| GET | `/api/ebooks/subjects` | query: `class_name` | `{success, subjects: []}` |
| GET | `/api/ebooks/chapters` | query: `class_name, subject` | `{success, chapters: []}` |
| POST | `/api/ebooks/generate-questions` | `{class, subject, chapters[], assessment_category, assessment_number, complexity}` | `{success, version or error}` |
| GET | `/api/ebooks/question-versions` | query: `class, subject, chapter, ...` | `{success, versions: []}` |
| POST | `/api/ebooks/upload-questions` | multipart `images` | `{success, questions: [] or error}` |
| POST | `/api/ebooks/save-uploaded-questions` | `{class, subject, chapters[], ..., questions}` | `{success, version or error}` |
| GET | `/api/ebooks/generate-questions/document` | query: `class, subject, chapter, ...` | raw `.docx` bytes |

---

## Frontend Screens

**Login** (`screens/login_screen.py`)
- Email/mobile + password form
- "Sign up" and "Forgot password" links
- "Continue as Guest" button (client-side, no backend)

**Signup** (`screens/signup_screen.py`)
- Email/mobile + password + confirm password
- Validation feedback
- "Sign in" link

**Forgot Password** (`screens/forgot_password_screen.py`)
- Email/mobile input
- Username existence check (no email sending)

**Home** (`screens/home_screen.py`)
- Dashboard with navigation to Academics sections

**Setup E-Books** (`screens/setup_ebooks_screen.py`)
- Class/Subject/Chapter dropdowns (hardcoded lists)
- File picker for images
- **SCAN** button → shows snackbar, uploads to `/api/ebooks/scan`
- Text area showing extracted content
- **SUBMIT** button → saves to `/api/ebooks/chapter`

**Generate Questions** (`screens/generate_questions_screen.py`)
- **Generate Tab:**
  - Class/Subject/Chapter selectors (cascading, database-driven)
  - Assessment Category, Assessment Number, Complexity dropdowns
  - **GENERATE** button
  - Version history + **DOWNLOAD** button
- **Upload Tab:**
  - File picker for question paper images
  - Extract button → `/api/ebooks/upload-questions`
  - Edit extracted questions in text area
  - **SAVE** button

**Shared Frame** (`components/app_frame.py`)
- Top app bar with menu icon
- Drawer with navigation + user info + logo (reads `APP_LOGO` from config)
- Applied to all authenticated screens

**Logo & Icons:**
- Window icon, login screen logo, and drawer logo all use `APP_LOGO` from `config/config.py`
- Default: `resources/edukoreai-logo.ico` (Windows ICO format for best taskbar/titlebar display)
- Logo path is resolved at runtime relative to the script directory for cross-platform compatibility
- Set via `APP_LOGO` env var in `.env` (can be customized without code changes)

---

## AI Integration

### LLM Provider Pattern

**Location:** `edukoreaiapi/llm/`

Abstract base (`base.py`):
```python
class LLMProvider:
    def generate_text(prompt, images=[], max_tokens, temperature) -> str
```

Factory (`factory.py`):
```python
get_llm_provider() -> LLMProvider
```

Implementations:
- `providers/claude_provider.py` — Anthropic SDK
- `providers/openai_provider.py` — OpenAI SDK
- `providers/gemini_provider.py` — Google SDK
- `providers/ollama_provider.py` — HTTP to local Ollama

**When Adding a Provider:**
1. Implement `LLMProvider` interface in `providers/new_provider.py`
2. Register in `factory.py` `get_llm_provider()` conditional
3. All call sites use the factory, no hardcoding

### OCR Provider Pattern

**Location:** `edukoreaiapi/ocr/`

Abstract base (`base.py`):
```python
class OCRProvider:
    def extract_text(images) -> str
```

Factory (`factory.py`):
```python
get_ocr_engine() -> OCRProvider
```

Implementations:
- `easyocr_engine.py` — EasyOCR library (local, GPU-optional)
- `llm_vision_engine.py` — Delegates to configured LLM provider

---

## Development

### Local Setup

**Backend:**
```bash
cd edukoreaiapi
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with MongoDB URI, API keys
python main.py
# Runs on http://localhost:8000
```

**Frontend:**
```bash
cd edukoreaiui
python -m venv uivenv
source uivenv/bin/activate  # Windows: uivenv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with API_BASE_URL, etc.
python main.py
# Opens Flet window
```

### Testing

**Backend Tests** (no pytest config, plain scripts):
```bash
cd edukoreaiapi
python tests/test_mongodb_connection.py
python tests/test_scanned_chapter.py
```

**Frontend:** No automated tests. Manual UI testing only.

### Code Organization

**Backend (edukoreaiapi/)**
```
main.py                  FastAPI app entry point, lifespan, route includes
config/config.py         dotenv loading, all config vars
routers/
  auth.py               Login/signup/forgot-password routes
  ebooks.py             OCR, question generation, document export routes
database/
  db.py                 MongoDB collection access, CRUD functions
services/
  ocr_service.py        extract_text_from_images() wrapper
  question_service.py   generate_questions_from_chapter() wrapper
  paper_generator.py    generate_question_paper_docx() 
schemas.py              Pydantic request/response models
llm/                    LLM provider abstraction
ocr/                    OCR provider abstraction
```

**Frontend (edukoreaiui/)**
```
main.py                 Flet entry point, routing, icon path resolution
                        • Resolves icon path using Path(__file__).parent.resolve()
                        • Uses .as_posix() for cross-platform forward slashes
                        • Validates file existence before setting window icon
config/config.py        dotenv loading, APP_LOGO path (default: resources/edukoreai-logo.ico)
services/
  api_client.py         httpx wrappers for all backend endpoints
screens/
  login_screen.py       • Imports APP_LOGO from config (not hardcoded)
  signup_screen.py
  forgot_password_screen.py
  home_screen.py
  setup_ebooks_screen.py
  generate_questions_screen.py
components/
  app_frame.py          Shared app bar, drawer, chrome
                        • Imports APP_LOGO from config (not hardcoded)
resources/              Logos, assets
  edukoreai-logo.ico    Window icon, login, drawer (ICO format for Windows compatibility)
fonts/                  Custom fonts
  Cambria Regular.ttf
```

---

## Deployment

### Backend Deployment (Cloud Run)

**Docker:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

**CI/CD:** `.github/workflows/deploy.yml` (manual trigger)
- Requires GCP setup (Cloud Run, Artifact Registry, Workload Identity Federation)
- Builds image, pushes to Artifact Registry, deploys to Cloud Run
- Env vars from GitHub Secrets: `MONGO_URI`, `DB_NAME`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`
- Deployed URL is public (no auth required)

### Frontend Deployment (APK)

**.github/workflows/build-apk.yml** (manual trigger, `build_mode` input)
- Requires Flutter 3.44.8, Java 17, Python 3.12
- Generates `.env` from GitHub Vars (not Secrets)
- Builds APK via Flutter

---

## Known Gaps & Follow-Ups

### Security
1. **Exposed credential in test file** — `edukoreaiapi/tests/test_mongodb_connection.py` contains hardcoded MongoDB Atlas credentials. Rotate these credentials immediately in MongoDB Atlas and move to env vars.
2. **No API key protection** — Deployed backend is public; anyone can call `/generate-questions` and spend Anthropic credits.
3. **Session management not implemented** — `MAX_LOGIN_ATTEMPTS`, `LOCKOUT_DURATION`, `SESSION_TIMEOUT` are mentioned in docs but not enforced in code.

### Feature Gaps
1. **Forgot-password incomplete** — No email/SMS sending. `request_password_reset()` is a stub.
2. **Guest login not tracked** — Guest account doesn't create a backend record; questions authored by guests are indistinguishable from real users.
3. **No content history for chapters** — Overwriting scanned chapters loses previous text permanently.
4. **Hardcoded chapter taxonomy** — Classes, subjects, chapters in `setup_ebooks_screen.py` are disconnected from any admin interface or database-driven config.

### Performance
1. **Sequential OCR calls** — Multi-image scans call Claude once per image, not batched. Scales linearly with image count.
2. **No image format conversion** — Relies on MIME type guessing; could fail on misconfigured files.

### Code Quality
1. **Inconsistent error handling in api_client.py** — `scan_images()` raises on error; others return `{success: False}`.
2. **Async/await inconsistency** — Some routes use `asyncio.to_thread`, others block directly.
3. **Duplicate validation patterns** — Email/mobile validation logic not centralized.

---

## Notes for Developers

### Cross-Project Contract
- Any change to an API endpoint path/payload must be mirrored in both `edukoreaiapi/routers/` and `edukoreaiui/services/api_client.py`.
- No shared types between projects; keep schemas in sync manually.

### Configuration Precedence
- Environment variables override `.env.example` defaults
- `.env.example` is template only; never rely on it for deployments
- Always check deployed env vars (GitHub Secrets, Cloud Run configuration, etc.) — docs may lag

### Testing Before Deployment
- Run backend tests locally: `python edukoreaiapi/tests/*.py`
- Test frontend manually: login, setup ebooks, generate questions, download
- Verify MongoDB has correct documents (use MongoDB Atlas UI)
- Check API response times under load (generate questions is slowest)

---

**End of Specification**
