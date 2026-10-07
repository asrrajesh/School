# Intent: Deploy the UI as a web application on Cloud Run

- **ID:** 005
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** approved
- **Type:** new feature

## Developer request
> Deploy the UI as a web application on Cloud Run, with its own workflow.
>
> Today the UI runs as a Flet web server only locally (UI_MODE=web, port from WEB_PORT, view=WEB_BROWSER) and as a desktop app or an Android APK. There is no Dockerfile for it and no workflow that deploys it.
>
> Scope:
> - Add edukoreaiui/Dockerfile (Python 3.12, installs requirements.txt, runs the Flet web server) and edukoreaiui/.dockerignore (exclude .env, venv, caches, build output).
> - Make the UI start correctly in a container: bind 0.0.0.0, use the port Cloud Run provides in $PORT, and do not try to open a browser. Desktop and local web behavior stay as they are.
> - Add .github/workflows/deploy-ui-web.yml as a third workflow next to deploy-api.yml and build-apk.yml: manual (workflow_dispatch), same Workload Identity Federation login and PROD environment, build from edukoreaiui/, push to Artifact Registry and deploy a Cloud Run service for the UI. API_BASE_URL (the Cloud Run API URL) and the other UI settings come in as env vars from repo variables; no secrets baked into the image.
> - Set what Cloud Run needs for a Flet websocket app (for example session affinity and a request timeout long enough for a session) and start with memory based on the API lesson from change 004 only if needed.
> - Update CLAUDE.md, README.md and knowledge/nfr.md for the new workflow.
>
> Out of scope: Google sign-in on the hosted web app (it needs a local loopback port), a custom domain, a PR CI check, a post-deploy health check, and changes to the API or the APK build.
>
> Open points to confirm: the Artifact Registry repo name for the UI (a new repo or reuse), whether the UI service is public (--allow-unauthenticated), and the repo variables to add (API_BASE_URL and the UI settings), plus the verification (you run the workflow, open the URL and log in).

## Problem
The UI can only be used as a desktop app, an Android APK, or locally in a browser (`UI_MODE=web`). There is no way to open it from a URL. `edukoreaiui/main.py` starts the web mode with `ft.run(main, view=ft.AppView.WEB_BROWSER, port=WEB_PORT)`: it takes its port from `WEB_PORT` (default 8550) instead of the `$PORT` Cloud Run provides, sets no host, and asks Flet to open a local browser. The UI has no Dockerfile or `.dockerignore`, and the repo has only the API deploy workflow (`.github/workflows/deploy-api.yml`) and the APK build (`.github/workflows/build-apk.yml`).

## Proposed outcome
- `edukoreaiui/Dockerfile` and `edukoreaiui/.dockerignore` exist; the image contains no `.env` or secrets.
- In a container the UI binds all interfaces, uses `$PORT` and does not open a browser. Desktop mode and local web mode (`python main.py` with `UI_MODE=web`) behave as they do today.
- `.github/workflows/deploy-ui-web.yml` is a manual workflow in the same style as `deploy-api.yml` (same Workload Identity login, `PROD` environment). It builds the image from `edukoreaiui/`, pushes it to Artifact Registry and deploys a Cloud Run service for the UI, with `API_BASE_URL` and the other UI settings supplied as env vars from repo variables.
- The service is configured for a Flet websocket app (session affinity and a request timeout long enough for a session); memory is raised only if needed.
- After a manual run, the developer opens the service URL, the login page loads and the UI talks to the deployed API (log in).
- `CLAUDE.md`, `README.md` and `knowledge/nfr.md` describe the new workflow.

## Affected users and systems
- **Users:** teachers who will use the UI from a browser instead of the desktop app or APK; the owner who deploys.
- **Screens / UI:** no screen changes; only the startup in `edukoreaiui/main.py` (`__main__` block).
- **Deployment:** new `edukoreaiui/Dockerfile`, `edukoreaiui/.dockerignore`, `.github/workflows/deploy-ui-web.yml`; new Cloud Run service and Artifact Registry repo for the UI; new repo variables.
- **Config:** `edukoreaiui/config/config.py` and `.env.example` if the port or host handling needs settings.
- **API:** none. The API's CORS is currently `*` (`CORS_ORIGINS` variable), so the UI origin is not blocked.
- **Knowledge files to update afterwards:** `knowledge/nfr.md` (deployment and UI platform notes), `knowledge/ui-behavior-and-design.md` (platforms line).

## Constraints
- Out of scope, as stated: Google sign-in on the hosted web app (it needs a local loopback port, `GOOGLE_OAUTH_PORT`, which `knowledge/nfr.md` lists as unsupported for web), a custom domain, a PR CI check, a post-deploy health check, and any change to the API or the APK build.
- All HTTP still goes through `services/api_client.py`; no API contract change.
- No secrets baked into the image; settings come in as Cloud Run env vars from repo variables. The deploy stays manual, and the guard hook blocks Claude from running `gh workflow run` or `gcloud ... deploy`, so the developer runs the workflow and checks the URL.
- Any new production env var for the UI goes into the new workflow's `env_vars` and the repo variables, as `CLAUDE.md` requires for the API.

## Open questions
1. Artifact Registry repo for the UI image: a new `edukoreaiui` repo or reuse `edukoreaiapi`? Assumption: a new `edukoreaiui` repo in `asia-south1` (the developer creates it, as for the API).
2. Should the UI service be public (`--allow-unauthenticated`)? Assumption: yes, like the API, since users log in inside the app.
3. Which repo variables: `API_BASE_URL` (the API's Cloud Run URL) plus `APP_TITLE`, `THEME_COLOR`, `BACKGROUND_COLOR`, as in `build-apk.yml`? Assumption: yes; `WINDOW_*` do not apply to the browser.
4. Does the web UI work end to end with the hosted API (login, scan, generate)? Assumption: login works; features that use a save-file dialog (the question paper download on Generate Questions) may behave differently in a hosted browser session and are not part of this change; the spec will record what was and was not checked.
5. Is 2 GiB or more needed for the UI service? Assumption: no, the UI is a plain Flet server without torch; start with the default and raise it only if the first deploy shows it is needed.
