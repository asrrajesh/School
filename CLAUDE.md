# CLAUDE.md

Two independent Python apps that talk only over HTTP (no shared code):

- `edukoreaiapi/` — FastAPI backend: auth (password + Google OAuth), eBook OCR, AI question generation, `.docx` export
- `edukoreaiui/` — Flet (Flutter-based) desktop/web/Android client; calls the API only through `services/api_client.py`

`designsamples/` is static HTML mockups. Ignore the gitignored venvs `edukoreaiapi/apivenv/` and `edukoreaiui/uivenv/` when searching.

## Commands

```bash
# API (http://localhost:8000, /health for readiness)
cd edukoreaiapi && pip install -r requirements.txt && cp .env.example .env && python main.py
# UI (needs API_BASE_URL in .env)
cd edukoreaiui && pip install -r requirements.txt && cp .env.example .env && python main.py
# API tests: plain scripts, need live MongoDB (and an OCR/LLM provider for the scan test). Run from edukoreaiapi/
python tests/test_mongodb_connection.py
python tests/test_scanned_chapter.py
```

No UI tests and no lint/format config in either project. `fix_indexes.py` is a one-off script that rebuilds the `users` partial unique indexes; never run automatically.

## Conventions

- **Read `knowledge/` before changing behavior.** It is the as-is documentation: `functional-specification`, `data-model`, `api-specification`, `prompt-and-generation-rule`, `ui-behavior-and-design`, `nfr`. Keep it a current-state snapshot, not a changelog.
- **Providers:** LLM (`llm/factory.py`, `LLM_PROVIDER`: claude/openai/gemini/ollama) and OCR (`ocr/factory.py`, `OCR_ENGINE`: easyocr/llm_vision). A new provider implements the base interface and is registered in its factory. Never hardcode provider logic at call sites.
- **API contract:** any change to an endpoint path, method or request/response schema must be mirrored in `edukoreaiui/services/api_client.py`. Screens never call httpx directly.
- **API errors:** business failures return `{"success": false, "error": ...}` bodies, not HTTP errors. No JWTs/sessions; the UI keeps the returned user.
- **Google OAuth:** the code exchange needs the client secret, so it stays server-side (`/api/auth/google-callback`). `GOOGLE_CLIENT_ID` must match in both apps; `GOOGLE_OAUTH_PORT` (8080) must differ from `WEB_PORT` (8550).
- **Screens:** each `screens/*.py` exports `*_view(page)`; authenticated screens are wrapped by `components/app_frame.py` `with_app_frame()`.

## Architecture

- API: `main.py` (app, CORS, OCR preload) → `routers/{auth,ebooks,menus}.py` → `services/` (`ocr_service`, `question_service`, `paper_generator`, `google_oauth_service`) → provider factories and `database/db.py` (pymongo, bcrypt). Models in `schemas.py`, settings in `config/config.py`.
- UI: `main.py` (routing via `page.on_route_change`) → `screens/` → `services/api_client.py`. Settings in `config/config.py`.
- Deploy: API via `edukoreaiapi/Dockerfile` and `edukoreaiapi/.github/workflows/deploy.yml` (Cloud Run, manual). **Any new production env var must be added to that workflow's `env_vars` and the repo secrets.** UI APK via `edukoreaiui/.github/workflows/build-apk.yml`; set `API_BASE_URL` to the Cloud Run URL.

## Feature workflow

Each change lives in `changes/<id>-<short-desc>/` and moves through: `/create-intent <requirements>` → `intent.md`; `/create-spec <id>` → `spec.md`; `/create-plan <id>` → `plan.md`; implement; `/update-knowledge <path to intent.md>`. Revise with `/update-intent`, `/update-spec`, `/update-plan <id> <changes>`. Each file has a status (`draft` → `approved` → `implemented`).

Branches: `main` (release; the user merges `develop` into it and tags manually) and `develop` (integration) are fixed and never deleted or committed to directly. `/create-intent` creates `develop-<id>-<short-desc>` from `develop` (for example `develop-001-ui-not-launching`); every stage is committed on that branch as `<stage>(<id>): summary` with stages `intent`, `spec`, `plan`, `impl`, `knowledge`. Implementation has no skill: commit it as `impl(<id>): ...`, and run `/update-plan` if the work departs from the plan. Always ask the user before committing and again before pushing; never force-push. Finish with a PR from the change branch into `develop`.

## Skills

Workflow skills (`/create-intent` etc.) are manual slash commands. Policy skills (`api-contract`, `security-rules`, `ui-conventions`, `llm-provider-rules`) load automatically when a task matches their description. See `.claude/skills/README.md`; the repo owner approves skill changes.

## Common mistakes

When a mistake happens twice, add it here.

- Building `pydantic-core` on Python 3.14 fails (no wheel, Rust build blocked by Windows Application Control, error 4551). Use Python 3.13 or 3.12 (the Dockerfile uses 3.12).
- The Flet desktop client can be blocked by Windows code integrity / Smart App Control and exit silently. Set `UI_MODE=web` in `edukoreaiui/.env`. See `changes/001-ui-not-launching/`.
- Changing an endpoint without updating `api_client.py`, or adding an API env var without updating `deploy.yml`.
