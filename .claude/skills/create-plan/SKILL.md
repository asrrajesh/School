---
name: create-plan
description: Turn an approved changes/<id>-<short-desc>/spec.md (with its intent.md) into an implementation plan.md in the same folder. Run manually before implementing.
disable-model-invocation: true
argument-hint: "<id>"
---

# Create an implementation plan

Produce `changes/<id>-<short-desc>/plan.md`. The spec says what must be true; the plan says **which files change, in what order, and how each step is proved**. Work read-only on the codebase (as in plan mode): the only file you write is `plan.md`. Do not change application code.

## Steps

1. **Get the id** from `$ARGUMENTS` (a number; normalize to three digits). If missing, list the existing changes (folder, title, intent and spec status) and ask. Find `changes/<id>-*/`; it needs `intent.md` and `spec.md`, otherwise point to `/create-intent` or `/create-spec` and stop.
2. **Check statuses.** The spec must be `approved`; if `draft`, stop and ask the user to approve it (or confirm proceeding). If the spec or intent is `implemented`, stop and ask. If `plan.md` exists, do not overwrite it; point to `/update-plan`.
3. **Ground it.** Read the intent, the spec, `CLAUDE.md`, the `knowledge/` files they touch, and every code file the change will touch. Verify facts by inspection; do not rely on the spec's claims alone.
4. **Interrogate your own plan** before writing it: what could this change break, which step is riskiest, what alternatives exist. Put the answers in the plan.
5. **Write `plan.md`** using the template below. Keep it as short as the change allows. Do not add scope beyond the spec; if the plan reveals a gap or conflict in the spec, record it under **Open questions** and suggest `/update-spec`.
6. **Report** the path, a short summary, the riskiest step, open questions, and next steps: review, set status to `approved`, implement step by step (run `/update-plan <id> ...` if the work departs from the plan), then `/update-knowledge changes/<id>-<short-desc>/intent.md`.

## Branch and commit

Branch model: `main` (release, merged and tagged manually by the user) and `develop` (integration) are fixed branches; never commit on them. Each change lives on its own branch `develop-<id>-<short-desc>` created from `develop`, and every workflow stage is its own commit on that branch.

Check the branch first: run `git branch --show-current`. It must be `develop-<id>-*` for this change. On `main` or `develop`, stop. If another `develop-<id>-*` branch exists, offer to switch to it (needs a clean working tree); otherwise tell the user the change has no branch. Do this before step 1's other work.

Commit (never without asking):
1. Show `git status` and the proposed message `plan(<id>): <summary>`, and ask the user whether to commit. Stage only the files this stage produced (`changes/<id>-*/plan.md`). Add the attribution trailer from the session reminder.
2. After committing, ask separately whether to push (`git push -u origin <branch>`). Never force-push.

## Template

```markdown
# Plan: <title, same as the intent>

- **Intent:** [intent.md](intent.md)
- **Spec:** [spec.md](spec.md)
- **Author:** <git config user.name>
- **Date:** <YYYY-MM-DD>
- **Status:** draft

## Approach
<Two or three sentences: the chosen strategy.>

## Files affected
| File | Change | Why |
|---|---|---|

## Steps
1. <Ordered, small, individually verifiable. Say which spec requirement each step serves.>
   - **Proof:** <command or manual check and expected result>

## Risks
- **What could break:** <...>
- **Riskiest step:** <step number and why>

## Alternatives considered
- <Option and why it was not chosen.>

## Rollback
<How to undo the change.>

## Open questions
1. <Unresolved item, with the assumption made.>
```
