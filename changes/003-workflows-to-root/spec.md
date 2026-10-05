# Spec: Move GitHub Actions workflows to the repository root

- **Intent:** [intent.md](intent.md)
- **Author:** Rajesh
- **Date:** 2026-10-05
- **Status:** implemented (2026-10-05)

## Summary
Move the two workflows from the nested `.github/` folders to the repo root as `deploy-api.yml` and `build-apk.yml`, adjusting only the paths that assumed the app folder was the repo root. Triggers, secrets, vars, `env_vars` and deploy targets stay as they are, and the old nested folders and the references to them go away.

## Findings
- `git ls-files` shows exactly two workflow files, `edukoreaiapi/.github/workflows/deploy.yml` and `edukoreaiui/.github/workflows/build-apk.yml`, both from the initial commit. There is no root `.github/`. GitHub only reads the root, so neither can run.
- `deploy.yml` (manual, environment `PROD`): the only root-relative step is `docker build -t $IMAGE:$SHA .` (line 50). `edukoreaiapi/Dockerfile` does `COPY requirements.txt .` and `COPY . .`, so it needs `edukoreaiapi/` as its build context. `edukoreaiapi/.dockerignore` (which excludes `.github/`, `.env`, `tests/`) is only honored when that folder is the context. Everything else (auth, `deploy-cloudrun`, `env_vars`, `flags`) is path-independent.
- `build-apk.yml` (manual, input `build_mode`): root-relative steps are `pip install -r requirements.txt` (line 54), `cat <<EOF > .env` (line 59), `flet build apk ...` (line 83, which reads `pyproject.toml`, `main.py` and `resources/` from the working directory), and `find build/apk` (line 89). `edukoreaiui/pyproject.toml` exists; `build/` is gitignored. The artifact `path` is the located file, so it works as long as `find` returns a workspace-relative path.
- References to the old paths: `CLAUDE.md:37`, `CLAUDE.md:59` (says `deploy.yml`), `README.md:66-67`, `REVIEW.md:14`, `knowledge/nfr.md:53,56`, `.claude/skills/security-rules/SKILL.md:3,14`, `.claude/skills/llm-provider-rules/SKILL.md:15` (`deploy.yml`), `.claude/hooks/test_guards.py:29` (sample command only). `.claude/skills/update-knowledge/SKILL.md:36` uses the generic `.github/workflows/*`, which is already correct. `guard_edit.py` skips `.github` parts and the root `.github/` is outside both app folders, so editing workflows is not blocked.
- `deploy.yml`'s header comment still says "see chat/README" and lists the required secrets; it stays accurate.
- Not verifiable here: that the secrets, vars and `PROD` environment exist, and that the runs succeed. The developer confirmed the variables exist and will trigger the runs manually.

## Requirements
1. `.github/workflows/deploy-api.yml` and `.github/workflows/build-apk.yml` exist at the repo root. `edukoreaiapi/.github/` and `edukoreaiui/.github/` no longer exist.
2. `deploy-api.yml` is identical to the old `deploy.yml` except for the Docker build path: the image builds with `edukoreaiapi/` as the build context, so the `Dockerfile` and `edukoreaiapi/.dockerignore` apply as before.
3. `build-apk.yml` is identical to the old file except that the Python install, `.env` creation, `flet build apk` and APK lookup run in `edukoreaiui/`, and the uploaded artifact is still found and uploaded.
4. Triggers are unchanged (both `workflow_dispatch`; the APK keeps the `build_mode` input with the same default). Workflow `name:`, secrets, vars, `env_vars`, `environment: PROD`, the GCP settings and the artifact name are unchanged.
5. No references to `edukoreaiapi/.github/`, `edukoreaiui/.github/` or the filename `deploy.yml` remain in `CLAUDE.md`, `README.md`, `REVIEW.md`, the skills, hooks or `knowledge/`, except in `changes/` records.

## Design
- `git mv edukoreaiapi/.github/workflows/deploy.yml .github/workflows/deploy-api.yml` and `git mv edukoreaiui/.github/workflows/build-apk.yml .github/workflows/build-apk.yml` (keeps history), then remove the empty nested `.github` folders.
- `deploy-api.yml`: change step "Build and push image" to `docker build -t ${{ env.IMAGE }}:${{ github.sha }} edukoreaiapi` (context path as the last argument). Chosen over `-f edukoreaiapi/Dockerfile .` because with a root context the app's `.dockerignore` would be ignored and the whole repo would be sent to Docker.
- `build-apk.yml`: add `defaults: run: working-directory: edukoreaiui` at job level, which covers the pip install, `.env` creation, `flet build apk` and APK lookup (`find build/apk` becomes relative to `edukoreaiui/`). For the "Locate built APK" step, output the path with the folder prefix (`find edukoreaiui/build/apk` run with `working-directory: .` for that step) so `upload-artifact` gets a workspace-relative path, because `with: path:` does not use `defaults.run.working-directory`. The Flutter/Java/Python/apt steps do not depend on the folder. Chosen over `cd` in every step because it is one setting and hard to miss a step.
- Doc and skill edits: replace the old paths with `.github/workflows/deploy-api.yml` and `.github/workflows/build-apk.yml`; `deploy.yml` becomes `deploy-api.yml` in `CLAUDE.md:59`, `llm-provider-rules/SKILL.md:15` and `test_guards.py:29`. `knowledge/nfr.md` is updated by `/update-knowledge`, not in the implementation stage.

## Out of scope / must not change
- Triggers, secrets, vars, `env_vars`, `PROD` environment, regions, image name, service name, Flutter/Java/Python versions.
- `Dockerfile`, `.dockerignore`, `pyproject.toml`, application code, the guard hooks' behavior (only the sample command in the self-test text changes).
- PR CI check, post-deploy health check, rollback runbook, web deployment of the UI.

## Verification
- Static (done by Claude): both YAML files parse (`python -c "import yaml..."` or equivalent); `git ls-files '*/.github/*'` returns nothing and `ls .github/workflows` shows the two files; `grep -rn` for `edukoreaiapi/.github`, `edukoreaiui/.github` and `deploy.yml` outside `changes/` and venvs returns nothing; `python .claude/hooks/test_guards.py` reports 0 failures; `git diff -M` shows each moved file with only the intended lines changed.
- Manual (developer, after the change is merged into `main`, since `workflow_dispatch` workflows are listed only from the default branch): in the Actions tab run **Build Android APK** (debug first, it is quicker) and confirm it produces the artifact; then run **Deploy API to Cloud Run** and confirm the service deploys and `/health` responds.
- Not verifiable here: real runs, the GCP Workload Identity Federation trust for this repo, and whether the Flutter/APK build works from `edukoreaiui/` (it was never run).

## Flagged concerns
- The workflows have never run on GitHub, so problems unrelated to the move (for example the WIF provider not trusting `asrrajesh/School`, the Flutter version, Android licenses) may only appear on the first run.
- The deploy workflow ships to production. Moving it makes it triggerable for the first time; it stays manual with the `PROD` environment, and the guard hook still blocks Claude from triggering it.
- `workflow_dispatch` workflows only appear in the Actions tab once the file is on the default branch (`main`); verification depends on you merging `develop` into `main`.

## Open questions
None.
