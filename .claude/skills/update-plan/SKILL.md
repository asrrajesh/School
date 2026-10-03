---
name: update-plan
description: Revise an existing changes/<id>-<short-desc>/plan.md, including recording departures made during implementation. Run manually, as often as needed.
disable-model-invocation: true
argument-hint: "<id> <what to change or add>"
---

# Update a plan file

Revise an existing plan with the changes in `$ARGUMENTS`. Expected form: `<id> <update>`. Do not write or change application code.

## Steps

1. **Get the id.** The first word must be a number (normalize to three digits). If missing, list existing changes (folder, title, statuses) and ask.
2. **Find the plan** at `changes/<id>-*/plan.md`. If none exists, point to `/create-plan` and stop.
3. **Get the update text** (everything after the id). If empty, ask what should change.
4. **Check the status.** `draft`: proceed. `approved`: proceed; if implementation has not started, set it back to `draft` and tell the user. If implementation is under way, keep `approved` and record the departure (step 6). `implemented`: ask first.
5. **Check against the spec.** Read the plan and `spec.md`. If the update contradicts or exceeds the spec, say so and suggest `/update-spec <id> ...` first.
6. **Edit in place** so the plan reads as one coherent current document. Keep the header links, Author and Date. When recording a departure made during implementation, state what changed, why, and the effect on later steps and proofs. Do not invent scope; put vague points under **Open questions**. Say what was removed if anything was.
7. **Log the revision.** Add or extend `## Revision history` at the end (newest last): `- <YYYY-MM-DD> — <git user name> — <summary>. Request: "<update text>"`. Add or update a `- **Last updated:** <date>` header line under Status.
8. **Report** the path, sections changed, status change and why, and any conflicts or new open questions.

Do not commit unless the user asks.
