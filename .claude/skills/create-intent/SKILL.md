---
name: create-intent
description: Turn a developer's feature requirements into changes/<id>-<short-desc>/intent.md. Run manually at the start of each new feature.
disable-model-invocation: true
argument-hint: "<feature requirements in your own words>"
---

# Create an intent file

Capture the requirements in `$ARGUMENTS` as a new `intent.md`. This is the first step of a feature: it records **what and why**, not how. Do not write or change application code.

If `$ARGUMENTS` is empty, ask the user to describe the feature and stop.

## Steps

1. **Ground it in the current system.** Read the `knowledge/` files that the request touches (see `CLAUDE.md` for the list). Work out which screens, endpoints, collections and rules are affected, and whether the request is **new** or **changes something that already exists**. For example, a login page already exists in this app. If so, say so in the intent and describe the change, not a rebuild.
2. **Pick the folder.** List `changes/` (create it if missing). The id is the highest existing three-digit prefix plus 1, zero-padded (`001` if none). The folder name is `<id>-<short-desc>`: 2–4 lowercase words joined by hyphens, taken from the request (for example `001-login`, `002-teacher-roles`). Create `changes/<id>-<short-desc>/intent.md`. Never overwrite an existing intent.
3. **Write the file** in the template below. Use the developer's own requirements as the source and keep their wording where it is specific (for example "username, password and submit button"). Do not invent requirements. If the developer left something open (for example "global standard" without defining it), record it under **Open questions** instead of guessing, and you may state the assumption you would make.
4. **Ask only if blocked.** If the request is too vague to write a meaningful Problem or Outcome, ask the user one to three short questions before writing. Otherwise write the draft and list the gaps as open questions.
5. **Report** the file path, a two-line summary, whether it is new or a change to existing behavior, which knowledge files it touches, and the open questions. Tell the user the next steps: review and edit the intent, set status to `approved`, implement, then run `/update-knowledge changes/<id>-<short-desc>/intent.md`.

## Branch and commit

Branch model: `main` (release, merged and tagged manually by the user) and `develop` (integration) are fixed branches; never commit on them. Each change lives on its own branch `develop-<id>-<short-desc>` created from `develop`, and every workflow stage is its own commit on that branch.

Create the branch **before writing the file** (after step 2 has picked the id and name): require a clean working tree, run `git checkout develop`, `git pull --ff-only`, then `git checkout -b develop-<id>-<short-desc>` (for example `develop-001-ui-not-launching`). If the branch already exists or `develop` is missing, stop and tell the user.

Commit (never without asking):
1. Show `git status` and the proposed message `intent(<id>): <summary>`, and ask the user whether to commit. Stage only the files this stage produced (`changes/<id>-<short-desc>/intent.md`). Add the attribution trailer from the session reminder.
2. After committing, ask separately whether to push (`git push -u origin <branch>`). Never force-push.

## Template

```markdown
# Intent: <feature title>

- **ID:** <id>
- **Author:** <git user name; use `git config user.name`>
- **Date:** <today, YYYY-MM-DD>
- **Status:** draft
- **Type:** new feature | change to existing behavior

## Developer request
> <the exact text of $ARGUMENTS, verbatim>

## Problem
<The pain point or gap, in plain language. State the current behavior from knowledge/ when this changes something that exists.>

## Proposed outcome
<What should be true when this is done. Concrete, observable, and in the developer's terms. Use a short list of behaviors or acceptance criteria where the request gives them.>

## Affected users and systems
- **Users:** <who uses it>
- **Screens / UI:** <files or screens, from knowledge/ui-behavior-and-design.md>
- **API:** <endpoints added or changed, from knowledge/api-specification.md>
- **Data:** <collections or fields, from knowledge/data-model.md>
- **AI / prompts:** <only if relevant>
- **Knowledge files to update afterwards:** <list>

## Constraints
<Limits that apply: rules from CLAUDE.md that matter here (for example mirror API changes in api_client.py, use the provider factories), existing behavior to preserve, and anything the developer stated.>

## Open questions
1. <unresolved item, with the assumption you would make if any>
```

Keep sections short. Omit a line in "Affected users and systems" that does not apply rather than writing "n/a" for each.
