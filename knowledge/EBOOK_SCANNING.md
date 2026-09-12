# E-Book Scanning (OCR) - Setup E-Books

## Overview

This is the feature that Generate Questions *depends on* but that has no
dedicated documentation of its own — every existing `knowledge/` doc treats
"chapter content already exists in MongoDB" as a given precondition. This doc
covers where that content actually comes from.

**In one line:** a user uploads photos of textbook pages, Claude's vision
API reads the text off them, and the result is saved as plain text against a
class/subject/chapter key.

Spans:
- **edukoreaiapi** — `services/claude_ocr.py`, `routers/ebooks.py` (the
  `/scan` and `/chapter` routes), `database/db.py`
- **edukoreaiui** — `screens/setup_ebooks_screen.py`, `services/api_client.py`

---

## User Workflow

```
Menu ☰ → Academics → Setup E-Books
    ↓
Select Class / Subject / Chapter (fixed dropdown lists, see below)
    ↓
Attach one or more images (file picker, image types only)
    ↓
Click SCAN → images upload → Claude extracts text → text fills the content box
    ↓
User can review/edit the extracted text directly in the text field
    ↓
Click SUBMIT → text saved to MongoDB, keyed by class+subject+chapter
```

Selecting a class/subject/chapter that already has saved content
auto-loads it into the text field (`load_existing_content()`), so revisiting
an already-scanned chapter shows what's there instead of a blank form —
useful for correcting OCR mistakes without rescanning.

### Where the dropdown values come from

Unlike Generate Questions (which populates its Class/Subject/Chapter chips
from `get_scanned_classes()` / `get_scanned_subjects()` / `get_scanned_chapters()`
— i.e., only from what's *already* in the database), Setup E-Books uses
**hardcoded lists** baked directly into `setup_ebooks_screen.py`:

```python
class_dropdown_state = SelectorState("Class", ["I", "II", ..., "X"])
subject_dropdown_state = SelectorState("Subject", ["Science", "English", "Computer Science", "Mathematics"])
chapter_dropdown_state = SelectorState("Chapter", [str(n) for n in range(1, 51)])
```

This is a meaningful asymmetry worth knowing about: Setup E-Books lets you
pick *any* combination from these fixed lists (including ones with no data
yet), while Generate Questions can only show you combinations that already
exist. If a class/subject naming convention changes, this is the file to
edit — there's no shared config or database-driven source for these options.

---

## Backend

### `services/claude_ocr.py`

```python
extract_text_from_images(image_files) -> str
```

Each item in `image_files` must expose `.name` (str) and `.bytes` (bytes) —
`routers/ebooks.py` provides this via a small adapter:

```python
class _UploadedImage:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self.bytes = data
```

For each image:
1. Guesses MIME type from filename via `mimetypes.guess_type()`, falling
   back to `image/jpeg` if unknown.
2. Base64-encodes the bytes and sends to Claude as an image content block,
   alongside a fixed extraction prompt:
   > "Extract all text from this textbook page exactly as written. Preserve
   > headings, numbered lists, paragraphs, and questions. Return only the
   > extracted text, with no commentary."
3. Uses `model=ANTHROPIC_MODEL` (same config value question-generation
   uses — see the note on model configuration below), `max_tokens=4096`,
   `temperature=0` for deterministic output.
4. Concatenates results across all images into one string, each section
   prefixed with `--- {filename} ---`, joined with double newlines.

Multiple images = multiple separate API calls (once per image, in a loop),
**not** a single multi-image request. If someone scans a 20-page chapter as
20 images, that's 20 sequential Claude calls before the text field
populates — worth knowing if scan times feel slow.

### Error handling

Same exception-to-message mapping pattern as `claude_questions.py`:

| Exception | User-facing message |
|---|---|
| `anthropic.AuthenticationError` | "Claude denied the API key. Create an active Anthropic API key and update ANTHROPIC_API_KEY in .env." |
| `anthropic.PermissionDeniedError` | "Claude denied access to the configured model. Check ANTHROPIC_MODEL and your Anthropic account permissions." |
| `anthropic.APIConnectionError` | "Could not reach Claude. Check your internet connection." |
| `anthropic.APIStatusError` | "Claude request failed ({status_code}): {message}" |
| Empty bytes for a file | `ValueError(f"Could not read {image_file.name}.")` |

These are the *identical* error strings used in `claude_questions.py` — if
you're troubleshooting "Claude denied the API key" and only checking Generate
Questions, remember Setup E-Books hits the same API key and will fail the
same way.

### Endpoint (`routers/ebooks.py`)

```
POST /api/ebooks/scan
```

Accepts `images: list[UploadFile]` via multipart form data. Wraps the whole
call in try/except and returns `{"success": False, "error": str(exc)}` on
any failure rather than raising an HTTP error status — the frontend checks
the `success` key rather than the HTTP status code (see `scan_images()`
below, which does still call `response.raise_for_status()` for transport-
level failures, but treats a 200 with `success: false` as an app-level error
it needs to unpack itself).

```
GET  /api/ebooks/chapter?class_name=&subject=&chapter=
POST /api/ebooks/chapter
```

`GET` fetches saved content (used by `load_existing_content()`);
`POST` saves it (used by `submit_content()`). Both are thin wrappers over
`database/db.py` functions.

### `save_scanned_chapter()` (`database/db.py`)

```python
save_scanned_chapter(class_name, subject, chapter, content, username) -> dict
```

Uses MongoDB's `update_one(..., upsert=True)` with `$set` /
`$setOnInsert` split:

- `$set` always updates `content`, `updated_by`, `updated_at` — so
  re-submitting an existing chapter overwrites its content and stamps who
  changed it last.
- `$setOnInsert` only fires on first creation — sets `class`, `subject`,
  `chapter`, `created_by`, `created_at`.

This means the `scanned_chapters` collection retains **only the current
content**, not history. Editing and resubmitting a chapter destroys the
previous text — there's no versioning. `updated_by`/`updated_at` tell you
*who last changed it*, not what it used to say.

The three list functions — `get_scanned_classes()`, `get_scanned_subjects()`,
`get_scanned_chapters()` — all use MongoDB's `.distinct()` on the
`scanned_chapters` collection, meaning they only ever reflect chapters that
have actually been *saved* (post-scan, post-submit), which is exactly what
feeds Generate Questions' cascading selectors.

---

## Frontend

### `screens/setup_ebooks_screen.py`

Key pieces:
- `file_picker = ft.FilePicker()`, restricted to `ft.FilePickerFileType.IMAGE`,
  `allow_multiple=True`, `with_data=True` (loads bytes immediately rather
  than requiring a separate read step).
- `scan_chapters()` — validates class/subject/chapter + at least one image
  selected, shows a blue "Scanning images..." snackbar, calls
  `scan_images()` via `asyncio.to_thread`, and on success drops the result
  straight into `content_field.value`. The user must then click **SUBMIT**
  separately — scanning does not auto-save.
- `submit_content()` — validates selectors + non-empty content, calls
  `save_scanned_chapter()` via `asyncio.to_thread`, shows a green success
  snackbar and navigates to `/home` on success.

### `services/api_client.py`

```python
scan_images(image_files) -> str
```

Note this one behaves differently from every other function in
`api_client.py`: it does **not** catch `httpx.HTTPError` and return a dict.
It calls `response.raise_for_status()` and, if the parsed JSON's `success`
key is falsy, **raises** `RuntimeError(result.get("error", "Scan failed."))`.
The caller (`scan_chapters()` in the screen) is written to expect this — it
wraps the call in its own try/except. If you reuse `scan_images()` elsewhere,
remember it raises rather than returning `{"success": False, ...}` like its
neighbors do.

```python
get_scanned_chapter(class_name, subject, chapter) -> dict | None
save_scanned_chapter(class_name, subject, chapter, content, username) -> dict
```

These two *do* follow the standard try/except-and-return-dict pattern used
elsewhere in the file.

---

## Data Model

### Collection: `scanned_chapters`

```json
{
  "_id": ObjectId,
  "class": "Class Name",
  "subject": "Subject",
  "chapter": "Chapter Name",
  "content": "Extracted or manually-entered chapter text...",
  "created_by": "username",
  "created_at": ISODate(),
  "updated_by": "username",
  "updated_at": ISODate()
}
```

This is the exact collection `get_scanned_chapter()` reads from in
`routers/ebooks.py`'s `generate_questions()` endpoint — it's the hard
dependency mentioned in every Generate Questions doc as "chapter content
must be scanned first." This document is where that requirement is actually
implemented.

---

## A Note on the Model Configuration

Both this feature and Generate Questions read the same `ANTHROPIC_MODEL`
environment variable from `edukoreaiapi/config/config.py`:

```python
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
```

The existing `knowledge/` docs (`IMPLEMENTATION_SUMMARY.md`,
`QUICKSTART.md`, etc.) state this model string as if it's fixed. It isn't —
it's only the *default* if the env var is unset. Whatever your deployed
`.env` or Cloud Run env vars actually specify (see
`.github/workflows/deploy.yml`, which passes `ANTHROPIC_MODEL` as a secret)
is what both OCR and question generation will actually use. Check your live
`.env` / Cloud Run configuration rather than trusting any hardcoded model
name in documentation, this one included.

---

## Known Gaps / Follow-Up Candidates

1. **No content history.** Overwriting a scanned chapter loses the previous
   text permanently. If chapters get miscorrected, there's no undo.
2. **Hardcoded dropdown lists** in `setup_ebooks_screen.py` are disconnected
   from whatever taxonomy Generate Questions or any future admin screen
   might expect — a class/subject typo here silently creates a new,
   never-matching bucket.
3. **Sequential per-image OCR calls** — no batching, so scan time scales
   linearly with image count. Fine for a few pages; worth revisiting for
   full-chapter multi-page scans.
4. **`scan_images()`'s raise-vs-return inconsistency** with the rest of
   `api_client.py` is a minor trap for future maintainers extending this file.
