# API Specification (current state)

> Reverse-engineered on 2026-10-03 (git `67ba196`) from `edukoreaiapi/routers/*.py`, `schemas.py` and `edukoreaiui/services/api_client.py`.
> FastAPI app "EduKoreAI API" v1.0.0. Default base URL `http://localhost:8000` (`API_HOST`/`API_PORT`); in Docker/Cloud Run it listens on `$PORT` (8080). Interactive docs are FastAPI's defaults (`/docs`, `/openapi.json`), which are the authoritative machine-readable schema.
> **Contract rule:** any change here must be mirrored in `edukoreaiui/services/api_client.py`.

## Conventions

- **No authentication.** No token, cookie or header is checked. User identity is the `username` value the client sends (the user `_id`).
- **Error style:** business failures return **HTTP 200** with `{"success": false, "error": "<message>"}`. Real HTTP errors occur only for validation (422), the document download (404/500) and unexpected crashes.
- JSON bodies unless marked multipart. Timestamps are UTC, stored server-side only.
- CORS: origins from `CORS_ORIGINS` (default `*`), credentials, all methods and headers allowed.
- Client timeouts (UI): 30 s default, 120 s for generate and save-uploaded, 300 s for scan and upload.

## Health

| Method | Path | Response |
|---|---|---|
| GET | `/health` | `{"status":"ok"}` |

## Auth — `/api/auth`

| Method & path | Request | Success response | Failure |
|---|---|---|---|
| POST `/login` | JSON `{username, password}` | `{success:true, user:{_id, email, mobile}}` | `{success:false, error}`: "Account not found. Please sign up." / "Incorrect password. Please try again." / DB error text |
| POST `/signup` | JSON `{username, password}` | `{success:true}` | invalid username; password shorter than `PASSWORD_MIN_LENGTH`; "already registered"; DB error |
| GET `/users/{user_id}` | path `user_id` | `{success:true, user:{_id, email, mobile, name}}` | "User not found." |
| POST `/forgot-password` | JSON `{username}` | `{success:true}` (no message is sent) | invalid username; "No account found…" |
| POST `/google-callback?code=<str>` | query `code` (no body) | `{success:true, user:{_id, email}}` | "Failed to exchange auth code for token." / "Invalid or expired Google token." |
| POST `/google-login` | JSON `{token}` (Google ID token) | `{success:true, user:{_id, email}}` | "Invalid or expired Google token." |

Notes:
- `username` is an email (`EMAIL_PATTERN`) or mobile (`MOBILE_PATTERN`: optional `+`, 10–15 digits).
- `/login` for a Google-only account (no `password` field) fails with a raw error string (a missing-key error) rather than a friendly message.
- The code exchange in `/google-callback` uses a **hardcoded** `redirect_uri` of `http://localhost:8080/callback`, so the UI's `GOOGLE_OAUTH_PORT` must stay 8080 unless this is changed.

## Menus — `/api/menus`

| Method & path | Response |
|---|---|
| GET `/api/menus` | `{panels:[{panel:str, items:[{title:str, description:str, order:int, icon:bool}]}]}` |

## E-Books — `/api/ebooks`

| Method & path | Request | Response |
|---|---|---|
| GET `/classes` | — | `{classes:[str]}` (distinct, sorted, from `scanned_chapters`) |
| GET `/subjects` | query `class_name` | `{subjects:[str]}` |
| GET `/chapters` | query `class_name`, `subject` | `{chapters:[str]}` |
| GET `/chapter` | query `class_name`, `subject`, `chapter` | `{content: str \| null}` |
| POST `/chapter` | JSON `SaveChapterRequest` `{class_name, subject, chapter, content, username}` | `{success:true, id: str \| null}` (`id` is null when an existing chapter was updated) or `{success:false, error}` |
| POST `/scan` | multipart `images`: one or more files | `{success:true, content: str}` or `{success:false, error}`. `content` = one `--- <filename> ---\n<text>` block per image, separated by blank lines. |
| GET `/question-versions` | query `class_name`, `subject`, `chapters` (comma-separated), `assessment_category`, `assessment_number` (int) | `{versions:[int]}` ascending |
| POST `/generate-questions` | JSON `GenerateQuestionsRequest` (below) | success: `{success:true, id, version, questions:[…], message}`; else `{success:false, error}` |
| POST `/upload-questions` | multipart form: `class_name`, `subject`, `chapters` (comma-separated), `assessment_category`, `assessment_number`, `complexity`, `username`, plus `images` files | same shape as generate. **Not called by any UI screen** (the UI scans, then calls `/save-uploaded-questions`). |
| POST `/save-uploaded-questions` | JSON `SaveUploadedQuestionsRequest` (below) | same shape as generate |
| GET `/generate-questions/document` | query `class_name`, `subject`, `chapters` (comma-separated), `assessment_category`, `assessment_number`, `version` (int) | `.docx` bytes (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`) with `Content-Disposition: attachment; filename="<CAT><N> - <subject> - <chapters> - v<version>.docx"`; HTTP 404 `{detail}` if the version doesn't exist; 500 `{detail}` if rendering fails |

### Request models (`schemas.py`)

```
QuestionRowConfig   { questionType: str, questionCount: int, marksPerQuestion: float }
GenerateQuestionsRequest {
  class_name: str, subject: str, chapters: [str],
  assessmentCategory: str,            # "fa" | "sa" (not validated)
  assessmentNumber: int,              # 1 | 2 (not validated)
  complexity: "basic" | "intermediate" | "advanced",   # validated
  questionRows: [QuestionRowConfig], username: str }
SaveUploadedQuestionsRequest {
  class_name, subject, chapters: [str], assessmentCategory, assessmentNumber,
  complexity: (same literal), paperContent: str,
  questionRows: [QuestionRowConfig], username: str }
```

### Behavior notes
- `/generate-questions`: joins each selected chapter that has saved text as `--- <chapter> ---\n<content>`. If none has text: `{success:false, error:"Chapter content not found. Please scan the e-books first."}`. Chapters without text are silently skipped. Otherwise one LLM call, then a save (next version).
- `/save-uploaded-questions` and `/upload-questions`: empty text → error; zero extracted questions → error; success saves with `source:"uploaded"` and `sourceContent`. The `/upload-questions` variant saves `configuration: []`; `/save-uploaded-questions` saves the posted rows.
- All LLM/OCR exceptions are caught and returned as `{success:false, error:<message>}`.

## UI client mapping (`api_client.py`)
`login_user`, `register_user`, `get_user`, `request_password_reset`, `google_callback`, `get_scanned_chapter`, `save_scanned_chapter`, `get_menus`, `get_classes`, `get_subjects`, `get_chapters`, `scan_images`, `generate_questions`, `upload_questions` (unused by screens), `save_uploaded_questions`, `get_question_versions`, `download_question_paper`. Read-only list calls swallow errors and return empty values, so an unreachable API shows as empty dropdowns rather than an error.
