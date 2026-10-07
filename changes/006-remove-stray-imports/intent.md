# Intent: Remove stray imports that stop the hosted UI from starting

- **ID:** 006
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** approved
- **Type:** change to existing behavior

## Developer request
> The hosted UI fails to start on Cloud Run: screens/login_screen.py has two unused stray imports at the top (from pydoc import text, from turtle import bgcolor, color). turtle needs tkinter, which the python:3.12-slim image lacks, so the container crashes at import before listening on $PORT. Remove the two unused imports so the UI starts in the container. Out of scope: any other change to the login screen or to other files. Evidence: failed Deploy UI (web) run 37647465947, revision edukoreaiui-00001-krv, container failed to start on PORT=8080 within about 14 seconds.

## Problem
The first run of **Deploy UI (web) to Cloud Run** (change 005) built and pushed the image, but the Cloud Run revision `edukoreaiui-00001-krv` never became ready: the container failed to start and listen on `PORT=8080`, and it failed within about 14 seconds (a crash, not a slow start).

`edukoreaiui/screens/login_screen.py` starts with two imports that look like editor auto-imports and are not used in the file: `from pydoc import text` and `from turtle import bgcolor, color`. `turtle` needs `tkinter`, which the `python:3.12-slim` base image does not include. `main.py` imports `screens.login_screen` at the top, so the import would fail before the server starts. On the developer's Windows machine the standard Python install includes tkinter, so it works there. A search of `edukoreaiui/` and `edukoreaiapi/` finds these two as the only such stray standard-library imports.

## Proposed outcome
- `screens/login_screen.py` no longer imports `pydoc` or `turtle`; nothing else in the file changes.
- The UI starts without `tkinter`, so the container listens on `$PORT` and the hosted service can become ready.
- After the next manual run of **Deploy UI (web) to Cloud Run**, the service URL serves the login page.

## Affected users and systems
- **Users:** the owner deploying the web UI; later, teachers using the hosted UI.
- **Screens / UI:** `edukoreaiui/screens/login_screen.py` (the first two lines only). No visible behavior changes.
- **API:** none. **Data:** none.
- **Knowledge files to update afterwards:** probably none (no behavior change); `/update-knowledge` will confirm and only record the new status.

## Constraints
- Out of scope, as stated: any other change to the login screen or to other files.
- The deploy workflow and Dockerfile from change 005 stay as they are; the developer re-runs the workflow after the merge to `main`, and the guard hook blocks Claude from running it.
- Desktop and local web behavior must be unchanged (the removed names are unused).

## Open questions
1. Is the import error really the cause of the crash? Assumption: yes (it matches a fast crash, and `turtle` cannot import without `tkinter` on the slim image), but the revision's container log has not been read. The developer can check Cloud Run, then `edukoreaiui`, then Revisions, then `edukoreaiui-00001-krv`, then Logs, for a `ModuleNotFoundError`. If the log shows a different error, this intent would need to be updated.
2. Does the app have other reasons to fail in the container once this import is gone? Assumption: unknown. The first run after the fix will show it, and any further cause would be a new change.
