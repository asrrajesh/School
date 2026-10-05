# Plan: Move GitHub Actions workflows to the repository root

- **Intent:** [intent.md](intent.md)
- **Spec:** [spec.md](spec.md)
- **Author:** Rajesh
- **Date:** 2026-10-05
- **Status:** approved

## Approach
Move both workflow files to the root with `git mv` (history kept), make the minimum path edits so they work from the repo root, then replace the old paths in the docs, skills and the hook self-test. Move first, then edit the YAML, then the references, so each step is a small, reviewable diff.

## Files affected
| File | Change | Why |
|---|---|---|
| `edukoreaiapi/.github/workflows/deploy.yml` -> `.github/workflows/deploy-api.yml` | `git mv`; Docker build gets context `edukoreaiapi` | Req 1, 2, 4 |
| `edukoreaiui/.github/workflows/build-apk.yml` -> `.github/workflows/build-apk.yml` | `git mv`; add job `defaults.run.working-directory: edukoreaiui`; "Locate built APK" step runs from the repo root and searches `edukoreaiui/build/apk` | Req 1, 3, 4 |
| `CLAUDE.md` (lines 37, 59) | New workflow paths; `deploy.yml` -> `deploy-api.yml` | Req 5 |
| `README.md` (lines 66-67) | New workflow paths | Req 5 |
| `REVIEW.md` (line 14) | New path | Req 5 |
| `.claude/skills/security-rules/SKILL.md` (lines 3, 14) | New path | Req 5 |
| `.claude/skills/llm-provider-rules/SKILL.md` (line 15) | `deploy.yml` -> `deploy-api.yml` | Req 5 |
| `.claude/hooks/test_guards.py` (line 29) | Sample command `gh workflow run deploy-api.yml` | Req 5 |
| `knowledge/nfr.md` (lines 53, 56) | Not in this stage; updated by `/update-knowledge` | Req 5 |

No change to `Dockerfile`, `.dockerignore`, `pyproject.toml`, app code or hook logic.

## Steps
1. **Move the files.** `mkdir .github/workflows`, then `git mv edukoreaiapi/.github/workflows/deploy.yml .github/workflows/deploy-api.yml` and `git mv edukoreaiui/.github/workflows/build-apk.yml .github/workflows/build-apk.yml`; remove the empty nested `.github` folders. Serves req 1.
   - **Proof:** `git ls-files '*/.github/*'` lists only the two root files; `ls edukoreaiapi/.github edukoreaiui/.github` fails (folders gone).
2. **Fix `deploy-api.yml`.** Change the "Build and push image" line to `docker build -t ${{ env.IMAGE }}:${{ github.sha }} edukoreaiapi`. Nothing else. Serves req 2 and 4.
   - **Proof:** `git diff -M HEAD -- .github/workflows/deploy-api.yml` shows exactly one changed line against the old file.
3. **Fix `build-apk.yml`.** Add under the job (next to `runs-on`): `defaults: run: working-directory: edukoreaiui`. In "Locate built APK" set `working-directory: .` and `find edukoreaiui/build/apk -name "*.apk"`, so the output path is workspace-relative for `upload-artifact`. Serves req 3 and 4.
   - **Proof:** `git diff -M` against the old file shows only those lines; every `run:` step that touches the project (pip install, `.env`, `flet build apk`) inherits the default.
4. **Validate both YAML files.** Parse them with PyYAML (not installed here, so install it into the scratchpad with `python -m pip install --target <scratchpad> pyyaml`, not into the project or global environment) and check that `on` (`workflow_dispatch`, with `build_mode` for the APK), the job names and the secrets/vars referenced are unchanged against the old files from `git show HEAD:<old path>`. Serves req 4.
   - **Proof:** both parse; a script that extracts every `secrets.*`, `vars.*` and `env_vars` entry gives the same set for old and new.
5. **Update the references** in `CLAUDE.md`, `README.md`, `REVIEW.md`, the two skills and `test_guards.py` (paths and `deploy.yml` -> `deploy-api.yml` as listed above). Serves req 5.
   - **Proof:** `grep -rnE "edukoreaiapi/\.github|edukoreaiui/\.github|deploy\.yml" . --exclude-dir=.git --exclude-dir=apivenv --exclude-dir=uivenv --exclude-dir=changes` shows only `knowledge/nfr.md` (left for `/update-knowledge`).
6. **Run the guard checks:** `python .claude/hooks/test_guards.py` (expect 0 failures) and `python .claude/skills/api-contract/scripts/check_endpoints.py` (expect OK, unchanged). Serves the "must not change" list.
7. **Hand over the manual verification.** The developer runs the APK workflow in debug mode, then the API deploy, once the change is on `main` (see the spec's Verification). Record in the implementation log that this was not run here.

## Risks
- **What could break:**
  - A missed root-relative path in the APK job. A `flet build apk` run from `edukoreaiui/` is untested, and the `upload-artifact` `path` ignores the job default, which is why step 3 makes the locate step output a workspace-relative path.
  - `docker build ... edukoreaiapi` uses `edukoreaiapi/` as the context, as the old `.` did, so the `Dockerfile` and `.dockerignore` behave the same.
  - The workflows have never run on GitHub, so first-run failures unrelated to the move (WIF trust for this repo, Android licenses) are possible.
  - Stale doc references. The grep in step 5 covers this.
- **Riskiest step:** step 3, because the APK path handling can only be proved by a real run. Step 4 only proves syntax and parity.

## Alternatives considered
- One combined workflow for both apps: rejected, different triggers, secrets and tooling (see the earlier discussion and the spec).
- `docker build -f edukoreaiapi/Dockerfile .`: rejected, a root context would ignore `edukoreaiapi/.dockerignore` and upload the whole repo.
- `cd edukoreaiui` in each APK step: rejected, `defaults.run.working-directory` is one setting and cannot miss a step.
- Leaving the old files in place as a copy: rejected by the intent.

## Rollback
`git revert` the `impl(003)` commit (it restores the nested files and removes the root ones). Nothing is deployed by this change, so there is no runtime state to undo.

## Open questions
1. PyYAML is not installed in this environment. Assumption: install it into the scratchpad only for the step 4 check (no project or global change). If that is unacceptable, the fallback is a manual diff review.

## Implementation log
- **Step 1:** done. Both files moved with `git mv` to `.github/workflows/deploy-api.yml` and `.github/workflows/build-apk.yml`; the empty nested `.github` folders are removed. Proof: `git ls-files '*/.github/*' '.github/*'` lists only the two root files; the nested folders no longer exist.
- **Step 2:** done. `deploy-api.yml` differs from the old file by one line: `docker build -t ... edukoreaiapi`. Proof: `git diff -M` shows 1 line changed.
- **Step 3:** done. `build-apk.yml` has job-level `defaults.run.working-directory: edukoreaiui`; "Locate built APK" has `working-directory: .` and `find edukoreaiui/build/apk`. Proof: `git diff -M` shows 6 lines added/changed (5 insertions, 1 replaced) and nothing else.
- **Step 4:** done. PyYAML installed into the scratchpad only (`pip install --target`). Both files parse; for each, workflow name, triggers (including the `build_mode` input) and the set of `secrets.*`/`vars.*` references are identical to the old files from `git show HEAD:<old path>`.
- **Step 5:** done. Paths updated in `CLAUDE.md`, `README.md`, `REVIEW.md`, `security-rules` and `llm-provider-rules` skills, and the sample command in `test_guards.py`. Proof: the grep for `edukoreaiapi/.github`, `edukoreaiui/.github` and `deploy.yml` (excluding `changes/` and venvs) returns only `knowledge/nfr.md` lines 53 and 56, left for `/update-knowledge`.
- **Step 6:** done. `python .claude/hooks/test_guards.py` reports 0 failures; `check_endpoints.py` reports OK (18 endpoints, 17 client calls, 1 allowlisted).
- **Step 7:** not run here. The developer triggers the APK workflow (debug first) and then the API deploy after the change is on `main`.
- **Departures:** none.
- **Unverified overall:** real GitHub runs of both workflows, the `flet build apk` run from `edukoreaiui/`, the WIF trust for `asrrajesh/School`.
