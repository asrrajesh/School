# REVIEW.md

Policy for reviewing pull requests in this repo, whether the reviewer is a person, `/code-review`, or an automated Claude review. Every PR into `develop` gets the same passes. The human reviewer keeps final approval.

## Context to read first
- The change folder `changes/<id>-<short-desc>/` named in the PR (`intent.md`, `spec.md`, `plan.md`). Not every PR has one (for example `docs/` workflow changes).
- `CLAUDE.md` for conventions, and `knowledge/` for the as-is behavior the change should keep or update.
- The policy skills in `.claude/skills/` are the review standards for their areas: `api-contract`, `security-rules`, `ui-conventions`, `llm-provider-rules`.

## Passes
Run all three on every PR. Report findings ranked by severity.

1. **Bugs and logic.** Wrong behavior, unhandled errors, broken edge cases, off-by-one and null handling, regressions in existing flows, changes that only work in one `UI_MODE`.
2. **Security.** Apply `security-rules`: secrets or personal data in code, logs or UI; client secret outside the API; password handling; widened CORS; a new production env var missing from `.github/workflows/deploy-api.yml` or `.env.example`; unvalidated input.
3. **Compliance with the change.**
   - Does the code do what `spec.md` requires, and follow the steps in `plan.md`? Flag extra scope and missing requirements.
   - API changes mirrored in `edukoreaiui/services/api_client.py` (run `python .claude/skills/api-contract/scripts/check_endpoints.py`).
   - UI changes follow `ui-conventions`; LLM/OCR changes follow `llm-provider-rules`.
   - `knowledge/` updated for behavior changes, with intent, spec and plan statuses consistent (`python .claude/scripts/check_change.py <id> --stage knowledge`).
   - Branch and commit conventions: `develop-<id>-<desc>`, one `<stage>(<id>): summary` commit per stage.

## Severity
- **Blocker:** security issue, data loss, broken login/generation flow, API and client out of sync, or the change contradicts its spec. Do not merge.
- **Major:** likely bug in a normal flow, missing error handling, missing knowledge update. Fix before merge unless the owner accepts the risk in the PR.
- **Minor:** unclear naming, small duplication, missing comment where the code is non-obvious. Fix or defer.
- **Nit:** style or preference. Report at most 3 per PR and only if nothing above was found elsewhere. There is no linter, so do not invent style rules.

## What not to flag
- Anything under `edukoreaiapi/apivenv/`, `edukoreaiui/uivenv/`, `designsamples/`, or generated files.
- Wording and formatting in `knowledge/` that does not change meaning.
- Known gaps already documented in `knowledge/` (for example no sessions/JWTs, no UI tests, no lint config) unless the PR makes them worse.
- Pre-existing issues outside the diff. Mention at most one as a follow-up.

## Output
For each finding: severity, file and line, one sentence on the problem, the concrete failure it causes, and a suggested fix. End with an overall verdict: approve, approve with minor items, or changes requested. State what could not be verified (for example no UI tests, no live MongoDB or LLM).

## Human reviewer
Decide whether the change matches the intended behavior and whether the remaining risk is acceptable. Merge only when no Blocker is open. Repeated findings go into `CLAUDE.md` ("Common mistakes") or the matching policy skill.
