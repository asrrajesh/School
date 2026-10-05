---
name: wrap-up
description: Wrap up a finished change: raise the PR from develop-<id>-<desc> into develop and ask for review; once the developer confirms it is merged, verify the merge, delete the feature branch and return to an up-to-date develop. Run manually after /update-knowledge, and again after the merge.
disable-model-invocation: true
argument-hint: "[id]"
---

# Wrap up a change

The last phase of a change: get it reviewed and merged, then clean up so the developer can start the next task from a fresh `develop`. The skill is stateless: each run looks at the branch and the PR and does the next step.

## Workflow check

1. **Get the id** from `$ARGUMENTS` (a number; normalize to three digits). If it is missing, take it from the current branch name `develop-<id>-*`; if that does not work either, list the existing changes (folder, title, statuses) and ask.
2. Run `python .claude/scripts/check_change.py <id> --stage wrap-up`. It needs the branch `develop-<id>-*`, the intent, spec and plan all `implemented` (that is what `/update-knowledge` sets), and a `knowledge(<id>)` commit on the branch, so `/wrap-up` cannot run before the `/update-knowledge` phase is done and committed. If it prints `ERROR` about statuses, stop and tell the user to run `/update-knowledge changes/<id>-*/intent.md` first. If the only error is the branch (the user already switched away, usually after merging), rerun with `--any-branch`. Show any `WARNING`.
3. Find the feature branch: `git branch --list "develop-<id>-*"` (local) and `git ls-remote --heads origin "develop-<id>-*"` (remote). Never touch `main`, `develop` or any other branch.
4. Find the PR for that branch: `gh pr list --head <branch> --state all --json number,state,url,mergedAt,title`. If `gh` is not found in Bash on Windows, use PowerShell with `$env:Path += ";C:\Program Files\GitHub CLI"`. If `gh` is unavailable or not logged in, say so and fall back to asking the user (and to `git fetch` plus `git branch -r --merged origin/develop` for the merged check).

## Decide the phase from the PR state

| State | Phase |
|---|---|
| No PR | **A. Raise the PR** |
| PR open | Report the PR link and review state; ask the user to review and merge it, then to confirm here. Do nothing else. |
| PR merged | **B. Clean up** |
| PR closed, not merged | Stop and ask the user what to do (reopen, new PR, abandon). Delete nothing. |

## Phase A: raise the PR and ask for review

1. **Prerequisites.** The working tree must be clean (`git status --short`); if not, stop and ask. The branch must have the stage commits (`git log --oneline develop..HEAD`); list them. Warn if the `knowledge(<id>)` commit is missing.
2. **Push** the branch if it is not on origin or is ahead of it: show what will be pushed, ask, then `git push -u origin <branch>`. Never force-push.
3. **Write the PR** from the change files, never from memory:
   - Title: `<id>: <intent title>` (short).
   - Body: a Summary of what changed and why (from `intent.md` and `spec.md`), the files or areas touched, and a **Test plan** built from the spec's Verification and the plan's `## Implementation log`. Check only items that were actually run and passed; leave the rest unchecked and say why.
   - Link the change folder `changes/<id>-<short-desc>/`.
   - End the body with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
4. **Show the title and body and ask before creating** (it publishes content). Write the body to a file in the scratchpad directory and pass it with `--body-file`: `gh pr create --base develop --head <branch> --title "..." --body-file <file>`. Never pass the body inline with `--body`; on Windows PowerShell 5.1 quotes in the body break the arguments. Base is always `develop`, never `main`.
5. **Ask for review.** Give the PR link. Say the review should follow `REVIEW.md` (bugs and logic, security, compliance with the spec and plan), and offer to run `/code-review` on the branch first if the developer wants an AI pass. Ask them to review, merge when satisfied, and then confirm here (re-run `/wrap-up <id>` or say it is merged). Stop; do not merge the PR yourself.

## Phase B: clean up after the merge

1. **Confirm the merge.** The PR state must be `MERGED` (not just the user's word); show the PR number and merge time. If the user says it is merged but GitHub says otherwise, report the mismatch and stop.
2. **List what will be deleted** (local branch `<branch>`, and remote branch `origin/<branch>` if it still exists) and ask for one confirmation. Deleting the remote branch is a push to GitHub, so do not skip the question.
3. **Delete the remote feature branch first, only if it still exists** (GitHub may have deleted it on merge; then say so and skip): `git push origin --delete <branch>`. Do this while still on the feature branch: the repo's guard hook blocks every `git push` issued from `develop` or `main`.
4. **Leave the feature branch and delete it locally.** A checked-out branch cannot be deleted, so run `git checkout develop && git pull --ff-only`, then `git branch -d <branch>`. If git refuses because the PR was squash- or rebase-merged (the PR is already confirmed merged), use `git branch -D <branch>`. Delete nothing else. Never delete `main` or `develop`.
5. **Finish with a fresh `develop`:** run `git checkout develop && git pull` (already done in step 4; run it again so the developer sees the final state) and verify with `git branch --show-current`, `git status --short` and `git log --oneline -3`.
6. **Report** to the developer: PR merged, branches deleted, now on up-to-date `develop`, ready for the next `/create-intent`. Mention anything left over (unmerged local branches, uncommitted files).

## Rules

- Never commit in this skill, and never push to `develop` or `main`. The only pushes are the feature branch (phase A) and the remote feature-branch deletion (phase B), both after asking and both issued from the feature branch.
- Never merge the PR for the developer; merging is theirs.
- If anything is unexpected (dirty tree, wrong branch, PR for a different base), stop and ask instead of improvising.
