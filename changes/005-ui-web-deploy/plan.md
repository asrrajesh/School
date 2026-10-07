# Plan: Deploy the UI as a web application on Cloud Run

- **Intent:** [intent.md](intent.md)
- **Spec:** [spec.md](spec.md)
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** approved

## Approach
Add the three new files (Dockerfile, `.dockerignore`, workflow) modeled on the API's, with no change to `main.py`, since Flet reads `FLET_SERVER_IP` and `FLET_SERVER_PORT` from the environment. Before writing the workflow, prove locally that the Flet env variables really make the server listen where the Dockerfile says, because Docker is not available here. Then update the docs that list the workflows.

## Files affected
| File | Change | Why |
|---|---|---|
| `edukoreaiui/Dockerfile` | New: python:3.12-slim, requirements + `flet-web==0.86.5`, `UI_MODE=web`, `FLET_SERVER_IP=0.0.0.0`, CMD sets `FLET_SERVER_PORT` from `$PORT` | Req 1, 3 |
| `edukoreaiui/.dockerignore` | New: `.env`, `uivenv/`, `__pycache__/`, `*.pyc`, `build/`, `.github/`, `.git/` | Req 2 |
| `.github/workflows/deploy-ui-web.yml` | New, copied from `deploy-api.yml` with UI names, build path, `flags`, `env_vars` | Req 4, 5 |
| `CLAUDE.md` (Architecture, Deploy line 37; Common mistakes line 59) | Mention the new workflow and that a new UI env var goes into its `env_vars` and repo variables | Req 7 |
| `README.md` (Deployment, lines 66-67) | Add the UI web service next to the API and APK entries | Req 7 |
| `knowledge/nfr.md`, `knowledge/ui-behavior-and-design.md` | Not in this stage; updated by `/update-knowledge` | Req 7 |

No change to `main.py`, `config/config.py`, `requirements.txt`, `deploy-api.yml`, `build-apk.yml`, the API or the skills.

## Steps
1. **Prove the Flet env behavior locally** (no file change). From `edukoreaiui/` with the existing venv, run `FLET_FORCE_WEB_SERVER=true UI_MODE=web FLET_SERVER_IP=0.0.0.0 FLET_SERVER_PORT=18550 python main.py` in the background (the force flag simulates a headless Linux container, so no browser opens), then fetch `http://127.0.0.1:18550/` and check which address the port is bound to; stop the process afterwards. Serves req 1 and 3.
   - **Proof:** HTTP 200 on port 18550 (not 8550), the listener is bound to `0.0.0.0`, and no browser window opened. If it listens on the wrong port or only on 127.0.0.1, stop and raise a departure (fall back to a small `main.py` change via `/update-plan`).
2. **Write `edukoreaiui/Dockerfile` and `edukoreaiui/.dockerignore`** as in the table. Serves req 1 and 2.
   - **Proof:** `grep` shows `python:3.12-slim`, `flet-web==0.86.5`, `UI_MODE=web`, `FLET_SERVER_IP=0.0.0.0`, `FLET_SERVER_PORT=${PORT:-8080}`, `EXPOSE 8080`; `.dockerignore` contains `.env`, `uivenv/`, `__pycache__/`; `git status` confirms `.env` is not tracked.
3. **Write `.github/workflows/deploy-ui-web.yml`:** copy `deploy-api.yml`, then change `name` (Deploy UI (web) to Cloud Run), `SERVICE`, `REPOSITORY`, `IMAGE` (to `edukoreaiui`), the build line (`docker build -t ... edukoreaiui`), `flags` (`--allow-unauthenticated --port=8080 --session-affinity --timeout=3600`) and `env_vars` (`UI_MODE=web`, `API_BASE_URL`, `APP_TITLE`, `THEME_COLOR`, `BACKGROUND_COLOR` from `vars`). Keep triggers, `environment: PROD`, permissions and the auth steps. Serves req 4 and 5.
   - **Proof:** a script parses the file with PyYAML (scratchpad) and compares it with `deploy-api.yml`: identical except the name, env names, build line, `flags` and `env_vars`; `secrets.*`/`vars.*` references are exactly `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`, `API_BASE_URL`, `APP_TITLE`, `THEME_COLOR`, `BACKGROUND_COLOR`.
4. **Update `CLAUDE.md` and `README.md`** to mention `.github/workflows/deploy-ui-web.yml` with the API and APK workflows, including the one-time setup (Artifact Registry repo `edukoreaiui`, repo variable `API_BASE_URL`). Serves req 7.
   - **Proof:** `grep -n deploy-ui-web CLAUDE.md README.md` shows the new entries; no other lines changed (`git diff --stat`).
5. **Run the guard checks:** `python .claude/hooks/test_guards.py` (0 failures) and `python .claude/skills/api-contract/scripts/check_endpoints.py` (OK). Confirm `git diff` touches no file outside the table.
6. **Hand over the manual verification.** The developer creates the Artifact Registry repo `edukoreaiui` and the `API_BASE_URL` variable, then after the merge to `main` runs **Deploy UI (web) to Cloud Run**, opens the URL and logs in (spec Verification). Serves req 6. Not run here; the implementation log says so.

## Risks
- **What could break:**
  - Flet might not honor the env variables the way the installed source suggests, or the container may need the web client assets in a different place; the local simulation in step 1 covers the first, the real run the rest.
  - `flet-web==0.86.5` must match `flet==0.86.5`; a mismatch would trigger Flet's runtime reinstall.
  - A missing Artifact Registry repo or empty `API_BASE_URL` makes the first run fail or the app unusable.
  - A hosted session with several instances can lose its in-memory state (known, flagged in the spec).
  - The font loaded from a local path, and file download/upload, may behave differently in a browser.
- **Riskiest step:** step 3 and step 6 together. Nothing here builds or runs the image (no Docker), so only the real workflow run proves the Dockerfile and the Cloud Run settings.

## Alternatives considered
- A `main.py` change to bind `0.0.0.0` and read `$PORT`: rejected for now, since Flet's own environment variables do it without touching app code; kept as the fallback.
- Adding `flet-web` to `requirements.txt`: rejected, the APK build also installs that file and does not need the web server package.
- Reusing the API's Artifact Registry repo: rejected by the assumption in the spec, a separate repo keeps the images apart.

## Rollback
`git revert` the `impl(005)` commit (removes the three new files and the doc lines). The workflow is manual and nothing is deployed by this stage; a deployed `edukoreaiui` Cloud Run service, if the developer ran it, is deleted in the Cloud Run console.

## Open questions
1. None new. The spec's open questions (new `edukoreaiui` repo, public service, no instance cap) are assumed as stated there.

## Implementation log
- **Step 1:** done. Local simulation from `edukoreaiui/` with `FLET_FORCE_WEB_SERVER=true UI_MODE=web FLET_SERVER_IP=0.0.0.0 FLET_SERVER_PORT=18550 python main.py`: HTTP 200 on `http://127.0.0.1:18550/`, no response on 8550, `netstat` shows the listener on `0.0.0.0:18550`, and no browser opened. The process was stopped afterwards. This confirms Flet 0.86.5 honors both variables. Note: on this Windows machine the force flag stands in for the container's headless Linux detection.
- **Step 2:** done. `edukoreaiui/Dockerfile` and `edukoreaiui/.dockerignore` written. Proof: grep finds `python:3.12-slim`, `flet-web==0.86.5`, `UI_MODE=web`, `FLET_SERVER_IP=0.0.0.0`, the CMD `FLET_SERVER_PORT=${PORT:-8080} exec python main.py` and `EXPOSE 8080`; `sh -c 'FLET_SERVER_PORT=${PORT:-8080} exec env'` passes 8080 by default and 9999 when `PORT=9999`; `.dockerignore` lists `.env`, `uivenv/`, `__pycache__/`; `edukoreaiui/.env` is untracked and gitignored.
- **Step 3:** done. `.github/workflows/deploy-ui-web.yml` copied from `deploy-api.yml`. Proof: a diff against `deploy-api.yml` shows only the name, header comment, `SERVICE`/`REPOSITORY`/`IMAGE`, the build path, `flags` (`--allow-unauthenticated --port=8080 --session-affinity --timeout=3600`) and `env_vars` (`UI_MODE=web`, `API_BASE_URL`, `APP_TITLE`, `THEME_COLOR`, `BACKGROUND_COLOR`); the file parses; triggers (`workflow_dispatch`), `environment: PROD` and permissions are unchanged; references are exactly `secrets.WIF_PROVIDER`, `secrets.WIF_SERVICE_ACCOUNT`, `vars.API_BASE_URL`, `vars.APP_TITLE`, `vars.THEME_COLOR`, `vars.BACKGROUND_COLOR`.
- **Step 4:** done. `CLAUDE.md` (Deploy line and the env-var mistake line) and `README.md` (Deployment, new UI web entry with the one-time setup) mention `deploy-ui-web.yml`. Proof: `grep` shows the entries; `git diff --stat` shows only those two files changed (3 insertions, 2 deletions).
- **Step 5:** done. `python .claude/hooks/test_guards.py` reports 0 failures; `check_endpoints.py` reports OK (18 endpoints, 17 client calls, 1 allowlisted); no file outside the plan's table changed (`main.py`, `config.py`, `requirements.txt`, other workflows and the API are untouched).
- **Step 6:** not run here. The developer creates the Artifact Registry repo `edukoreaiui` and the `API_BASE_URL` variable, then runs **Deploy UI (web) to Cloud Run** after the merge to `main`, opens the URL and logs in.
- **Departures:** none.
- **Unverified overall:** the Docker image build and container start (no Docker on this machine), the websocket and session-affinity behavior on Cloud Run, login against the deployed API, the custom font and the file download/upload in a hosted browser.
