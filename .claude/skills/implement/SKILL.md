---
name: implement
description: Implement the approved changes/<id>-<short-desc>/plan.md in the code, step by step, with proofs, then ask the developer to approve the implementation. Run manually after the plan is approved.
disable-model-invocation: true
argument-hint: "<id>"
---

# Implement an approved plan

Carry out `changes/<id>-<short-desc>/plan.md` in the application code. The intent says why, the spec says what must be true, the plan says how: this skill does the how, **exactly as planned**, proves each step, and stops for the developer's approval before the knowledge sync.

## Workflow check

Once you have the id, run `python .claude/scripts/check_change.py <id> --stage impl`. It requires the branch `develop-<id>-*` and an `approved` spec and plan. If it prints `ERROR`, stop and tell the user what to fix first (for example approve the plan); do not work around it. Show any `WARNING`.

## Steps

1. **Get the id** from `$ARGUMENTS` (a number; normalize to three digits). If missing, list the existing changes (folder, title, spec and plan status) and ask. Find `changes/<id>-*/`.
2. **Read everything first:** `intent.md`, `spec.md`, `plan.md`, `CLAUDE.md`, the `knowledge/` files the plan touches, and every file the plan lists under **Files affected**. Verify the plan still matches the code. If it does not (files moved, assumptions false), stop and suggest `/update-plan <id> ...` instead of improvising.
3. **Apply the policy skills** that match the files you are changing (`api-contract`, `security-rules`, `ui-conventions`, `llm-provider-rules`) and follow their rules.
4. **Implement the plan's steps in order.** For each step:
   - make only the changes the step describes; no extra features, refactors or cleanup outside the plan
   - run the step's **Proof** (command or manual check) and record the real result
   - if a proof fails, fix the cause within the step's scope and re-run it; do not weaken or skip the proof
5. **Handle departures.** If the work must differ from the plan (a better approach, a new file, a different order), stop, explain why, and ask the developer. If they agree, record it with `/update-plan <id> ...` (or ask them to run it) before continuing. Anything that contradicts the spec goes back to `/update-spec` first.
6. **Run the spec's Verification items** and any relevant existing tests or checks (for example `check_endpoints.py` for API changes). State what could not be verified (no UI tests, no live MongoDB or LLM, desktop client blocked, and so on). Never claim a check passed that was not run.
7. **Write the implementation log.** Add or extend an `## Implementation log` section at the end of `plan.md`, one line per plan step with its proof result, plus any departures and unverified items. Do not change the plan's steps or its status.
8. **Ask for approval.** Report to the developer: files changed, each step's proof result, departures, and what is unverified. Ask them to review the diff (`git diff`) and approve the implementation. Do not commit before they approve, and do not run `/update-knowledge` yourself.
9. **After approval,** commit as below. Then tell the user the next step is to run `/update-knowledge changes/<id>-<short-desc>/intent.md` themselves (it is a manual command), followed by pushing and opening the PR into `develop`.

If the developer asks for changes instead of approving, make them within the plan's scope (or go through step 5), re-run the affected proofs, update the log, and ask again.

## Branch and commit

Branch model: `main` (release, merged and tagged manually by the user) and `develop` (integration) are fixed branches; never commit on them. The change lives on `develop-<id>-<short-desc>`, and every workflow stage is its own commit on that branch.

The branch is checked by the workflow check above. App-code edits are also gated by a hook that runs the same check.

Commit (never without asking):
1. Show `git status` and the proposed message `impl(<id>): <summary>`, and ask whether to commit. Stage the code files the plan lists, the tests you added, and `plan.md` (its implementation log). Add the attribution trailer from the session reminder. Several `impl(<id>)` commits are fine for large plans (one per logical group of steps).
2. After committing, ask separately whether to push (`git push -u origin <branch>`). Never force-push.
