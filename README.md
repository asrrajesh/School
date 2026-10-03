# EduKoreAI

EduKoreAI helps school staff build assessment papers. Textbook pages are scanned into chapter text, and an LLM generates structured questions from it, or extracts questions from a scanned existing paper. Results are versioned and can be downloaded as a Word (`.docx`) document.

## Repository layout

| Folder | What it is |
|---|---|
| `edukoreaiapi/` | FastAPI backend: authentication (password and Google OAuth), OCR, AI question generation, `.docx` export. Uses MongoDB. |
| `edukoreaiui/` | Flet client (desktop, browser, Android) that calls the backend over HTTP. |
| `knowledge/` | Current-state documentation of the application (functional spec, data model, API, prompts, UI, NFRs). |
| `changes/` | One folder per change with `intent.md`, `spec.md` and `plan.md`. |
| `designsamples/` | Static HTML design mockups. |

The two apps share no code; they communicate only through the REST API.

## Prerequisites

- Python 3.12 or 3.13. Python 3.14 is not recommended: some dependencies (such as `pydantic-core`) have no prebuilt wheels and fail to build on Windows.
- A MongoDB instance.
- An LLM provider key (Claude, OpenAI, Gemini, or a local Ollama) for question generation, and optionally Google OAuth credentials for Google sign-in.

## Run the API

```bash
cd edukoreaiapi
python -m venv apivenv
# activate the venv, then:
pip install -r requirements.txt
cp .env.example .env   # fill in MONGO_URI, LLM provider settings, etc.
python main.py
```

The API listens on http://localhost:8000. `GET /health` reports readiness.

## Run the UI

```bash
cd edukoreaiui
python -m venv uivenv
# activate the venv, then:
pip install -r requirements.txt
cp .env.example .env   # set API_BASE_URL (default http://localhost:8000)
python main.py
```

`UI_MODE=desktop` opens a native window; `UI_MODE=web` opens the browser on `WEB_PORT` (default 8550). Use `web` if Windows Smart App Control blocks the desktop client.

## Tests

The API tests are plain scripts that need a live MongoDB. Run them from `edukoreaiapi/`:

```bash
python tests/test_mongodb_connection.py
python tests/test_scanned_chapter.py
```

There are no UI tests.

## Configuration

Settings are read from each app's `.env` file. See `edukoreaiapi/.env.example` and `edukoreaiui/.env.example` for every option, including `LLM_PROVIDER`, `OCR_ENGINE`, and the Google OAuth settings. Never commit `.env` files.

## Deployment

- **API:** `edukoreaiapi/Dockerfile` and the manual GitHub Actions workflow `.github/workflows/deploy.yml` deploy to Google Cloud Run. Any new production environment variable must be added to that workflow and the repository secrets.
- **Android APK:** `edukoreaiui/.github/workflows/build-apk.yml` (manual). Set `API_BASE_URL` to the deployed API URL for such builds.

## Working on this project

Read the relevant file in `knowledge/` before changing behavior. New work follows the flow documented in [CLAUDE.md](CLAUDE.md): intent, spec, plan, implement, then update knowledge.
