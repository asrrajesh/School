# Plan: Remove stray imports that stop the hosted UI from starting

- **Intent:** [intent.md](intent.md)
- **Spec:** [spec.md](spec.md)
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** approved

## Approach
Delete the first two lines of `edukoreaiui/screens/login_screen.py` and prove, without Docker, that the module and the app's import chain still load when `tkinter` is unavailable (the condition of the slim image). The real proof, a ready Cloud Run revision, is the developer's manual deploy after the merge to `main`.

## Files affected
| File | Change | Why |
|---|---|---|
| `edukoreaiui/screens/login_screen.py` (lines 1-2) | Remove `from pydoc import text` and `from turtle import bgcolor, color` | Req 1, 2, 3 |

No other file changes. `knowledge/` is not expected to change; `/update-knowledge` will confirm and only record the new status.

## Steps
1. **Delete lines 1-2** of `edukoreaiui/screens/login_screen.py`, so the file starts with `import asyncio`. Nothing else. Serves req 1, 2 and 4.
   - **Proof:** `git diff` shows exactly those two removed lines; `python -m py_compile edukoreaiui/screens/login_screen.py` exits 0; `grep -rnE "^\s*(from|import) (turtle|pydoc)" edukoreaiui edukoreaiapi` (excluding venvs) finds nothing.
2. **Container-like import check.** From `edukoreaiui/`, with `tkinter` and `_tkinter` set to `None` in `sys.modules` (it makes their import fail, as on the slim image), import `screens.login_screen` and then `main`. Before the change the first import failed with `ModuleNotFoundError` (recorded in the spec). Serves req 3.
   - **Proof:** both imports succeed (exit 0, no `ModuleNotFoundError`).
3. **Local web start still works.** From `edukoreaiui/`: `FLET_FORCE_WEB_SERVER=true UI_MODE=web FLET_SERVER_PORT=18550 python main.py` in the background, fetch `http://127.0.0.1:18550/`, then stop the process (the force flag keeps a browser from opening). Serves req 4.
   - **Proof:** HTTP 200 on port 18550 and nothing left listening afterwards.
4. **Run the guard checks:** `python .claude/hooks/test_guards.py` (0 failures) and `python .claude/skills/api-contract/scripts/check_endpoints.py` (OK, unchanged). Confirm `git diff --stat` shows one file changed.
5. **Hand over the manual verification.** After the PR is merged and `develop` is merged into `main`, the developer re-runs **Deploy UI (web) to Cloud Run**, expects a ready revision and the login page at the service URL. Optionally the developer reads the log of revision `edukoreaiui-00001-krv` to confirm the earlier `ModuleNotFoundError`. Serves req 5. Not run here; the implementation log will say so.

## Risks
- **What could break:** nothing in the app's behavior, since the removed names are unused (the only `color` use is the `show_snack` parameter, which shadows the import). The real risk is that these imports are not the cause of the container crash, or that another startup problem is hidden behind them; the deploy would then still fail and the revision log would show the next error.
- **Riskiest step:** step 5, because it is the only step that exercises the real container, which cannot be run here (no Docker).

## Alternatives considered
- Adding `tkinter` (`python3-tk`) to the image: rejected, the imports are unused and the Dockerfile stays minimal.
- Running a wider cleanup of unused imports across the UI: rejected by the intent (out of scope); the spec's import inventory found no other tkinter-dependent module.

## Rollback
`git revert` the `impl(006)` commit (it restores the two lines).

## Open questions
1. None new. The intent's questions stand: the developer may check the revision log to confirm the cause, and any further failure after this fix becomes a new change.

## Implementation log
- **Step 1:** done. Lines 1-2 of `edukoreaiui/screens/login_screen.py` removed; the file now starts with `import asyncio`. Proof: `git diff` shows exactly the two removed lines (2 deletions, 1 file); `python -m py_compile` exits 0; a search for `turtle`/`pydoc` imports in `edukoreaiui/` and `edukoreaiapi/` (excluding venvs) finds nothing.
- **Step 2:** done. With `tkinter` and `_tkinter` set to `None` in `sys.modules` (run from `edukoreaiui/` with its venv), `import screens.login_screen` and `import main` both succeed. Before the change the first one raised `ModuleNotFoundError` (recorded in the spec).
- **Step 3:** done. `FLET_FORCE_WEB_SERVER=true UI_MODE=web FLET_SERVER_PORT=18550 python main.py`: HTTP 200 on `http://127.0.0.1:18550/`; the process was stopped afterwards and nothing listens on 18550. Side observation: without `FLET_SERVER_IP` the server already listened on `0.0.0.0` and `[::]` on this machine, so the spec 005 remark that Flet would bind only 127.0.0.1 by default was not accurate; the Dockerfile setting is harmless and stays.
- **Step 4:** done. `python .claude/hooks/test_guards.py` reports 0 failures; `check_endpoints.py` reports OK (18 endpoints, 17 client calls, 1 allowlisted); `git diff --stat` shows one file changed.
- **Step 5:** not run here. The developer re-runs **Deploy UI (web) to Cloud Run** after the merge to `main` and optionally reads the log of revision `edukoreaiui-00001-krv`.
- **Departures:** none.
- **Unverified overall:** that these imports were the cause of the container crash (the revision log was not read), the Docker image and the Cloud Run revision, and the login page at the service URL.
