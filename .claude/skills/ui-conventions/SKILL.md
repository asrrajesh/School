---
name: ui-conventions
description: Use whenever adding or changing a screen, component, route, theme or startup behavior in edukoreaiui/ (screens/, components/, main.py, config/config.py).
---

# UI conventions (Flet)

Current behavior and visual design are documented in `knowledge/ui-behavior-and-design.md`; read the matching section before changing a screen.

## Rules
1. **One screen per file** in `edukoreaiui/screens/`, exporting a `*_view(page)` function that returns Flet controls.
2. **Routes** are registered in `main.py` (`page.on_route_change`, `page.on_view_pop`). Authenticated screens are wrapped with `with_app_frame(content, page)` from `components/app_frame.py`; login, signup and forgot-password are not.
3. **All HTTP goes through `services/api_client.py`.** Never call httpx from a screen or component. If a screen needs new data, use the `api-contract` skill to add the endpoint and client function together.
4. **Configuration** comes from `config/config.py` (loaded from `.env`): `THEME_COLOR`, `BACKGROUND_COLOR`, `APP_TITLE`, `APP_LOGO`, window settings. Do not hardcode colors, titles or the API URL in screens. The font is `Cambria Regular`, registered in `main.py`.
5. **Launch modes.** `UI_MODE=desktop` opens a native window, `UI_MODE=web` the browser on `WEB_PORT`. A change must work in both; Google sign-in uses the local port `GOOGLE_OAUTH_PORT`, which must differ from `WEB_PORT`.
6. **Mark placeholders.** UI that does nothing is documented as **[placeholder]** in `knowledge/`; do not leave dead buttons without recording them.
7. **No UI tests exist.** Verify manually: run the app (use `UI_MODE=web` if the desktop client is blocked) and exercise the changed flow.
