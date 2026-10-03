# Plan: UI does not open after flet-desktop install

- **Intent:** [intent.md](intent.md)
- **Spec:** [spec.md](spec.md)
- **Author:** Rajesh
- **Date:** 2026-10-03
- **Status:** draft

## Approach
Switch this machine to browser mode (`UI_MODE=web`), then make `main.py` report a failed desktop launch with the workaround instead of exiting silently. No API, data or knowledge-schema changes.

## Files affected
| File | Change | Why |
|---|---|---|
| `edukoreaiui/.env` (gitignored) | `UI_MODE=web` | Requirement 1: working UI now |
| `edukoreaiui/main.py` (`__main__` block, ~line 137) | Print the active mode; wrap desktop `ft.run` and print cause + `UI_MODE=web` hint on failure | Requirements 2 and 3 |
| `knowledge/nfr.md`, `knowledge/ui-behavior-and-design.md` | Update after build via `/update-knowledge`, only if startup behavior changed | Keep snapshot current |

## Steps
1. Set `UI_MODE=web` in `edukoreaiui/.env`. Serves requirement 1.
   - **Proof:** with the API running, `py main.py` from `edukoreaiui/` opens http://localhost:8550 and shows the login screen.
2. Edit the `__main__` block: print the mode in use; for desktop mode catch exceptions from `ft.run(main)` and print a message naming Windows code integrity / Smart App Control as the likely cause and the `UI_MODE=web` workaround. Serves requirements 2 and 3.
   - **Proof:** with `UI_MODE=desktop`, force a failure (for example temporarily point `ft.run` at an invalid view) and confirm the message prints; with a working client the app opens as before.
3. Check the Code Integrity log shows no new `flet.exe` blocks in web mode.
   - **Proof:** `Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-CodeIntegrity/Operational'} -MaxEvents 50` has no new flet entries after the run.
4. Run `/update-knowledge changes/001-ui-not-launching/intent.md`.

## Risks
- **What could break:** desktop launch on machines where it works, if the wrapper swallows exceptions or changes exit codes. Re-raise after printing.
- **Riskiest step:** step 2. A finding from planning: in a trial run of `ft.run(main)` in desktop mode today, the client stayed up until killed and raised nothing in Python. The earlier block (12:16 and 12:41 in the log) may be intermittent or the exit may happen in the child process, so Python may not see an exception. The wrapper alone may never fire.
- **Mitigation:** if no exception is observable, replace the wrapper with a pre-launch hint printed in desktop mode on Windows, naming the workaround. Do not auto-fall back to web.

## Alternatives considered
- Auto-fall back to web on failure: rejected, it hides the misconfiguration and opens a browser unexpectedly.
- Changing Python version (3.13): rejected for now, the log points at code integrity, not Python.
- Adding a Windows policy exception: out of scope and a security decision.

## Rollback
Set `UI_MODE=desktop` in `.env` and revert the `main.py` block with `git checkout edukoreaiui/main.py`.

## Open questions
1. Is the desktop block intermittent? Assumption: yes or timing related; step 2's fallback covers both.
2. Does Google sign-in work in web mode (port 8080 callback)? Untested; check after step 1.
