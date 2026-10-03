# Data Model (current state)

> Reverse-engineered on 2026-10-03 (git `67ba196`) from `edukoreaiapi/database/db.py`, `routers/*.py` and `fix_indexes.py`.
> Database: MongoDB, name from `DB_NAME` (default `MySchool`). Connection from `MONGO_URI` (default `mongodb://localhost:27017/`), server selection timeout `DB_CONNECTION_TIMEOUT` ms (default 5000).
> There are **no schema validators**. The shapes below are what the code writes. Access is only through pymongo in `database/db.py`, except `routers/menus.py`, which reads `menus` directly.

## Collections

### `users`
| Field | Type | Written by | Notes |
|---|---|---|---|
| `_id` | string (UUID4) | signup, Google login | not an ObjectId |
| `email` | string | signup (email username), Google | unique **partial** index |
| `mobile` | string | signup (mobile username) | unique **partial** index |
| `password` | string (bcrypt hash) | signup | absent for Google-only accounts |
| `google_id` | string | Google login | Google `sub`. Unique **partial** index. |
| `auth_method` | string `"google"` | Google create or link | not set for password users |
| `linked_at` | datetime (UTC) | Google link or create | |
| `created_at` | datetime (UTC) | signup, Google create | |
| `name` | string | **never written** | read by `get_user_by_id`; always null today |

Example (password user): `{_id, mobile, password, created_at}`. Example (Google): `{_id, google_id, email, auth_method:"google", linked_at, created_at}`.

Account linking: a Google login finds a user by `google_id`, else by `email` (then sets `google_id`, `auth_method`, `linked_at` on that user), else creates a new user.

**Indexes** (created in `get_db()` at first connection): `email`, `mobile` and `google_id`, each unique with `partialFilterExpression: {field: {$exists: true}}`. `fix_indexes.py` is a manual script that drops legacy `username_1`, `email_1` and `mobile_1` indexes and recreates the partial `email` and `mobile` indexes. It is needed only if old non-partial indexes exist.

### `scanned_chapters`
Textbook chapter text, one document per class + subject + chapter.

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | auto |
| `class` | string | for example "I" … "X" from the Setup E-Books screen |
| `subject` | string | |
| `chapter` | string | for example "1" … "50" |
| `content` | string | OCR text as edited by the user. Image sections start with `--- <filename> ---`. |
| `created_by`, `created_at` | string, datetime | set on insert only (`$setOnInsert`) |
| `updated_by`, `updated_at` | string, datetime | set on every save |

Upsert key: `{class, subject, chapter}`. **No unique index** enforces it. `created_by` and `updated_by` hold whatever `username` the client sent, which is the user `_id` from the UI session, or the string `"Guest"` or `"unknown"`.

Derived lookups: classes, subjects and chapters offered on the Generate screen come from `distinct()` over this collection.

### `questions`
One document per saved version of a paper, generated or uploaded.

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | auto |
| `class`, `subject` | string | |
| `chapters` | array of string | selected chapters, in selection order |
| `assessmentCategory` | `"fa"` \| `"sa"` | |
| `assessmentNumber` | int (1 or 2 in the UI) | |
| `version` | int | max existing version for the combination + 1 |
| `complexity` | `"basic"` \| `"intermediate"` \| `"advanced"` | |
| `questions` | array of question objects (below) | |
| `configuration` | array of `{questionType, questionCount, marksPerQuestion}` | user's rows. Empty (`[]`) for papers saved via `/upload-questions`. |
| `source` | `"generated"` \| `"uploaded"` | |
| `sourceContent` | string | OCR text of the paper, **uploaded only** |
| `generated_by` | string | username sent by the client (user `_id`) |
| `generated_at` | datetime (UTC) | |

**Question object** (as returned by the LLM, stored unchanged):
`{type: "mcq"|"short"|"long", marks: number, question: string, options?: [string×4], correctOption?: "A"|"B"|"C"|"D", answerKey: string}`. `options` and `correctOption` apply to MCQ only. The code does not validate the shape, so other `type` values or missing fields are stored as returned.

**No indexes** exist on this collection.

Version rules:
- Next version = `max(version)` over documents matching class, subject, assessment category and number, and `chapters` matching the requested list (`$in`, or any chapters when the list is empty), plus 1. It is read then insert, with no transaction.
- Version listing and fetch use `chapters: {$in: requested}`. A paper for chapters [1,2] therefore appears when you ask for [2,3], and versions are shared across overlapping chapter sets.
- Fetch without a version returns the highest version.

### `menus`
Read by `GET /api/menus` to build the home screen panels. **Nothing in the repo writes it**, so it is seeded manually.

| Field | Type | Notes |
|---|---|---|
| `panel` | string | grouping title, for example a section name |
| `title`, `description` | string | row text |
| `order` | int | sort order (ascending) |
| `icon` | bool | whether to draw an icon placeholder box |

The API returns documents sorted by `order`, grouped by `panel` in first-seen order, without `_id`.

## Relationships (logical only; no foreign keys)

```
users._id ──(string copy)──> scanned_chapters.created_by / updated_by
users._id ──(string copy)──> questions.generated_by
scanned_chapters(class, subject, chapter) ──(by name)──> questions(class, subject, chapters[])
```
Questions are generated from chapter text at that time and keep no pointer to the chapter text version used, other than `sourceContent` for uploads.

## Not stored today
Roles, school or tenant, password reset tokens, sessions or tokens, audit trail, deletion or archival flags, prompt or model used for a generation, token usage and cost.
