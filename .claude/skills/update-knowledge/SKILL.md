---
name: update-knowledge
description: Sync the knowledge/ folder with the code after a feature is implemented. Run manually, once per finished feature.
disable-model-invocation: true
argument-hint: "[path to the feature's intent.md]"
---

# Update knowledge after a feature

`knowledge/` describes the **current state** of EduKoreAI (functional-specification, data-model, api-specification, prompt-and-generation-rule, ui-behavior-and-design, nfr). After a feature ships, bring those files back in line with the code. `$ARGUMENTS` is the feature's `intent.md`, if given.

## Rules
- Describe what the code **does now**, not what was planned. Verify every claim by reading the code. Do not copy it from the intent.
- Edit existing sections in place. Do not append a changelog or a "new feature" section. Rewrite so each file reads as one coherent snapshot.
- Keep the existing conventions: **[placeholder]** for UI that does nothing, *(inferred)* for guessed purpose, and "Known gaps" lists for defects. Remove a gap only if the code now fixes it. Add new gaps you notice.
- Do not touch code. Only change files under `knowledge/` (and the status line of the intent file, step 6).
- If the intent and the code disagree (planned but not built, or built differently), document the code and tell the user about the difference.

## Steps

1. **Find the baseline.** Read the `Reverse-engineered on … (git <hash>)` line at the top of the knowledge files, or the last synced hash if a file already has one. Run `git log --oneline <hash>..HEAD` and `git diff --stat <hash>..HEAD -- edukoreaiapi edukoreaiui designsamples`. If the working tree has uncommitted changes, include them (`git diff HEAD`). If there is no usable hash, ask the user which commit to compare from.
2. **Read the intent** (if `$ARGUMENTS` is given) to learn what the feature was meant to change, then read the changed code to learn what it actually does.
3. **Map changes to knowledge files:**

   | Changed code | Update |
   |---|---|
   | `database/db.py`, new collections or fields, indexes, `fix_indexes.py` | `data-model.md` |
   | `routers/*.py`, `schemas.py`, `services/api_client.py` | `api-specification.md` (and check the UI client mapping section) |
   | `llm/**`, `ocr/**`, `services/question_service.py`, `services/paper_generator.py`, `services/ocr_service.py` | `prompt-and-generation-rule.md` |
   | `screens/**`, `components/**`, `main.py` (UI), `designsamples/**`, theme or config | `ui-behavior-and-design.md` |
   | New user-visible behavior, roles, flows, business rules | `functional-specification.md` |
   | Auth, security, config keys, timeouts, deployment files (`Dockerfile`, `.github/workflows/*`), tests, dependencies | `nfr.md` |

   A single feature usually touches several files. Check each one, since a data change often affects the API and functional docs too.
4. **Edit the knowledge files** following the rules above. Update tables, flows and the "gaps" lists.
5. **Update the header** of every knowledge file you changed: `Reverse-engineered on <date> (git <hash>)` becomes `Last synced <today's date> (git <current short hash>)`. Use `git rev-parse --short HEAD`. If you changed files that were not committed yet, say so in the header.
6. **Close the loop.** If an intent file was given, set its status line to `implemented` and add the date. Update `CLAUDE.md` only if commands, structure, endpoints list or architecture rules changed.
7. **Report** to the user: files changed, one line per change, any intent-versus-code differences, and anything you could not verify.

## Branch and commit

Branch model: `main` (release, merged and tagged manually by the user) and `develop` (integration) are fixed branches; never commit on them. Each change lives on its own branch `develop-<id>-<short-desc>` created from `develop`, and every workflow stage is its own commit on that branch.

Check the branch first: run `git branch --show-current`. It must be `develop-<id>-*` for this change. On `main` or `develop`, stop. If another `develop-<id>-*` branch exists, offer to switch to it (needs a clean working tree); otherwise tell the user the change has no branch. Take the id from the intent path in `$ARGUMENTS`.

Commit (never without asking):
1. Show `git status` and the proposed message `knowledge(<id>): <summary>`, and ask the user whether to commit. Stage only the files this stage produced (`knowledge/` and the intent's status line). Add the attribution trailer from the session reminder.
2. After committing, ask separately whether to push (`git push -u origin <branch>`). Never force-push.
