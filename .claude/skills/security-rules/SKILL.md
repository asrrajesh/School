---
name: security-rules
description: Use whenever changing authentication, signup/login, Google OAuth, password handling, config or .env files, secrets, CORS, or deployment settings (.github/workflows/deploy-api.yml, Dockerfile) in this repo.
---

# Security rules

Apply these before and after any change in the areas above. Details of current behavior and known gaps are in `knowledge/nfr.md` and `knowledge/api-specification.md`.

## Rules
1. **Secrets stay server-side.** `GOOGLE_CLIENT_SECRET` and every LLM key (`ANTHROPIC_API_KEY`, etc.) live only in the API's environment. The UI may hold `GOOGLE_CLIENT_ID` only. The OAuth code exchange stays in `POST /api/auth/google-callback`.
2. **Passwords are hashed with bcrypt** through `hash_password` / `check_password` in `edukoreaiapi/database/db.py`. Never store, log or return a plain or hashed password. Respect `PASSWORD_MIN_LENGTH`; usernames must match `EMAIL_PATTERN` or `MOBILE_PATTERN`.
3. **No secrets or personal data in logs, error messages, UI text or the repo.** `.env` and `.env.local` are gitignored; only `.env.example` files are committed, with placeholder values.
4. **New production env var.** Add it to the `env_vars` block and repo secrets in `.github/workflows/deploy-api.yml`, to `.env.example`, and to `config/config.py`. Otherwise it works locally and is missing on Cloud Run.
5. **CORS** origins come from `CORS_ORIGINS`; never widen to `*` to make something work.
6. **Validate input at the API boundary** (Pydantic models in `schemas.py`, explicit checks in routers/db). The UI's checks are for convenience only.

## Known gaps (do not assume they are fixed)
- There are no sessions or JWTs and no authorization checks: any caller can use every endpoint. Do not build features that assume a trusted user id from the client without flagging this.
- Do not weaken OS security (for example Smart App Control or code-integrity policy) to make something run; use the documented workaround (`UI_MODE=web`).

If a change needs an exception to any rule, state it in the PR description and ask the repo owner.
