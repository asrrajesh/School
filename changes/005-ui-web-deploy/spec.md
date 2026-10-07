# Spec: Deploy the UI as a web application on Cloud Run

- **Intent:** [intent.md](intent.md)
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** implemented (2026-10-07)

## Summary
Add a Dockerfile and `.dockerignore` for the Flet UI and a third manual workflow, `.github/workflows/deploy-ui-web.yml`, that builds the image, pushes it to Artifact Registry and deploys it as a Cloud Run service. In the container Flet is told where to listen through environment variables, so `main.py` stays unchanged.

## Findings
- `edukoreaiui/main.py:139-141`: web mode runs `ft.run(main, view=ft.AppView.WEB_BROWSER, port=WEB_PORT)` with no `host`. `WEB_PORT` defaults to 8550 (`config/config.py:71`). `UI_MODE` defaults to `desktop` (`config.py:69`).
- Flet 0.86.5 (`flet/app.py`, `run_async`, read from the installed package): on a headless Linux machine (no `DISPLAY`, not WSL; `is_linux_server()`) Flet forces its web server and never opens a browser. It also reads `FLET_SERVER_PORT` (overrides the `port` argument) and `FLET_SERVER_IP` (overrides `host`). With no host set, `url_host` is `127.0.0.1` and the server would not accept outside traffic, so the container must set `FLET_SERVER_IP=0.0.0.0`.
- `pip install flet==0.86.5` does not include the web server package: `flet-web` is an optional extra (`Requires-Dist: flet-web==0.86.5; extra == "web"`), and `requirements.txt` only has `flet==0.86.5`. If it is missing, `ensure_flet_web_package_installed()` pip-installs it at startup, which would run at every cold start, so the image should install it at build time.
- The UI's HTTP calls to the API are made by the UI's Python process through `services/api_client.py` (httpx), not by the browser. CORS therefore does not apply to this deployment, so the intent's remark about the API's CORS is harmless but not needed.
- `API_BASE_URL`, `APP_TITLE`, `THEME_COLOR`, `BACKGROUND_COLOR` are read from the environment with `os.getenv(key, default)` (`config.py:42-51,60`), so an empty variable overrides the default with an empty string.
- `.github/workflows/build-apk.yml` already reads `vars.API_BASE_URL`, `APP_TITLE`, `THEME_COLOR`, `WINDOW_*` and `BACKGROUND_COLOR`, and its last run succeeded; `.github/workflows/deploy-api.yml` is the pattern for the Workload Identity login, `PROD` environment, build, push and deploy.
- `edukoreaiui/` has no Dockerfile or `.dockerignore`; the gitignored `.env` and `uivenv/` live there. The app loads its font from a filesystem path (`main.py:30-31`), which a hosted web session may not be able to fetch (the same already applies to local web mode).
- Docker is not installed on this machine, so the image cannot be built or run here.
- Not verifiable here: the image build, the container start, the websocket behavior on Cloud Run, and login against the deployed API. These need the real workflow run.

## Requirements
1. `edukoreaiui/Dockerfile` builds an image based on Python 3.12 that installs `requirements.txt` plus `flet-web==0.86.5`, copies the app, sets `UI_MODE=web` and `FLET_SERVER_IP=0.0.0.0`, and starts `python main.py` with `FLET_SERVER_PORT` set from `$PORT` (default 8080).
2. `edukoreaiui/.dockerignore` excludes `.env`, `uivenv/`, `__pycache__/`, `*.pyc`, `build/`, `.github/` and `.git/`, so no secrets or local environments enter the image.
3. `edukoreaiui/main.py` and the desktop/local-web behavior are unchanged.
4. `.github/workflows/deploy-ui-web.yml` is manual (`workflow_dispatch`) and follows `deploy-api.yml`: same Workload Identity login and `PROD` environment, builds from `edukoreaiui`, pushes to Artifact Registry repo `edukoreaiui`, and deploys the Cloud Run service `edukoreaiui` in `asia-south1` with `--allow-unauthenticated --port=8080 --session-affinity --timeout=3600`.
5. The service's env vars come from repo variables only: `API_BASE_URL`, `APP_TITLE`, `THEME_COLOR`, `BACKGROUND_COLOR` (and `UI_MODE=web` as a fixed value). No secrets are used or baked in.
6. After a manual run, the service URL serves the login page, and logging in works against the deployed API.
7. `CLAUDE.md`, `README.md` and `knowledge/nfr.md` (and the platforms line of `knowledge/ui-behavior-and-design.md`) describe the new workflow; the old paths and the other workflows are untouched.

## Design
- **Dockerfile** (`python:3.12-slim`): `WORKDIR /app`; copy `requirements.txt`, `pip install --no-cache-dir -r requirements.txt flet-web==0.86.5`; `COPY . .`; `ENV PYTHONUNBUFFERED=1 UI_MODE=web FLET_SERVER_IP=0.0.0.0`; `EXPOSE 8080`; `CMD ["sh", "-c", "FLET_SERVER_PORT=${PORT:-8080} exec python main.py"]`. This mirrors the API's Dockerfile and uses Flet's own environment variables, so `main.py` needs no code change. If the first run shows that these variables do not take effect, a small `main.py` change is the fallback, handled through `/update-plan`.
- **Workflow:** copy the shape of `deploy-api.yml` with `SERVICE: edukoreaiui`, `REPOSITORY: edukoreaiui`, `IMAGE: asia-south1-docker.pkg.dev/edukoreai/edukoreaiui/edukoreaiui`, the build step `docker build -t ... edukoreaiui`, and `env_vars` of `UI_MODE=web`, `API_BASE_URL=${{ vars.API_BASE_URL }}`, `APP_TITLE`, `THEME_COLOR`, `BACKGROUND_COLOR` from `vars`. Memory is left at the default; raise it only if the first deploy shows it is needed (the API's torch load was the reason in change 004).
- **One-time GCP/GitHub setup (developer):** create the Artifact Registry Docker repo `edukoreaiui` in `asia-south1`; the existing deployer service account already has Artifact Registry write and Cloud Run admin; set the repo variable `API_BASE_URL` to the API's Cloud Run URL (the others already exist for the APK build).
- **Docs:** new workflow added next to the other two in `CLAUDE.md` (Architecture, Deploy), `README.md` (Deployment) and `knowledge/nfr.md` (section 7 and the UI platform note); `knowledge/ui-behavior-and-design.md` gets the browser-hosted platform mention.

## Out of scope / must not change
- Google sign-in on the hosted web app (needs the local loopback port `GOOGLE_OAUTH_PORT`), a custom domain, a PR CI check, a post-deploy health check, and any change to the API, `api_client.py` or the APK build.
- `main.py`, screens, `config/config.py`, `requirements.txt`, `deploy-api.yml` and `build-apk.yml`.

## Verification
- Static (Claude): `deploy-ui-web.yml` parses; compared with `deploy-api.yml` the only differences are the service, repository and image names, the build path, the `flags`, and the `env_vars` block; the `vars.*`/`secrets.*` references are exactly `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT` and the four UI variables; the Dockerfile and `.dockerignore` contain the lines above; `git status` shows no change to other workflows or app code; `python .claude/hooks/test_guards.py` reports 0 failures; the docs mention `deploy-ui-web.yml` where the other two workflows are listed.
- Manual (developer, after the merge to `main`): create the Artifact Registry repo and the `API_BASE_URL` variable; run **Deploy UI (web) to Cloud Run**; open the service URL; expect the login page, then log in and open Home and a screen that calls the API; check the revision logs if it fails.
- Not verifiable here: the image build and run (no Docker), the websocket behavior on Cloud Run, the custom font in the hosted browser, and the question-paper download on a hosted web session.

## Flagged concerns
- **Session state:** a Flet session lives in the memory of one instance. `--session-affinity` helps but does not guarantee the same instance after a scale-out or restart, in which case a user's session resets. Capping instances (`--max-instances=1`) would avoid it but is not requested; left as a follow-up decision.
- **Empty variables:** a missing or empty `API_BASE_URL` repo variable gives the UI an empty base URL and every call fails. The workflow should not hide this; the developer must set the variable before the first run.
- **Features that use files:** the question-paper download (`FilePicker.save_file`) and image upload on a hosted browser session may behave differently from desktop; not checked in this change.
- **Font:** `Cambria Regular` is loaded from a local path and may fall back to a default font in the hosted browser.
- **Cost and exposure:** the service is public like the API and bills only while running; the UI has no login protection beyond the app's own login.

## Open questions
1. Artifact Registry repo: new `edukoreaiui` (assumed, created by the developer before the first run).
2. Cloud Run `--allow-unauthenticated` for the UI (assumed yes), consistent with the intent.
3. Whether to cap instances for session safety (assumed no, session affinity only, as the intent says).
