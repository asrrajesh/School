# Spec: Remove stray imports that stop the hosted UI from starting

- **Intent:** [intent.md](intent.md)
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** implemented (2026-10-07)

## Summary
Delete the first two lines of `edukoreaiui/screens/login_screen.py` (`from pydoc import text` and `from turtle import bgcolor, color`). They are unused, and `turtle` cannot be imported without `tkinter`, which the `python:3.12-slim` image used by the UI's Dockerfile does not have. Nothing else changes.

## Findings
- `edukoreaiui/screens/login_screen.py:1-2` contain the two imports; `git log` shows the file's earlier commits only, no deliberate use.
- None of the three imported names is used from the import. An AST check of the file finds no use of `text` or `bgcolor` as names. The only use of `color` is line 45 (`bgcolor=color`), which refers to the parameter of `show_snack(msg: str, color=ft.Colors.RED_600)` defined at line 41; that parameter shadows the imported name.
- `edukoreaiui/main.py:5` imports `screens.login_screen` at module level, so a failing import there stops the app before `ft.run` is reached and before the server listens on `$PORT`.
- Reproduction of the failure condition on this machine (which has tkinter) by blocking it: with `tkinter` and `_tkinter` blocked in `sys.modules`, `import turtle` and `import screens.login_screen` both raise `ModuleNotFoundError`. This matches a fast crash in a container without tkinter, but the Cloud Run revision's log (`edukoreaiui-00001-krv`) has not been read.
- An import inventory of all UI code finds only standard-library modules, local packages, and `flet`, `httpx`, `dotenv` (all in `requirements.txt` plus `flet-web` in the Dockerfile). `turtle` is the only module among them that needs `tkinter`; `pydoc` imports fine without it.
- Not verifiable here: the container start itself (no Docker on this machine) and the Cloud Run run.

## Requirements
1. `edukoreaiui/screens/login_screen.py` contains neither `from pydoc import text` nor `from turtle import ...`.
2. No other line of the file or any other file changes.
3. The login screen module imports without `tkinter` available, and the rest of the UI import chain from `main.py` is unaffected.
4. Desktop and local web behavior are unchanged (the removed names are unused).
5. After the change is on `main`, a manual run of **Deploy UI (web) to Cloud Run** yields a ready revision and the service URL serves the login page.

## Design
Delete lines 1-2 of `edukoreaiui/screens/login_screen.py`; the file then starts with `import asyncio`. No other edit. Chosen over adding `tkinter` to the image because the imports are unused and the Dockerfile should stay minimal.

## Out of scope / must not change
- Any other change to the login screen, other screens or files, the Dockerfile, the workflows, `requirements.txt` and `main.py`.

## Verification
- Static (Claude): `git diff` shows only the two removed lines; `python -m py_compile edukoreaiui/screens/login_screen.py` exits 0; grep finds no `turtle` or `pydoc` import left in `edukoreaiui/` or `edukoreaiapi/`.
- Container-like import (Claude): with `tkinter` and `_tkinter` blocked in `sys.modules`, `import screens.login_screen` and `import main` (from `edukoreaiui/`) succeed.
- Local web start (Claude): `FLET_FORCE_WEB_SERVER=true UI_MODE=web FLET_SERVER_PORT=18550 python main.py` still serves HTTP 200, as before.
- Guard checks: `python .claude/hooks/test_guards.py` reports 0 failures.
- Manual (developer, after the merge to `main`): re-run **Deploy UI (web) to Cloud Run**, open the service URL, expect the login page. Optionally confirm the earlier crash by reading the log of revision `edukoreaiui-00001-krv` for `ModuleNotFoundError`.
- Not verifiable here: the Docker image and the Cloud Run revision.

## Flagged concerns
- The root cause is inferred from the code and a reproduction by blocking `tkinter`, not from the container log. If the log shows a different error, this fix would not be enough.
- Other startup problems may be hidden behind this one; the next run will show them.

## Open questions
1. None new. The intent's open questions stand: the log check is the developer's, and any further cause is a new change.
