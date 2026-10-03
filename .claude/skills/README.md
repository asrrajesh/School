# Project skills

Skills in `.claude/skills/<name>/SKILL.md` are shipped with the repo and reviewed through pull requests like code. Owner: Rajesh approves every skill change.

## Workflow skills (manual, type the slash command)
They create branches and commits, so they are never triggered automatically (`disable-model-invocation: true`).

| Skill | Purpose |
|---|---|
| `/create-intent`, `/update-intent` | `changes/<id>-<desc>/intent.md`; creates the `develop-<id>-<desc>` branch |
| `/create-spec`, `/update-spec` | `spec.md` (requirements and design) |
| `/create-plan`, `/update-plan` | `plan.md` (files, steps, risks, proofs) |
| `/update-knowledge` | Sync `knowledge/` with the code after implementation |

## Policy skills (automatic, by trigger)
Claude loads them when a task matches the "Use whenever ..." description.

| Skill | Applies to |
|---|---|
| `api-contract` | Router, `schemas.py` and `api_client.py` changes; includes `scripts/check_endpoints.py` |
| `security-rules` | Auth, OAuth, passwords, config/`.env`, secrets, CORS, deployment |
| `ui-conventions` | Screens, components, routes, theme, startup in `edukoreaiui/` |
| `llm-provider-rules` | LLM/OCR providers, prompts, question generation |

## Adding or changing a skill
1. Write it from an existing rule or documented mistake; keep rules short and point to `knowledge/` instead of copying it.
2. Use a "Use whenever ..." description for policy skills. Add a script under `scripts/` when a rule can be checked mechanically.
3. Test the trigger with at least three differently worded requests in a fresh session and record the result below.
4. Open a PR into `develop`; the owner approves it.
5. A mistake made twice goes into `CLAUDE.md` ("Common mistakes") or, if it is a repeatable rule, into a skill.

Skills are advisory: Claude is likely to apply them but not forced to. Mechanical rules should also get a script or, if blocking is wanted, a hook.

## Trigger test log
Not yet recorded. Test each policy skill with three phrasings in a fresh session (for example "add a delete-chapter endpoint", "change the signup route", "add a field to the login response" for `api-contract`) and list the result here.

| Skill | Phrasing | Loaded? | Date |
|---|---|---|---|
