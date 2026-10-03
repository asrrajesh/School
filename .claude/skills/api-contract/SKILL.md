---
name: api-contract
description: Use whenever adding, changing or removing an endpoint in edukoreaiapi/routers/*.py, a request model in schemas.py, or any function in edukoreaiui/services/api_client.py. Keeps the API and the UI client in sync.
---

# API contract between edukoreaiapi and edukoreaiui

The two apps share no code and no types. The contract lives in two places that must change together: the routers/`schemas.py` in the API and `edukoreaiui/services/api_client.py` in the UI.

## Rules
1. **Mirror every change.** A new, renamed or removed endpoint, a changed method, query/form/body field or response shape in `edukoreaiapi/routers/*.py` or `schemas.py` must be reflected in `api_client.py` in the same change (one client function per endpoint), and the other way round.
2. **Only `api_client.py` calls the API.** Screens and components never use httpx directly.
3. **Error shape.** Business failures return `{"success": false, "error": "<message>"}` with HTTP 200 rather than HTTP errors (the exception is the `.docx` download in `routers/ebooks.py`, which can raise `HTTPException`). Client functions turn connection failures into the same shape (see `_connection_error`). Keep new endpoints consistent with the neighbouring ones in the same router.
4. **Prefixes.** Routers use `/api/auth`, `/api/ebooks`, `/api/menus`. A new router must be included in `edukoreaiapi/main.py`.
5. **Docs.** Endpoint changes also change `knowledge/api-specification.md`; that file is updated by `/update-knowledge` at the end of the change, not by hand mid-change.

## Steps
1. Make the API change and the matching `api_client.py` change.
2. Run the check (standard library only, no venv needed):
   ```bash
   python .claude/skills/api-contract/scripts/check_endpoints.py
   ```
   It exits 1 and lists API endpoints with no client call, client calls with no router, and stale allowlist entries.
3. Endpoints that intentionally have no client function go in `API_ONLY` in the script (today: `POST /api/auth/google-login`). Remove the entry when a client function is added.
4. If the check cannot parse a new call style (it recognizes `httpx.<method>(f"{API_BASE_URL}/api/...")`), extend the regex in the script rather than skipping the check.

The check compares paths and methods only. It cannot verify field names or response shapes, so review those by reading both sides.
