# Authentication - Login, Signup & Password Reset

## Overview

This document covers the account system: signing up, logging in, and the
forgot-password flow. It spans both projects:

- **edukoreaiapi** — `routers/auth.py`, `database/db.py`, `schemas.py`
- **edukoreaiui** — `screens/login_screen.py`, `screens/signup_screen.py`,
  `screens/forgot_password_screen.py`, `services/api_client.py`

Unlike Generate Questions, none of this touches Claude — it's plain
MongoDB + bcrypt + Pydantic validation.

---

## What's Implemented

- ✅ Sign up with an email address or mobile number as the username
- ✅ Passwords hashed with bcrypt (never stored in plain text)
- ✅ Login with username/password
- ✅ Forgot-password flow that checks the account exists
- ✅ Session tracking via `page.session.store["current_user"]`
- ✅ A client-only "Continue as Guest" shortcut on the login screen

## What's *Not* Implemented (Important)

- ❌ **Forgot Password does not send an email or SMS.** `request_password_reset()`
  in `database/db.py` only checks whether the username exists in the `users`
  collection and returns `{"success": True}`. The docstring for that function
  literally calls it a "stub for real reset logic." There is no reset link, no
  OTP, and no token generation anywhere in the codebase.
- ❌ **Guest login is not a real account.** `do_guest_login()` in
  `login_screen.py` sets `current_user` to the literal string `"Guest"`
  directly in the Flet session — it never calls the backend, never hits
  `/api/auth/login`, and isn't backed by any database record. Any feature that
  trusts `current_user` as a real username (e.g. `generated_by` in the
  `questions` collection) will happily store `"Guest"` as the author.
- ❌ **No rate limiting or lockout.** The README for edukoreaiui documents
  `MAX_LOGIN_ATTEMPTS` and `LOCKOUT_DURATION` as configuration settings, but
  neither `routers/auth.py` nor `database/db.py` implements any attempt
  counting or lockout logic. These are aspirational config values only.
- ❌ **No session expiry.** `SESSION_TIMEOUT` is mentioned in the edukoreaiui
  README but there's no corresponding code checking or enforcing it.

---

## Backend

### Endpoints (`edukoreaiapi/routers/auth.py`)

All three routes are simple pass-throughs to `database/db.py` functions —
there's no additional business logic in the router layer.

```
POST /api/auth/login
POST /api/auth/signup
POST /api/auth/forgot-password
```

| Route | Request body (`schemas.py`) | Delegates to |
|---|---|---|
| `/login` | `LoginRequest{username, password}` | `login_user()` |
| `/signup` | `SignupRequest{username, password}` | `register_user()` |
| `/forgot-password` | `ForgotPasswordRequest{username}` | `request_password_reset()` |

### Validation rules (`database/db.py`)

A "username" is accepted if it matches **either** pattern (`is_valid_username`
calls `is_valid_email` OR `is_valid_mobile`):

- **Email:** `EMAIL_PATTERN` from config, default `^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$`
- **Mobile:** `MOBILE_PATTERN` from config, default `^\+?[0-9]{10,15}$`
  (10–15 digits, optional leading `+`)

Both patterns are configurable via `.env` (`EMAIL_PATTERN`, `MOBILE_PATTERN` in
`edukoreaiapi/config/config.py`), so if signups are being rejected
unexpectedly, check those env vars before assuming the code is wrong.

Password length is enforced only at signup, via `PASSWORD_MIN_LENGTH`
(default `8`, from `edukoreaiapi/config/config.py`). Login does **not**
re-check password length — it just compares the hash.

### `register_user(username, password)`

1. Strips whitespace from username.
2. Rejects if `is_valid_username()` fails →
   `"Enter a valid email address or mobile number."`
3. Rejects if `len(password) < PASSWORD_MIN_LENGTH` →
   `"Password must be at least {N} characters."`
4. Hashes with `bcrypt.hashpw(..., bcrypt.gensalt())` and inserts into
   `db.users` with `created_at: datetime.utcnow()`.
5. Catches `DuplicateKeyError` (the `users` collection has a unique index on
   `username`, created in `get_db()`) →
   `"This email / mobile number is already registered."`
6. Catches `ConnectionFailure` → `"Cannot connect to database. Please try again."`

### `login_user(username, password)`

1. Strips whitespace, looks up `db.users.find_one({"username": username})`.
2. No user found → `"Account not found. Please sign up."`
3. `bcrypt.checkpw()` fails → `"Incorrect password. Please try again."`
   (Note: `check_password()` wraps this in a try/except for `TypeError`/
   `ValueError` and returns `False` rather than raising, so malformed stored
   hashes fail closed as "incorrect password" rather than crashing.)
4. Success → `{"success": True, "user": {"username": ...}}`. Only the
   username is returned — no user ID, roles, or profile data, because none of
   that exists in the `users` schema yet (see Data Model below).

### `request_password_reset(username)`

Validates the username format, checks the account exists, and returns
success — **that's the entire implementation.** No email, no SMS, no token.
If you're building an actual reset flow, this is the function to extend.

---

## Frontend

### Screens

| Screen | File | Behavior |
|---|---|---|
| Login | `login_screen.py` | Sync handler `do_login()`, calls `login_user()` directly (no `asyncio.to_thread`) |
| Signup | `signup_screen.py` | Async handler `do_signup()`, wraps `register_user()` in `asyncio.to_thread` |
| Forgot Password | `forgot_password_screen.py` | Sync handler `do_reset()`, calls `request_password_reset()` directly |

Worth noting the inconsistency: signup runs the API call off the UI thread
via `asyncio.to_thread`, but login and forgot-password call it directly. On a
slow network, login and forgot-password will block the Flet event loop while
`httpx` waits for a response; signup won't. If this becomes noticeable,
aligning login/forgot-password to the same `asyncio.to_thread` pattern used
in signup (and in `generate_questions_screen.py`) would fix it.

### Session handling

`login_screen.py`'s `do_login()`, on success, does:

```python
page.session.store.set("current_user", result["user"]["username"])
```

Every other screen that needs "who is logged in" reads this same key —
`components/app_frame.py`'s drawer, `setup_ebooks_screen.py`'s
`submit_content()`, and `generate_questions_screen.py`'s
`generate_questions_async()` all call
`page.session.store.get("current_user")`. There's no other source of truth
for the current user anywhere in the app.

Logout (`components/app_frame.py`, `drawer_logout()`) just does
`page.session.store.remove("current_user")` and navigates to `/login`. No
backend call is made on logout — there's no server-side session to
invalidate, since sessions are entirely a Flet client-side construct.

### API client (`services/api_client.py`)

```python
login_user(username, password) -> dict
register_user(username, password) -> dict
request_password_reset(username) -> dict
```

All three use the shared 30-second `_TIMEOUT` and the shared
`_connection_error()` helper, which formats network failures as
`{"success": False, "error": f"Cannot reach the API server at {API_BASE_URL}. ({exc})"}`.
This is the same pattern `generate_questions()` uses, just with the longer
120-second timeout for that one call (see `README_AI_QUESTIONS.md`).

---

## Data Model

### Collection: `users`

```json
{
  "_id": ObjectId,
  "username": "user@example.com",
  "password": "$2b$12$...",
  "created_at": ISODate()
}
```

That's the entire schema — no roles, no profile fields, no email-verified
flag, no last-login timestamp. The unique index on `username` is created
lazily the first time `get_db()` runs (`_db.users.create_index("username", unique=True)`),
not via a migration script, so a fresh MongoDB instance gets the index
automatically on first connection.

---

## Known Gaps / Follow-Up Candidates

If this flow gets built out further, based on what's referenced but not
implemented:

1. Wire up real password reset (email or SMS) — the config already has a
   `ENABLE_PASSWORD_RESET_EMAIL` feature flag mentioned in the edukoreaiui
   README, but no code path uses it.
2. Either implement `MAX_LOGIN_ATTEMPTS` / `LOCKOUT_DURATION` or remove them
   from documentation/config so they stop implying protection that isn't there.
3. Decide what Guest mode should actually mean — right now it's a bare label
   with no backing record, which will surface confusingly anywhere
   `generated_by` or similar audit fields are displayed.
4. Consider aligning `login_screen.py` and `forgot_password_screen.py` to the
   `asyncio.to_thread` pattern already used in `signup_screen.py` for
   consistency.
