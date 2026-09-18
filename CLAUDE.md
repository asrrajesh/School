# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This repository contains two independent Python applications that communicate only via HTTP:

- **`edukoreaiapi/`** — FastAPI backend service handling authentication, eBook OCR scanning, and AI question generation
- **`edukoreaiui/`** — Flet desktop UI client (Flutter-based, not Kivy/PyQt/Tkinter) that calls the backend via `services/api_client.py`

There is no shared code between the projects; they interact only through REST API calls.

## Getting Started

### API (Backend)

```bash
cd edukoreaiapi
pip install -r requirements.txt
cp .env.example .env
python main.py
```

The API starts on `http://localhost:8000` (configurable via `.env`). Endpoint `/health` indicates readiness.

### UI (Frontend)

```bash
cd edukoreaiui
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Requires `API_BASE_URL` in `.env` (default `http://localhost:8000`). Uses Flet's built-in window launcher.

### Tests

API tests are plain Python scripts without pytest configuration:

```bash
cd edukoreaiapi
python tests/test_mongodb_connection.py
python tests/test_scanned_chapter.py
```

No UI tests exist. No linting configuration in either project.

## edukoreaiapi Architecture

### Core Components

**`main.py`**  
FastAPI application entry point. Sets up CORS from config, includes auth and ebooks routers, and preloads the OCR engine via a lifespan context manager. Exposes `/health` for readiness checks.

**`config/config.py`**  
Loads all settings from `.env` via python-dotenv. Key sections:
- `MONGO_URI`, `DB_NAME`, `DB_CONNECTION_TIMEOUT` — MongoDB connection
- `OCR_ENGINE` — Choose `easyocr` or `llm_vision` (vision-based OCR via LLM)
- `LLM_PROVIDER` — Choose `claude`, `openai`, `gemini`, or `ollama`; each provider has its own key/model config
- Server/CORS: `API_HOST`, `API_PORT`, `CORS_ORIGINS`

### Provider Pattern

Two swappable provider patterns keep the system extensible:

**LLM Provider**  
- Abstract base: `llm/base.py` (`LLMProvider`, `ImageInput`)
- Factory: `llm/factory.py` (`get_llm_provider()`, lru_cache'd, selects by `LLM_PROVIDER`)
- Implementations: `llm/providers/{claude,openai,gemini,ollama}_provider.py`
- Prompts: `llm/prompts/templates.py`
- Utilities: `llm/json_utils.py` (parse JSON from LLM responses), `llm/exceptions.py`

**OCR Provider**  
- Abstract base: `ocr/base.py` (`OCRProvider`)
- Factory: `ocr/factory.py` (`get_ocr_engine()`)
- Implementations:
  - `ocr/easyocr_engine.py` — EasyOCR library
  - `ocr/llm_vision_engine.py` — Delegates to the configured LLM provider for vision-based OCR

When adding a new LLM or OCR provider, implement the base interface and register it in the factory. Do not hardcode provider logic in call sites.

### Routers & Services

**`routers/auth.py`** (`/api/auth`)  
- `POST /login`, `POST /signup`, `POST /forgot-password` — delegates to `database/db.py`

**`routers/ebooks.py`** (`/api/ebooks`)  
- CRUD: `/classes`, `/subjects`, `/chapters`, `/chapter` (GET/POST)
- OCR: `POST /scan` — extract text from images
- Generation: `POST /generate-questions` — LLM generates questions from chapter content
- Upload: `POST /upload-questions`, `POST /save-uploaded-questions` — OCR + LLM extraction from scanned question papers
- Versioning: `/question-versions`
- Export: `GET /generate-questions/document` — render saved questions to a `.docx` file

Routers call `services/`:
- `ocr_service.py` — `extract_text_from_images()`
- `question_service.py` — `generate_questions_from_chapter()`, `extract_questions_from_paper()`
- `paper_generator.py` — `generate_question_paper_docx()`

These services call the provider factories and `database/db.py` (pymongo, bcrypt-hashed passwords).

**`schemas.py`**  
Pydantic request models for all endpoints.

## edukoreaiui Architecture

### Core Components

**`main.py`**  
Flet entry point. Sets up `ft.Page`, registers fonts, and implements client-side routing:
- `/login` (default `/`)
- `/signup`
- `/forgot_password`
- `/home`
- `/academics/setup_ebooks`
- `/academics/generate_questions`

Routes are handled via `page.on_route_change` and `page.on_view_pop`.

**`services/api_client.py`**  
The *only* module that talks to the backend. Uses httpx against `API_BASE_URL` (from `.env`). Contains one function per backend endpoint (e.g., `login_user()`, `scan_images()`, `generate_questions()`). Screens must call through this module; direct httpx calls elsewhere are a code smell.

**`screens/*.py`**  
Each screen file exports a `*_view(page)` function that returns Flet controls. Examples:
- `login_screen.py`
- `signup_screen.py`
- `generate_questions_screen.py`

**`components/app_frame.py`**  
`with_app_frame(content, page)` wraps authenticated screens with shared app bar and drawer chrome.

### Configuration

**`config/config.py`**  
Loads `.env`:
- `API_BASE_URL` — backend base URL (default `http://localhost:8000`)
- `APP_TITLE`, `THEME_COLOR`, `WINDOW_WIDTH/HEIGHT/RESIZABLE` — UI styling

**`resources/`** and **`fonts/`**  
- Logo: `edukoreai-logo.jpg`
- Font: `Cambria Regular.ttf` (registered as `page.fonts["Cambria Regular"]`)

Note: `pyproject.toml` references icon as `.png` but the actual file is `.jpg` — this may be a config inconsistency but no action taken unless requested.

## API Contract Between Projects

Any change to a backend router endpoint path, method, or request/response schema **must be mirrored** in `edukoreaiui/services/api_client.py`. There is no shared type system between the projects — they do not import each other's schemas. Keep them in sync manually.

Current endpoints:
- `/api/auth/*` (login, signup, forgot-password)
- `/api/ebooks/*` (classes, subjects, chapters, scan, generate-questions, upload-questions, save-uploaded-questions, question-versions, generate-questions/document)

## Known Issues & Oddities

- `edukoreaiui/README.md` is outdated (describes old direct-MongoDB architecture). Use this CLAUDE.md instead.
- No test files in `edukoreaiui/` — only backend has tests, and they are plain scripts without pytest configuration.
- No linting or formatting configuration (black, ruff, flake8, etc.) in either project.
