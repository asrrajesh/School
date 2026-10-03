# Intent: UI does not open after flet-desktop install

- **ID:** 001
- **Author:** Rajesh
- **Date:** 2026-10-03
- **Status:** approved
- **Type:** change to existing behavior

## Developer request
> Fix the below issue in edukoreai project
>
> When I run py main.py, I am getting below message
> (uivenv) c:\Users\asrra\Rajesh\edukoreai\edukoreaiui>py main.py
> Installing flet-desktop 0.86.5 package...OK
>
> (uivenv) c:\Users\asrra\Rajesh\edukoreai\edukoreaiui>
>
> Its not loading the UI.
>
> Can you find the route cause of this problem and fix it.

## Problem
Running `py main.py` in `edukoreaiui/` downloads and installs `flet-desktop` 0.86.5, then the process exits silently and no window appears. Per `knowledge/`, the UI starts a native Flet desktop window by default (`UI_MODE=desktop`, `ft.run(main)` in `main.py`) and offers `UI_MODE=web` as a workaround when Windows Smart App Control blocks the desktop client. The same machine already showed Application Control (os error 4551) blocking compiled binaries during the API install, so the desktop client being blocked is a likely, unconfirmed cause.

## Proposed outcome
- The root cause of the silent exit is identified and recorded.
- `py main.py` on this machine results in a visible, working UI (login screen), either in the desktop window or in the browser.
- If the desktop client cannot run on a machine, the failure is reported clearly instead of exiting with no message.

## Affected users and systems
- **Users:** developers/users running the UI locally on Windows.
- **Screens / UI:** startup in `edukoreaiui/main.py` (`UI_MODE`, `ft.run`); `edukoreaiui/.env`.
- **Knowledge files to update afterwards:** `knowledge/nfr.md`, `knowledge/ui-behavior-and-design.md` (only if startup behavior or the workaround changes).

## Constraints
- No API changes; `services/api_client.py` is unaffected.
- Keep the existing desktop and `UI_MODE=web` behavior for machines where it works.
- Do not weaken Windows security settings as the fix.

## Open questions
1. Is the cause Smart App Control blocking the flet-desktop binary? Assumption: yes; confirm via exit code and Windows event log.
2. Is `UI_MODE=web` an acceptable permanent fix for this machine? Assumption: yes.
3. Is the flet 0.86.5 / Python 3.14 combination itself a factor (the API install also failed on 3.14)? Assumption: possibly; test on Python 3.13.
