# Spec: Fix Cloud Run API deploy running out of memory at startup

- **Intent:** [intent.md](intent.md)
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** approved

## Summary
Add `--memory=2Gi --cpu-boost` to the Cloud Run deploy `flags` in `.github/workflows/deploy-api.yml`, so the API container can load the EasyOCR engine at startup without being killed at Cloud Run's 512 MiB default. Nothing else changes.

## Findings
- `.github/workflows/deploy-api.yml:60`: the "Deploy to Cloud Run" step sets only `flags: --allow-unauthenticated --port=8080`. No memory or CPU flag is set, so Cloud Run applies its defaults (512 MiB, 1 CPU).
- `edukoreaiapi/main.py:10-20` (`lifespan`): calls `get_ocr_engine()` before `yield`, so uvicorn does not accept connections until the OCR engine is built. An out-of-memory kill is a process kill, not an exception, so the `try/except Exception: pass` around it does not help.
- `edukoreaiapi/ocr/factory.py`: `OCR_ENGINE` defaults to `easyocr` (`config/config.py:52`), which builds `EasyOCREngine`; its `__init__` imports `easyocr` (torch, OpenCV) and creates `easyocr.Reader(...)` (`ocr/easyocr_engine.py:12-15`), downloading models on first run. The deploy workflow does not set `OCR_ENGINE`, so production uses the default.
- Cloud Run logs for revision `edukoreaiapi-00003-2dx` (2026-10-05, seen by the developer in Logs Explorer): `INFO: Waiting for application startup.` at 23:44:46, then `Memory limit of 512 MiB exceeded with 533 MiB used` at 23:44:55, `STARTUP TCP probe failed 1 time consecutively ... on port 8080`, and the revision `Ready` condition changed to False at 23:45:06. The same run authenticated, built and pushed the image successfully (GitHub run `37353442307`).
- Cloud Run's container filesystem is in memory, so EasyOCR's downloaded models count against the memory limit as well as the loaded torch runtime. The peak is unknown: only 533 MiB was reached before the kill.
- `--memory` and `--cpu-boost` are `gcloud run deploy` flags; the `deploy-cloudrun` action passes `flags` straight to that command (visible in the failed run's "Running: gcloud run deploy ..." line).
- Not verifiable here: that 2 GiB is enough and the revision then becomes ready. That needs a real deploy by the developer.

## Requirements
1. The "Deploy to Cloud Run" step's `flags` in `.github/workflows/deploy-api.yml` become `--allow-unauthenticated --port=8080 --memory=2Gi --cpu-boost`.
2. No other line of the workflow changes: triggers, secrets, vars, `env_vars`, the `PROD` environment, regions, image and service names stay as they are.
3. After the change is on `main`, a manual run of **Deploy API to Cloud Run** yields a ready revision, and `GET <service URL>/health` returns `{"status": "ok"}`.

## Design
Edit only the `flags` line in `.github/workflows/deploy-api.yml`. Chosen over a one-off `gcloud run services update --memory` because the workflow is the source of truth for the service settings, so the value survives every future deploy. 2 GiB is the developer's stated value; `--cpu-boost` gives the instance extra CPU during startup while the models load.

## Out of scope / must not change
- `OCR_ENGINE` (stays default `easyocr`), the OCR preload in `main.py`, and all application code.
- Startup probe settings, minimum or maximum instances, CPU count, concurrency and timeout.
- Everything else in the workflow, `Dockerfile`, `.dockerignore`, `knowledge/` (updated by `/update-knowledge`).

## Verification
- Static (Claude): the YAML still parses, and `git diff` shows exactly the one changed `flags` line; the set of `secrets.*` / `vars.*` references is unchanged; `python .claude/hooks/test_guards.py` reports 0 failures.
- Manual (developer, after the change is merged and `develop` is merged into `main`): run **Deploy API to Cloud Run**, expect the "Deploy to Cloud Run" step to succeed, then open `<service URL>/health` and expect `{"status": "ok"}`. If it fails again, read the revision's logs for a new memory or timeout message.
- Not verifiable here: the real deploy, the actual peak memory, and the cost impact.

## Flagged concerns
- 2 GiB may still not be enough for torch plus the models, or startup may still exceed the probe window; the log only proves the 512 MiB default is too small. A larger value or a different OCR approach would be a follow-up.
- A 2 GiB instance costs more per second while running. Cloud Run scales to zero by default, but a minimum-instances setting elsewhere (none is set in this workflow) would make the cost continuous.
- The OCR preload remains in the startup path, so every cold start pays the model-loading time (`knowledge/nfr.md` notes this as unmeasured).

## Open questions
1. Is a startup-time change (probe timeout, `--cpu=2`) needed? Assumption: no, `--cpu-boost` is enough; handled in a follow-up if the next run still fails.
