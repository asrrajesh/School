# Non-Functional Requirements (current state)

> Last synced 2026-10-05 (git `7ff2ee4`). Records what the code and deployment files **do today** (qualities, constraints, gaps). It does not set targets. Where no behavior exists, the entry says so.

## 1. Security

**Implemented**
- Passwords are hashed with bcrypt (random salt) and never returned by the API.
- Google sign-in: the authorization-code exchange and the client secret stay on the server; the ID token is verified with `google-auth` against `GOOGLE_CLIENT_ID` (10 s clock-skew tolerance).
- Input validation: username must match the email or mobile pattern; password minimum length (`PASSWORD_MIN_LENGTH`, default 8); `complexity` is restricted to three values by the request model.
- Secrets come from environment/`.env` (`MONGO_URI`, provider API keys, `GOOGLE_CLIENT_SECRET`); `.env` is gitignored. In production only `MONGO_URI`, `DB_NAME`, `DB_CONNECTION_TIMEOUT`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` and `CORS_ORIGINS` are injected by the workflow.

**Gaps (as-is)**
1. **No API authentication or authorization.** Endpoints accept any caller. `GET /api/auth/users/{id}` returns a user's email, mobile and name for any id. Actions are attributed to a client-supplied `username`.
2. **No sessions or tokens.** The UI keeps the user id in memory only; Logout does not clear it.
3. **CORS defaults to `*`** with credentials allowed; the Cloud Run deploy uses `--allow-unauthenticated`.
4. **Developer test credentials are pre-filled in the login form** (`login_screen.py`) and committed to the repo.
5. No rate limiting or lockout on login, signup or the LLM-backed endpoints (each generation or scan call costs money).
6. Google flow: no CSRF `state` parameter and no PKCE in the browser redirect; the token-exchange `redirect_uri` is hardcoded to `http://localhost:8080/callback`.
7. Forgot-password is a stub (no email or SMS), so there is no account-recovery path.
8. Debug `print` output to stderr in the Google flow includes the client ID and user email.
9. Uploaded images and extracted text are processed in memory with no size or type limits; text is sent to the configured third-party LLM.
10. Google-only users have no `password` field; a password login attempt fails with a raw error string.

## 2. Data privacy
- Personal data stored: email, mobile, Google subject ID, bcrypt hash, name (never written).
- Chapter text and uploaded question papers (possibly copyrighted textbook content) are sent to the selected LLM provider. With `OCR_ENGINE=easyocr` the image step stays local.
- No data retention, deletion or export features, and no consent handling.

## 3. Performance and timeouts
- UI → API timeouts: 30 s default, 120 s generate and save-uploaded, 300 s scan and upload.
- OCR (EasyOCR) models load at API start (startup cost; first request avoids it). EasyOCR installs torch, OpenCV and related packages (heavy).
- LLM calls are synchronous (blocking). FastAPI runs sync route functions in a thread pool; there is no queue, streaming, caching or background job, so a long generation holds a worker.
- `max_tokens` is fixed at 4096 for generation, extraction and vision OCR.
- MongoDB: `questions` and `scanned_chapters` have no indexes beyond `_id`, so lookups scan the collection. Fine at small scale only.
- Pymongo client is created once per process (lazy singleton).

## 4. Reliability and error handling
- Business errors are returned as `{success:false, error}` with HTTP 200; a broad `except Exception` converts most failures to that form, so errors can be hidden from HTTP-level monitoring.
- DB connection failures return a friendly "Cannot connect to database" message for most calls; read helpers (`get_scanned_*`, versions) return empty results on any error, which hides outages.
- LLM failures are mapped to typed exceptions (authentication, permission, connection, response) and surfaced as an error string. Malformed JSON from the model fails the whole request; there is no retry.
- Version numbers are computed with read-then-insert, so concurrent saves for the same paper can create duplicate versions.
- No health check of dependencies: `/health` returns ok without touching MongoDB or the LLM.

## 5. Observability
- No structured logging, metrics or tracing. Only ad-hoc `print` debug lines (mostly in the Google flow). Cloud Run's default request logs apply in production.

## 6. Configuration
- All settings from environment via python-dotenv (`override=True`, so `.env` beats the shell). Keys are documented in each project's `.env.example`.
- Provider choice is configuration only: `LLM_PROVIDER` (claude, openai, gemini, ollama) and `OCR_ENGINE` (easyocr, llm_vision). `LLM_MAX_TOKENS` and `LLM_TEMPERATURE` exist but are not applied to question generation.

## 7. Deployment and operations
- **API:** `edukoreaiapi/Dockerfile` (python:3.12-slim, `uvicorn main:app` on `$PORT`, default 8080). `.github/workflows/deploy-api.yml` (repo root) is **manual** (`workflow_dispatch`): authenticates to Google Cloud via Workload Identity Federation, builds the image from `edukoreaiapi/` and pushes it to Artifact Registry (`asia-south1`), and deploys to Cloud Run service `edukoreaiapi` in project `edukoreai` with `--allow-unauthenticated --port=8080`. Environment name `PROD`; secrets `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`, `MONGO_URI`, `DB_NAME`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`; vars `DB_CONNECTION_TIMEOUT`, `CORS_ORIGINS`.
- **Not in the deploy workflow:** Google OAuth variables, `LLM_PROVIDER`, `OCR_ENGINE` and the other provider keys. In production the defaults apply (`LLM_PROVIDER=claude`, `OCR_ENGINE=easyocr`), and Google sign-in is not configured.
- The container image installs EasyOCR with its model downloads at runtime (size and cold-start impact not measured).
- **UI:** `.github/workflows/build-apk.yml` (repo root) is manual (release or debug), Python 3.12, Java 17, Flutter 3.44.8; builds an Android APK, running its install, `.env` creation and `flet build apk` steps in `edukoreaiui/`. `API_BASE_URL` must point to the deployed API.
- The UI's Google flow needs a free local port (`GOOGLE_OAUTH_PORT`, default 8080), which suits desktop but not the web or mobile builds.
- No database migrations, backups, or environment promotion process are defined in the repo. MongoDB hosting is external (`MONGO_URI`, for example Atlas).

## 8. Quality and maintainability
- Tests: two plain Python scripts for the API (`tests/test_mongodb_connection.py`, `tests/test_scanned_chapter.py`) that need live services; no UI tests; no CI test step.
- No linter or formatter configuration. Some dead or unused code (unused `/upload-questions` client path, stray imports, commented-out import in `routers/ebooks.py`).
- Architecture rules in use: LLM and OCR behind abstract providers with factories; UI talks to the API only through `api_client.py`; API contract mirrored manually.

## 9. Compatibility and platform
- Python 3.12 (container and CI). Pinned: FastAPI 0.115.6, pymongo 4.17.0, pydantic 2.10.4, anthropic 0.69.0, python-docx 1.1.2.
- UI: Flet; desktop window sized for phone (400 × 780), browser mode (`UI_MODE=web`) available when Windows Smart App Control / code integrity blocks the Flet desktop client (it blocked `media_kit_libs_windows_video_plugin.dll`, so the window never opens); at startup `main.py` prints the active mode and, on Windows desktop mode, a hint about this workaround, and reports and re-raises an exception from `ft.run`. A block inside the client process may still exit silently. Android APK via CI.
- Locale: OCR language list configurable (`OCR_LANGUAGES`, default `en`); UI text is English only.

## 10. Accessibility
- No explicit accessibility work (labels, contrast checks, screen-reader semantics) was found. Several controls are icon-only. Small text sizes are used in the bottom bar (8 px labels).
