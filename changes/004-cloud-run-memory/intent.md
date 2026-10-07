# Intent: Fix Cloud Run API deploy running out of memory at startup

- **ID:** 004
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** implemented (2026-10-07)
- **Type:** change to existing behavior

## Developer request
> Cloud Run deploy of the API fails: the container is killed with "Memory limit of 512 MiB exceeded" during startup because the lifespan preloads EasyOCR (torch and models). Raise the Cloud Run memory and add startup CPU boost in .github/workflows/deploy-api.yml flags (--memory=2Gi --cpu-boost) so the revision starts and /health responds. Out of scope: switching OCR_ENGINE, changing the app's OCR preload, other deploy changes. Evidence: Cloud Run logs for revision edukoreaiapi-00003-2dx on 2026-10-05.

## Problem
The first run of **Deploy API to Cloud Run** from the repo root (change 003) got through authentication, the Docker build and push, but the Cloud Run revision `edukoreaiapi-00003-2dx` failed to become ready. Its logs show, during "Waiting for application startup", `Memory limit of 512 MiB exceeded with 533 MiB used`, then `STARTUP TCP probe failed ... on port 8080`.

The API's startup (`edukoreaiapi/main.py`, `lifespan`) loads the OCR engine before serving, and with the default `OCR_ENGINE=easyocr` that loads torch and the EasyOCR models. The workflow's deploy `flags` set no memory, so Cloud Run uses its 512 MiB default. `knowledge/nfr.md` records the preload and notes the cold-start cost "was not measured".

## Proposed outcome
- `.github/workflows/deploy-api.yml` deploys with `--memory=2Gi --cpu-boost` added to the existing `flags` (`--allow-unauthenticated --port=8080` stay).
- A manual run of **Deploy API to Cloud Run** produces a ready revision and `GET /health` on the service URL returns `{"status": "ok"}`.
- Nothing else in the workflow, the app or its configuration changes.

## Affected users and systems
- **Users:** the owner who deploys, and the API's production users (the service cannot start today).
- **Deployment:** `.github/workflows/deploy-api.yml` (the `flags` line of the "Deploy to Cloud Run" step).
- **Knowledge files to update afterwards:** `knowledge/nfr.md` (section 7: memory and CPU boost, and the cold-start note).

## Constraints
- Out of scope, as stated: switching `OCR_ENGINE` (for example to `llm_vision`), changing the app's OCR preload, and any other deploy change.
- Triggers, secrets, vars, `env_vars`, the `PROD` environment and the deploy targets stay as they are.
- Deploy stays manual; the guard hook blocks Claude from running `gh workflow run` and `gcloud ... deploy`, so the developer runs the deploy and checks `/health` after the change is on `main`.
- A cost impact is accepted by the developer: a 2 GiB instance costs more per second while running (the service scales to zero when idle unless a minimum is set elsewhere).

## Open questions
1. Is 2 GiB enough? Assumption: yes; the log only shows 533 MiB reached at about 9 seconds with startup still loading, so the real peak is unknown. If the revision is still killed, the next step is a larger value or a different OCR approach, handled as a follow-up.
2. Does the default startup probe timeout suffice once memory is raised? Assumption: yes (the default allows about 240 seconds); if model loading takes longer, the probe settings are a follow-up.
3. Is a CPU allocation change needed (for example `--cpu=2`)? Assumption: no; `--cpu-boost` is enough for startup.
