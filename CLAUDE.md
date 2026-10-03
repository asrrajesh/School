# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This repository contains two independent Python applications that communicate only via HTTP:

- **`edukoreaiapi/`** — FastAPI backend service handling authentication (password + Google OAuth), eBook OCR scanning, and AI question generation
- **`edukoreaiui/`** — Flet desktop/web/Android UI client (Flet is Flutter-based, not Kivy/PyQt/Tkinter) that calls the backend via `services/api_client.py`

There is no shared code between the projects; they interact only through REST API calls. `designsamples/` holds static HTML design mockups (not part of either app).

## Knowledge and Feature Workflow

`knowledge/` is the reverse-engineered, **as-is** documentation of the application. Read the relevant file before changing behavior:

- `knowledge/functional-specification.md` — what the product does, users and flows (there is only one role today)
- `knowledge/data-model.md` — MongoDB collections, fields, indexes
- `knowledge/api-specification.md` — every endpoint's request and response
- `knowledge/prompt-and-generation-rule.md` — OCR, LLM prompts, question generation and `.docx` export rules
- `knowledge/ui-behavior-and-design.md` — screens, behavior, visual design
- `knowledge/nfr.md` — security, performance, deployment, known gaps

New work follows this flow: write an `intent.md` for the feature (Problem, Proposed outcome, Affected users and systems, Constraints, Open questions; with author, date and status), implement it, then run `/update-knowledge <path to intent.md>` to merge what was built back into `knowledge/`. Keep knowledge files as current-state snapshots, not changelogs.

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

Requires `API_BASE_URL` in `.env` (default `http://localhost:8000`). `UI_MODE=desktop|web` selects a native Flet window or the browser (`WEB_PORT`, default 8550); `web` is the workaround when Windows Smart App Control blocks the desktop client.

Local virtualenvs `edukoreaiapi/apivenv/` and `edukoreaiui/uivenv/` exist in the working tree (gitignored); ignore them when searching.

### Tests

API tests are plain Python scripts without pytest configuration:

```bash
cd edukoreaiapi
python tests/test_mongodb_connection.py
python tests/test_scanned_chapter.py
```

These need a live MongoDB (`MONGO_URI`) and, for the scan test, a configured OCR/LLM provider. Run from `edukoreaiapi/` so `config`/`database` imports resolve. `fix_indexes.py` is a one-off maintenance script that rebuilds the `users` collection's partial unique indexes (username/email/mobile); it is not run automatically.

No UI tests exist. No linting configuration in either project.

## edukoreaiapi Architecture

### Core Components

**`main.py`**  
FastAPI application entry point. Sets up CORS from config, includes the auth, ebooks and menus routers, and preloads the OCR engine via a lifespan context manager. Exposes `/health` for readiness checks.

**`config/config.py`**  
Loads all settings from `.env` via python-dotenv. Key sections:
- `MONGO_URI`, `DB_NAME`, `DB_CONNECTION_TIMEOUT` — MongoDB connection
- `OCR_ENGINE` — Choose `easyocr` or `llm_vision` (vision-based OCR via LLM)
- `LLM_PROVIDER` — Choose `claude`, `openai`, `gemini`, or `ollama`; each provider has its own key/model config
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_OAUTH_SCOPES` — Google sign-in
- Validation: `PASSWORD_MIN_LENGTH`, `EMAIL_PATTERN`, `MOBILE_PATTERN` (usernames must be an email or mobile number)
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
- `POST /login`, `POST /signup`, `POST /forgot-password`, `GET /users/{user_id}` — delegates to `database/db.py`
- `POST /google-callback?code=...` — backend exchanges the OAuth auth code (needs the client secret, so this must stay server-side), verifies the ID token via `services/google_oauth_service.py`, then creates/links the user with `login_or_create_google_user()`
- `POST /google-login` — verifies an already-obtained Google token
- Business failures are returned as `{"success": false, "error": ...}` bodies rather than HTTP errors. There are no session tokens/JWTs; the UI just keeps the returned user.

**`routers/menus.py`** (`/api/menus`)  
`GET ""` reads the `menus` Mongo collection and groups items by `panel`, ordered by `order`. Drives the home screen's menu panels.

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

**Google OAuth (desktop flow)**  
`services/oauth_flow.py` opens the system browser at Google's consent URL; `services/oauth_server.py` runs a throwaway local HTTP server on `GOOGLE_OAUTH_PORT` (default 8080, must differ from `WEB_PORT`) to catch the `/callback?code=...` redirect. The UI then sends the code to the backend's `/api/auth/google-callback` via `api_client.py`. `GOOGLE_CLIENT_ID` must match on both sides; the client secret lives only in the API.

### Configuration

**`config/config.py`**  
Loads `.env`:
- `API_BASE_URL` — backend base URL (default `http://localhost:8000`)
- `APP_TITLE`, `THEME_COLOR`, `BACKGROUND_COLOR`, `WINDOW_WIDTH/HEIGHT/RESIZABLE` — UI styling
- `UI_MODE`, `WEB_PORT`, `GOOGLE_CLIENT_ID`, `GOOGLE_OAUTH_PORT`, `GOOGLE_OAUTH_SCOPES`

**`resources/`** and **`fonts/`**  
- Logo: `edukoreai-logo.ico` (`APP_LOGO`, also used by `pyproject.toml`)
- Font: `Cambria Regular.ttf` (registered as `page.fonts["Cambria Regular"]`)

## Deployment

- **API** — `edukoreaiapi/Dockerfile` (python:3.12-slim, uvicorn on `$PORT`, default 8080). `.github/workflows/deploy.yml` (manual `workflow_dispatch`) builds and deploys to Cloud Run (`edukoreai` project, `asia-south1`) via Workload Identity Federation. It only injects `MONGO_URI`, `DB_NAME`, `DB_CONNECTION_TIMEOUT`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `CORS_ORIGINS`; any new env var the API needs in production (e.g. the Google OAuth credentials) must be added to that workflow's `env_vars` and the repo secrets.
- **UI** — `edukoreaiui/.github/workflows/build-apk.yml` (manual) builds an Android APK via Flet/Flutter; set `API_BASE_URL` to the deployed Cloud Run URL for such builds.

## API Contract Between Projects

Any change to a backend router endpoint path, method, or request/response schema **must be mirrored** in `edukoreaiui/services/api_client.py`. There is no shared type system between the projects — they do not import each other's schemas. Keep them in sync manually.

Current endpoints:
- `/api/auth/*` (login, signup, forgot-password, users/{id}, google-callback, google-login)
- `/api/menus`
- `/api/ebooks/*` (classes, subjects, chapters, scan, generate-questions, upload-questions, save-uploaded-questions, question-versions, generate-questions/document)

## Known Issues & Oddities

- `edukoreaiui/README.md` is outdated (describes old direct-MongoDB architecture). Use this CLAUDE.md instead.
- No test files in `edukoreaiui/` — only backend has tests, and they are plain scripts without pytest configuration.
- No linting or formatting configuration (black, ruff, flake8, etc.) in either project.
