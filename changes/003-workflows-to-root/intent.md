# Intent: Move GitHub Actions workflows to the repository root

- **ID:** 003
- **Author:** Rajesh
- **Date:** 2026-10-05
- **Status:** approved
- **Type:** change to existing behavior

## Developer request
> Move the GitHub Actions workflows to the repository root so GitHub can run them.
>
> Today they live in edukoreaiapi/.github/workflows/deploy.yml (Cloud Run deploy, manual) and edukoreaiui/.github/workflows/build-apk.yml (APK build). GitHub only reads .github/workflows/ at the repo root, so neither workflow ever runs in asrrajesh/School.
>
> Scope:
> - Move them to .github/workflows/deploy-api.yml and .github/workflows/build-apk.yml (two files, one per app).
> - Fix paths so each works from the repo root (Docker build context edukoreaiapi/, working-directory edukoreaiui for the APK build, requirements and cache paths).
> - Keep the triggers as they are (deploy stays manual) and keep the secrets and env_vars they already use.
> - Update the references to the old paths in CLAUDE.md and the skills (security-rules, README) and in knowledge/ if mentioned.
> - Remove the old nested .github folders.
>
> Out of scope: a PR CI check, post-deploy health check, rollback runbook, and web deployment of the UI (separate changes).
>
> Open points to confirm: whether the repo secrets and variables the workflows use exist in asrrajesh/School, and how to verify (you trigger a manual run, since the guard hook blocks me from running gh workflow run).

## Problem
The repo `asrrajesh/School` is a single repository, but the two workflows sit in nested `.github/workflows/` folders under `edukoreaiapi/` and `edukoreaiui/` (leftovers from when each app had its own repo). GitHub only reads workflows at the repo root, so neither the Cloud Run deploy nor the APK build appears in the Actions tab or can be triggered. `knowledge/nfr.md` documents both as working manual workflows.

Both files also assume the app folder is the repo root. `deploy.yml` runs `docker build -t ... .` and `build-apk.yml` runs `pip install -r requirements.txt`, writes `.env`, runs `flet build apk` and searches `build/apk`, all from the checkout root.

## Proposed outcome
- `.github/workflows/deploy-api.yml` and `.github/workflows/build-apk.yml` exist at the repo root and show up in the Actions tab.
- Each still does what it does today and only its paths change: the API image builds from `edukoreaiapi/` and the APK steps run in `edukoreaiui/` (install, `.env` creation, `flet build apk`, APK lookup and upload path).
- Triggers are unchanged: both stay manual (`workflow_dispatch`, APK keeps its release/debug input). Secrets, vars, `env_vars`, environment `PROD`, and the GCP settings are unchanged.
- The old `edukoreaiapi/.github/` and `edukoreaiui/.github/` folders are removed.
- References to the old paths are updated.

## Affected users and systems
- **Users:** the developer/owner who triggers deploys and APK builds.
- **Deployment:** the two workflow files above. `edukoreaiapi/.dockerignore` lists `.github/` (harmless once the workflow is outside the build context; check during spec).
- **Docs and tooling referencing the old paths:** `CLAUDE.md` (Architecture/Deploy, Common mistakes), `README.md` (Deployment), `REVIEW.md` (security pass), `.claude/skills/security-rules/SKILL.md`, `.claude/skills/llm-provider-rules/SKILL.md`, `.claude/skills/update-knowledge/SKILL.md`, `.claude/hooks/test_guards.py` (sample command only).
- **Knowledge files to update afterwards:** `knowledge/nfr.md` (deployment section).
- No screens, API, data or AI/prompt changes.

## Constraints
- Do not change triggers, secrets, vars, `env_vars` or deploy targets. Any production env var rule from `CLAUDE.md` still applies (`env_vars` and repo secrets).
- Deploy stays manual. The guard hook blocks Claude from running `gh workflow run`, so verification of a real run is done by the developer.
- `guard_edit.py` skips `.github` paths and the root `.github/` is outside the app folders, so editing workflows is not blocked.
- Deploy-stage extras (PR CI check, post-deploy health check, rollback runbook) and web deployment of the UI are separate changes.

## Open questions
None. Resolved by the developer on 2026-10-05:
1. All secrets, vars and the `PROD` environment already exist in `asrrajesh/School`.
2. The developer verifies manually by triggering each workflow from the Actions tab once the change is on the default branch. Claude only does static checks (YAML parses, paths exist, no old-path references remain).
3. The old nested workflows are not kept; git history has them.
