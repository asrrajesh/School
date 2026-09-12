# Deployment & Infrastructure

## Overview

Everything the existing `knowledge/` docs assume is "already handled" —
Docker packaging, Cloud Run deployment, Android APK builds, and environment
configuration. None of it is documented outside scattered comments in the
workflow YAML files themselves.

**⚠️ Read the "Exposed Credential" section below before anything else in this
file — it needs action independent of any documentation work.**

---

## ⚠️ Exposed Credential — Action Needed

`edukoreaiapi/tests/test_mongodb_connection.py` contains a hardcoded MongoDB
Atlas connection string with a live-looking username and password:

```python
CONNECTION_STRING = "mongodb+srv://asrrajesh_db_user:Tdwhr20wZEg1dWXf@cluster0.citc42h.mongodb.net/?appName=Cluster0"
```

This is a real problem, independent of anything else in this document:

- **`.dockerignore` excludes `tests/`** from the Docker build, and
  **`.gitignore` excludes `.env`** — but neither ignores this specific file
  from version control. If this repo has ever been pushed to GitHub (public
  or private-but-widely-shared), this credential is in the git history now,
  and removing it from the current file won't remove it from history.
- The script also queries for a database named `"myschool"` (**lowercase**),
  which doesn't match `DB_NAME` used everywhere else in the app —
  `config.py` defaults to `"MySchool"` (mixed case). MongoDB database names
  are case-sensitive, so this test script is very likely checking the wrong
  database entirely, separate from the credential issue.

**Recommended immediate steps**, independent of any doc changes:
1. Rotate this credential in the MongoDB Atlas dashboard now.
2. Move the connection string into an environment variable
   (`os.getenv("MONGO_URI")`) the same way `database/db.py` does, rather than
   hardcoding it in a test file.
3. Add a check to prevent connection strings from being committed going
   forward (a pre-commit hook or a `git-secrets`-style scanner), since
   `.gitignore` alone didn't catch this one.
4. Fix or remove the `"myschool"` vs `"MySchool"` mismatch so the test
   actually checks the right database.

I haven't changed this file or the credential myself — flagging it is as far
as documentation can safely go. The rotation has to happen in Atlas directly.

---

## Docker (`edukoreaiapi/Dockerfile`)

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

Notes:
- Only the **backend** (`edukoreaiapi`) is containerized. `edukoreaiui` has
  no Dockerfile — it's built as a native app / APK instead (see below), not
  deployed as a container.
- The container listens on whatever `$PORT` Cloud Run injects, falling back
  to `8080` for local `docker run`. This is different from
  `edukoreaiapi/config/config.py`'s own `API_PORT` default of `8000` — that
  `8000`/`API_PORT` value only applies when running `python main.py`
  directly (see `if __name__ == "__main__"` in `main.py`, which reads
  `API_HOST`/`API_PORT` from config). Inside the Docker/Cloud Run path, the
  Dockerfile's `CMD` bypasses `main.py`'s `__main__` block entirely and
  drives uvicorn straight from the shell, so `API_PORT` has no effect there.
- `.dockerignore` excludes `.venv/`, `__pycache__/`, `*.pyc`, `.env`,
  `.git/`, `.github/`, and `tests/` — so test files (including the one with
  the exposed credential above) never end up inside built images, which is
  good, but doesn't help with the git-history exposure.

## Cloud Run Deployment (`.github/workflows/deploy.yml`)

Manually triggered (`workflow_dispatch`) GitHub Actions workflow. Per its own
inline comments, **one-time GCP setup is required before it can run**:

1. Enable APIs: `run.googleapis.com`, `artifactregistry.googleapis.com`,
   `iamcredentials.googleapis.com`
2. Create an Artifact Registry Docker repo named `edukoreaiapi` in the
   target region
3. Create a deployer service account + Workload Identity Federation pool/
   provider trusting this GitHub repo, granted `roles/run.admin`,
   `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser`
4. Add repo secrets: `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`, `MONGO_URI`,
   `DB_NAME`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`

Fixed values baked into the workflow's `env:` block:

```yaml
PROJECT_ID: edukoreai
REGION: asia-south1
SERVICE: edukoreaiapi
REPOSITORY: edukoreaiapi
IMAGE: asia-south1-docker.pkg.dev/edukoreai/edukoreaiapi/edukoreaiapi
```

Flow: authenticate via Workload Identity Federation (no long-lived key
file) → configure Docker for Artifact Registry → build & push image tagged
with the git SHA → `deploy-cloudrun@v2` with
`--allow-unauthenticated --port=8080` → prints the deployed URL.

Deployed env vars come from a mix of GitHub **secrets** (`MONGO_URI`,
`DB_NAME`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`) and **vars**
(`DB_CONNECTION_TIMEOUT`, `CORS_ORIGINS`) — worth knowing which is which if
you need to update one: secrets are set under repo Settings → Secrets,
vars under Settings → Variables, and they're not interchangeable in GitHub's
UI.

`--allow-unauthenticated` means the deployed API is public — anyone with the
URL can call every endpoint, including `/generate-questions` (which spends
Anthropic API credits) and the raw `/api/auth/*` routes. There's no API key,
IP allowlist, or auth layer in front of the FastAPI app itself in this
workflow.

## Android APK Build (`edukoreaiui/.github/workflows/build-apk.yml`)

Also `workflow_dispatch`-triggered, with a `build_mode` input
(`release`/`debug`, defaults to `release`).

Toolchain installed in the runner: Python 3.12, Java 17 (Temurin), Flutter
3.44.8 (Flet apps compile through Flutter under the hood), plus
`libgtk-3-dev`/`mesa-utils` for Flutter's Linux desktop checks and
`sdkmanager`/`flutter doctor --android-licenses` for the Android toolchain.

The `.env` file used for the build is generated **inline from repo
vars**, not secrets:

```yaml
- name: Create .env file from repo secrets/variables
  run: |
    cat <<EOF > .env
    API_BASE_URL=${{ vars.API_BASE_URL }}
    APP_TITLE=${{ vars.APP_TITLE }}
    THEME_COLOR=${{ vars.THEME_COLOR }}
    WINDOW_WIDTH=${{ vars.WINDOW_WIDTH }}
    WINDOW_HEIGHT=${{ vars.WINDOW_HEIGHT }}
    WINDOW_RESIZABLE=${{ vars.WINDOW_RESIZABLE }}
    BACKGROUND_COLOR=${{ vars.BACKGROUND_COLOR }}
    EOF
```

This means **`API_BASE_URL` must point at wherever the backend is actually
deployed** (e.g. the Cloud Run URL from the deploy workflow above) *before*
building the APK, or the built app will try to reach whatever's in that repo
variable — commonly a stale `localhost:8000` if it's never been updated
after the first setup. Since `config/config.py`'s
`load_dotenv(override=True)` call is wrapped in a try/except specifically
because "dotenv's stack-based file lookup can't work" in a packaged mobile
build (per the comment in that file), double-check this generated `.env`
actually gets bundled the way the source expects when troubleshooting a
built APK that can't reach the API.

Build command: `flet build apk --flutter-build-args=--{mode} --verbose --no-rich-output`.
The workflow then searches `build/apk` for the resulting `.apk` file and
fails explicitly (`if-no-files-found: error`) if none is found, uploading it
as a workflow artifact named `edukoreai-{mode}-apk`.

Two documented manual alternatives exist in `edukoreaiui/README.md` (not in
the workflow) — `flet build apk --release` run locally, or building directly
from the generated `flet_android_build/` Flutter project with
`flutter build apk --release`. Both are for local/manual builds outside CI.

---

## Environment Configuration Reference

Two separate `.env` files, one per project, each with its own `.env.example`.
Neither project shares environment variables with the other — they're
fully independent configs, connected only by `API_BASE_URL` pointing the UI
at wherever the API happens to be running.

### `edukoreaiapi/.env.example`

| Variable | Default (if unset) | Used by |
|---|---|---|
| `MONGO_URI` | *(blank — must be set)* | `database/db.py` |
| `DB_NAME` | `MySchool` | `database/db.py` |
| `DB_CONNECTION_TIMEOUT` | `5000` (ms) | `database/db.py` |
| `ANTHROPIC_API_KEY` | *(blank — must be set)* | `claude_ocr.py`, `claude_questions.py` |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | `claude_ocr.py`, `claude_questions.py` |
| `PASSWORD_MIN_LENGTH` | `8` | `database/db.py` signup validation |
| `EMAIL_PATTERN` | `^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$` | username validation |
| `MOBILE_PATTERN` | `^\+?[0-9]{10,15}$` | username validation |
| `API_HOST` | `0.0.0.0` | `main.py`, direct-run only |
| `API_PORT` | `8000` | `main.py`, direct-run only — **not used by the Docker/Cloud Run path**, see above |
| `CORS_ORIGINS` | `*` | `main.py` CORS middleware, comma-separated or `*` |

### `edukoreaiui/.env.example`

| Variable | Default (if unset) | Used by |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | `services/api_client.py` — every API call |
| `APP_TITLE` | `EduKoreAI` | `main.py` window title |
| `THEME_COLOR` | `#3949AB` | `main.py` theme seed color |
| `WINDOW_WIDTH` | `400` | `main.py` (desktop only, no effect in APK) |
| `WINDOW_HEIGHT` | `780` | `main.py` (desktop only) |
| `WINDOW_RESIZABLE` | `true` | `main.py` (desktop only) |
| `BACKGROUND_COLOR` | `#F5F5F5` | `main.py` page background |

Note the `edukoreaiui/README.md` also documents `SECONDARY_COLOR`,
`APP_VERSION`, `SESSION_TIMEOUT`, `MAX_LOGIN_ATTEMPTS`, `LOCKOUT_DURATION`,
and several `ENABLE_*` feature flags — **none of these appear in
`config/config.py`** as actual `os.getenv()` calls. They're documented in
the README as aspirational/planned settings, not currently wired to any
code. Don't expect setting them in `.env` to do anything yet.

---

## Package Manifests

| File | Key pins |
|---|---|
| `edukoreaiapi/requirements.txt` | `fastapi==0.115.6`, `uvicorn[standard]==0.34.0`, `pymongo==4.17.0`, `bcrypt==5.0.0`, `anthropic==0.69.0`, `pydantic==2.10.4`, `python-multipart==0.0.20` |
| `edukoreaiui/requirements.txt` | `flet==0.86.5`, `httpx==0.28.1`, `python-dotenv==1.2.3` |
| `edukoreaiui/pyproject.toml` | `[tool.flet] app_title = "My School Application"` |

Worth flagging: `pyproject.toml`'s `app_title` (`"My School Application"`)
does **not** match the `.env`-driven `APP_TITLE` default (`"EduKoreAI"`) used
by `main.py`, nor the app's actual name used everywhere else in code and
docs (`EduKoreAI`). It's unclear which one wins for a `flet build` — if the
built app's title looks wrong, this file is one place to check.

`python-multipart` is required specifically for the `/api/ebooks/scan`
endpoint's `UploadFile` handling — it's easy to forget this dependency if
someone strips down `requirements.txt` without realizing the image-upload
route needs it.

---

## Known Gaps / Follow-Up Candidates

1. **Rotate the exposed MongoDB credential** (see top of this document) —
   this is the highest-priority item in this entire file.
2. **No authentication in front of the public Cloud Run deployment** —
   `--allow-unauthenticated` plus no API-layer auth means the
   `/generate-questions` endpoint (which spends Anthropic credits) is
   callable by anyone with the URL.
3. **`app_title` mismatch** between `pyproject.toml` and `.env`/`main.py`.
4. **README-documented config that doesn't exist in code** — the
   `SESSION_TIMEOUT` / `MAX_LOGIN_ATTEMPTS` / `LOCKOUT_DURATION` /
   `ENABLE_*` flags in `edukoreaiui/README.md` should either be implemented
   or removed from the README so the docs stop overpromising.
5. **APK build's `API_BASE_URL`** needs an explicit, deliberate update in
   repo variables any time the backend's deployed URL changes — nothing
   automates keeping these two workflows in sync.
