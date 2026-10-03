---
name: update-spec
description: Revise an existing changes/<id>-<short-desc>/spec.md with new or changed requirements or design decisions. Run manually, as often as needed.
disable-model-invocation: true
argument-hint: "<id> <what to change or add>"
---

# Update a spec file

Revise an existing spec with the changes in `$ARGUMENTS`. Expected form: `<id> <update>`. Do not write or change application code.

## Steps

1. **Get the id.** The first word must be a number (normalize to three digits). If missing, list existing changes (folder, title, intent and spec status) and ask.
2. **Find the spec** at `changes/<id>-*/spec.md`. If none exists, say so and point to `/create-spec`. Do not create one.
3. **Get the update text** (everything after the id). If empty, ask what should change.
4. **Check the status.** `draft`: proceed. `approved`: proceed and set it back to `draft`, telling the user. `implemented`: ask first: (a) revise anyway, (b) open a new change with `/create-intent`.
5. **Check against the intent.** Read the spec and its `intent.md`. If the update contradicts or goes beyond the intent, say so and suggest `/update-intent <id> ...` first rather than letting them drift apart.
6. **Ground it.** Re-read the code and `knowledge/` the update touches; verify claims.
7. **Edit in place** so the spec reads as one coherent current document. Keep the header's Intent link, Author and Date. Do not invent requirements; record vague or conflicting points under **Open questions**. Do not delete earlier content unless the update replaces it, and say what was removed.
8. **Log the revision.** Add or extend a `## Revision history` section at the end (newest last): `- <YYYY-MM-DD> — <git user name> — <summary>. Request: "<update text>"`. Add or update a `- **Last updated:** <date>` header line under Status.
9. **Report** the path, sections changed, status change and why, conflicts or new open questions.

## Branch and commit

Branch model: `main` (release, merged and tagged manually by the user) and `develop` (integration) are fixed branches; never commit on them. Each change lives on its own branch `develop-<id>-<short-desc>` created from `develop`, and every workflow stage is its own commit on that branch.

Check the branch first: run `git branch --show-current`. It must be `develop-<id>-*` for this change. On `main` or `develop`, stop. If another `develop-<id>-*` branch exists, offer to switch to it (needs a clean working tree); otherwise tell the user the change has no branch. Do this before step 1's other work.

Commit (never without asking):
1. Show `git status` and the proposed message `spec(<id>): update - <summary>`, and ask the user whether to commit. Stage only the files this stage produced (`changes/<id>-*/spec.md`). Add the attribution trailer from the session reminder.
2. After committing, ask separately whether to push (`git push -u origin <branch>`). Never force-push.
