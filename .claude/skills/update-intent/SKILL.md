---
name: update-intent
description: Revise an existing changes/<id>-<short-desc>/intent.md with new or changed requirements. Run manually, as often as needed.
disable-model-invocation: true
argument-hint: "<id> <what to change or add>"
---

# Update an intent file

Revise an existing intent with the requirements in `$ARGUMENTS`. Expected form: `<id> <update requirements>`, for example `001 add a "remember me" checkbox and show an error after 3 failed attempts`. Do not write or change application code.

## Steps

1. **Get the id.** Take the first word of `$ARGUMENTS`. It counts as an id only if it is a number (`1`, `01` or `001`; normalize to three digits).
   - If there is no id, **stop and ask the user for it.** List the existing intents (folder name, title and status from each `intent.md`) to help them choose. Do nothing else until they answer.
2. **Find the intent.** Look for `changes/<id>-*/intent.md`.
   - If none exists, say so, list the existing intents, and ask the user which one they meant. Do not create a new intent; point to `/create-intent` for that.
3. **Get the update text.** Everything after the id is the update. If it is empty, ask the user what should change, then continue.
4. **Check the status line.**
   - `draft`: proceed.
   - `approved`: proceed, and set the status back to `draft` because the agreed scope has changed. Tell the user.
   - `implemented`: **ask first.** The feature is already built, so changing the intent no longer matches the code. Offer: (a) revise it anyway, (b) open a new intent with `/create-intent` that refers to this one. Follow the user's choice.
5. **Ground it.** Read the intent in full, then the `knowledge/` files it touches (see `CLAUDE.md`) so new statements are consistent with how the system works today.
6. **Edit in place.** Apply the update to the relevant sections (Problem, Proposed outcome, Affected users and systems, Constraints, Open questions) so the file reads as one coherent current intent. Rules:
   - Keep `ID`, `Author`, `Date` and the original **Developer request** quote unchanged.
   - Do not invent requirements. If the update is vague or conflicts with an earlier statement, record it under **Open questions** (with an assumption if useful) and tell the user.
   - Resolve an open question only when the update clearly answers it; move the answer into the right section.
   - Do not delete earlier requirements unless the update clearly replaces or removes them. When it does, say which ones in the report.
7. **Log the revision.** Add (or extend) a `## Revision history` section at the end, newest last:
   ```markdown
   ## Revision history
   - <YYYY-MM-DD> — <git user name> — <one-line summary of the change>. Request: "<the update text, verbatim>"
   ```
   Add a `- **Last updated:** <date>` line to the header, below Status, if it is not there; otherwise change its date.
8. **Report** to the user: the file path, the sections changed, the status (and why it changed, if it did), any conflicts or new open questions, and whether other knowledge files are now affected. Remind them that approving and then implementing is next, followed by `/update-knowledge <path>`.

Do not commit unless the user asks.
