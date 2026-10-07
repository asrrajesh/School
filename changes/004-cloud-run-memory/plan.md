# Plan: Fix Cloud Run API deploy running out of memory at startup

- **Intent:** [intent.md](intent.md)
- **Spec:** [spec.md](spec.md)
- **Author:** Rajesh
- **Date:** 2026-10-07
- **Status:** approved

## Approach
One-line edit: append `--memory=2Gi --cpu-boost` to the `flags` of the "Deploy to Cloud Run" step in the workflow, then prove statically that nothing else changed. The real proof (a ready revision and `/health`) is a manual deploy by the developer after the merge to `main`.

## Files affected
| File | Change | Why |
|---|---|---|
| `.github/workflows/deploy-api.yml` (line 60) | `flags: --allow-unauthenticated --port=8080 --memory=2Gi --cpu-boost` | Req 1, 2 |
| `knowledge/nfr.md` (section 7) | Not in this stage; updated by `/update-knowledge` | Keep the as-is docs current |

No change to app code, `Dockerfile`, `.dockerignore`, other workflows or the hooks.

## Steps
1. **Edit the `flags` line** in `.github/workflows/deploy-api.yml`, adding ` --memory=2Gi --cpu-boost` after `--port=8080`. Nothing else. Serves req 1 and 2.
   - **Proof:** `git diff -- .github/workflows/deploy-api.yml` shows exactly one changed line, the `flags` line, with the new value.
2. **Validate the YAML and parity.** Parse the file with the PyYAML copy already in the scratchpad (`pylib`), and compare against `git show HEAD:.github/workflows/deploy-api.yml`: workflow name, triggers, the `env_vars` block and the sets of `secrets.*` / `vars.*` references are identical, and only `flags` differs. Serves req 2.
   - **Proof:** the script prints the file parses, everything matches, and the only differing key is `flags` with the expected string.
3. **Run the guard checks:** `python .claude/hooks/test_guards.py` (expect 0 failures) and `python .claude/skills/api-contract/scripts/check_endpoints.py` (expect OK, unchanged). Serves the "must not change" list.
4. **Hand over the manual verification.** After the PR is merged and `develop` is merged into `main`, the developer runs **Deploy API to Cloud Run**, expects the "Deploy to Cloud Run" step to succeed and `<service URL>/health` to return `{"status": "ok"}`. Serves req 3. Not run here; the implementation log will say so.

## Risks
- **What could break:**
  - 2 GiB may still be too small for torch plus the models, or startup may still exceed the probe window, and the revision fails again. That would be a follow-up, not a regression: the service already cannot start today.
  - A typo in the flags (the action passes them straight to `gcloud run deploy`) would fail the deploy step. The values `--memory=2Gi` and `--cpu-boost` are standard `gcloud run deploy` flags, and the spec's test is the real run.
  - Higher per-second cost while an instance runs.
- **Riskiest step:** step 4 (the manual deploy), because it is the only step that shows the memory is enough, and it cannot be run here.

## Alternatives considered
- `gcloud run services update --memory 2Gi` by hand: rejected as the fix, since the workflow should hold the setting; fine as a quick experiment.
- Switching `OCR_ENGINE=llm_vision` or moving the OCR preload out of startup: rejected by the intent (out of scope), possible follow-ups.
- Larger values (4 GiB, `--cpu=2`): not chosen without evidence; the developer chose 2 GiB.

## Rollback
`git revert` the `impl(004)` commit, or remove the two flags. Nothing else is touched. No runtime state is changed by this stage; the next deploy applies the flags.

## Open questions
1. None new. The spec's open question (whether probe or CPU settings also need changes) is deliberately left to a follow-up if the next deploy fails.

## Implementation log
- **Step 1:** done. The `flags` line in `.github/workflows/deploy-api.yml` is now `--allow-unauthenticated --port=8080 --memory=2Gi --cpu-boost`. Proof: `git diff` shows 1 line changed (1 insertion, 1 deletion), the `flags` line.
- **Step 2:** done. The file parses (PyYAML from the scratchpad). Compared with `git show HEAD:...`: the secrets/vars references are identical, the `env_vars` block is identical, and everything except `flags` in the workflow is identical.
- **Step 3:** done. `python .claude/hooks/test_guards.py` reports 0 failures; `check_endpoints.py` reports OK (18 endpoints, 17 client calls, 1 allowlisted).
- **Step 4:** not run here. The developer runs **Deploy API to Cloud Run** after the merge to `main` and checks `/health`.
- **Departures:** none.
- **Unverified overall:** that 2 GiB is enough and the revision becomes ready, the actual peak memory, the `/health` response and the cost impact.
