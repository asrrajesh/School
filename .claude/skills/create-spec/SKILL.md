---
name: create-spec
description: Turn an approved changes/<id>-<short-desc>/intent.md into a requirements and design spec.md in the same folder. Run manually after the intent is approved.
disable-model-invocation: true
argument-hint: "<id>"
---

# Create a spec from an intent

Produce `changes/<id>-<short-desc>/spec.md` next to the intent. The intent says **what and why**; the spec says **exactly what must be true and how it will be built and verified**. Do not write or change application code.

## Steps

1. **Get the id** from `$ARGUMENTS` (a number; normalize to three digits). If missing, list the existing changes (folder, title, status) and ask. Find `changes/<id>-*/intent.md`; if none, say so and stop.
2. **Check the intent status.** `approved`: proceed. `draft`: stop and ask the user to review and approve it first (or to confirm proceeding anyway). `implemented`: stop and ask. If `spec.md` already exists, do not overwrite it; point to `/update-spec`.
3. **Ground it.** Read the intent in full, `CLAUDE.md`, and the `knowledge/` files it touches. Then read the actual code the change will touch. Verify facts (including root causes for bugs) by inspecting or reproducing, not by assuming. Record what you verified.
4. **Write `spec.md`** using the template below. Keep it as short as the change allows; a small fix needs a one-page spec. Do not invent requirements beyond the intent. Anything unresolved or any policy/security/UX concern goes under **Flagged concerns** and **Open questions** with an assumption.
5. **Report** the path, a short summary, the flagged concerns and open questions, and next steps: review against the intent, resolve concerns, set spec status to `approved`, implement, then `/update-knowledge changes/<id>-<short-desc>/intent.md`.

Do not commit unless the user asks.

## Template

```markdown
# Spec: <title, same as the intent>

- **Intent:** [intent.md](intent.md)
- **Author:** <git config user.name>
- **Date:** <YYYY-MM-DD>
- **Status:** draft

## Summary
<Two or three sentences: what will change and why.>

## Findings
<Verified facts from the code or reproduction, including the root cause for bugs. Cite files and lines.>

## Requirements
1. <Numbered, testable statements derived from the intent's Proposed outcome.>

## Design
<Files and functions to change, endpoints/schemas/collections touched, and the chosen approach with a one-line reason. Mention rejected alternatives only if relevant. Include the api_client.py mirror when the API changes.>

## Out of scope / must not change
- <Existing behavior to preserve.>

## Verification
- <How to prove each requirement: commands, manual steps, expected results.>

## Flagged concerns
- <Security, UX, compliance or risk items needing an owner's decision. "None" if none.>

## Open questions
1. <Unresolved item, with the assumption made.>
```
