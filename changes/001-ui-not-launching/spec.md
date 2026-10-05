# Spec: UI does not open after flet-desktop install

- **Intent:** [intent.md](intent.md)
- **Author:** Rajesh
- **Date:** 2026-10-03
- **Status:** implemented (2026-10-03)

## Summary
On this machine the Flet desktop client cannot start because Windows code integrity blocks one of its DLLs, and `main.py` exits without any message. Fix: make the browser mode the working path here and make the failure visible instead of silent.

## Findings
- `py main.py` runs `ft.run(main)` (`edukoreaiui/main.py:141`) because `UI_MODE=desktop` in `edukoreaiui/.env`.
- Flet downloads the client to `C:\Users\asrra\.flet\client\flet-desktop-full-0.86.5\flet\flet.exe`. The "Installing flet-desktop ... OK" line is that download succeeding.
- Event log `Microsoft-Windows-CodeIntegrity/Operational` (03-10-2026 12:16 and 12:41) shows `flet.exe` tried to load `media_kit_libs_windows_video_plugin.dll` and was blocked: "did not meet the Enterprise signing level requirements or violated code integrity policy (Policy ID {0283ac0f-fff1-49ae-ada1-8a933130cad6})".
- So the root cause is the Windows Application Control / Smart App Control policy on this machine blocking an unsigned plugin DLL, not a bug in the app code. The same policy blocked the Rust build scripts (os error 4551) during the API install.
- Environment: Python 3.14.7, flet and flet-desktop 0.86.5. Python version is not implicated by the log.

## Requirements
1. With `UI_MODE=web`, `py main.py` opens the login screen in the browser on `WEB_PORT` (8550).
2. If the desktop client fails to start, the user sees a message naming the likely cause and the `UI_MODE=web` workaround, not a silent exit.
3. Desktop and web behavior is unchanged on machines where the client runs.

## Design
- Immediate fix, no code: set `UI_MODE=web` in `edukoreaiui/.env`.
- Code change in `edukoreaiui/main.py` `__main__` block: wrap `ft.run(main)` for desktop mode so an exception is reported with the workaround. Also print a startup line stating the mode in use. (Chosen over auto-falling back to web, which would hide the misconfiguration and open a browser unexpectedly.)
- Limitation: the block happens inside the flet.exe child process, and the Python process may only see it as a non-zero exit or a closed session. The implementation must test what Python can detect; if nothing, fall back to a printed hint before launch when running on Windows desktop mode.
- No API change; `services/api_client.py` untouched.

## Out of scope / must not change
- No changes to Windows security policy or code-signing workarounds.
- Default `UI_MODE` in `.env.example` stays `desktop`.

## Verification
- Set `UI_MODE=web`, run `py main.py` from `edukoreaiui/` with the API running: login screen loads at http://localhost:8550.
- With `UI_MODE=desktop` on this machine: a clear message is printed explaining the block and the workaround.
- Re-check the Code Integrity log shows no new blocks for web mode.

## Flagged concerns
- Security: do not disable Smart App Control or add policy exceptions to make desktop mode work; owner of the machine policy decides if that is ever acceptable.
- UX: Google sign-in uses a local port (8080) and system browser, which should still work in web mode, but is untested.

## Open questions
1. Can Python reliably detect the blocked launch? Assumption: not always; a pre-launch hint is the fallback.
2. Should the web workaround be documented in the README or `.env.example` comments? Assumption: `.env.example` already covers it.
