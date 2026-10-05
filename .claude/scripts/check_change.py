"""Check that a change is at a valid point in the workflow before a stage runs.

Usage (from the repo root):
  python .claude/scripts/check_change.py <id> --stage <stage>
  python .claude/scripts/check_change.py <id> --demote-from <intent|spec>

Stages: intent-update, spec-create, spec-update, plan-create, plan-update, impl, knowledge, wrap-up.
--any-branch skips the branch rule (for wrap-up after the user already left the change branch).
Exit code 0 = OK (warnings may print), 1 = a rule is violated. Standard library only.

--demote-from sets downstream files that are `approved` back to `draft` (after the
named file was revised) and warns about downstream files that are `implemented`.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHANGES = ROOT / "changes"
ORDER = ["intent", "spec", "plan"]
STATUS_RE = re.compile(r"^(\s*-\s*\*\*Status:\*\*\s*)(\w+)", re.MULTILINE)

# stage -> (files that must exist, required status per file, file that must NOT exist)
RULES = {
    "intent-update": ({"intent": None}, None),
    "spec-create": ({"intent": {"approved"}}, "spec"),
    "spec-update": ({"intent": None, "spec": None}, None),
    "plan-create": ({"intent": None, "spec": {"approved"}}, "plan"),
    "plan-update": ({"intent": None, "spec": None, "plan": None}, None),
    "impl": ({"intent": None, "spec": {"approved", "implemented"}, "plan": {"approved", "implemented"}}, None),
    "knowledge": ({"intent": None, "spec": None, "plan": {"approved", "implemented"}}, None),
    "wrap-up": ({"intent": {"implemented"}, "spec": {"implemented"}, "plan": {"implemented"}}, None),
}


def run(*cmd: str) -> str:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout.strip()


def find_dir(change_id: str) -> Path | None:
    matches = sorted(CHANGES.glob(f"{change_id}-*")) if CHANGES.exists() else []
    return matches[0] if matches else None


def status_of(path: Path) -> str | None:
    match = STATUS_RE.search(path.read_text(encoding="utf-8"))
    return match.group(2).lower() if match else None


def check_stage(change_id: str, stage: str, any_branch: bool = False) -> int:
    errors, warnings = [], []
    folder = find_dir(change_id)
    if folder is None:
        print(f"ERROR: no folder changes/{change_id}-* (run /create-intent first)")
        return 1
    branch = run("git", "branch", "--show-current")
    if not any_branch and not branch.startswith(f"develop-{change_id}-"):
        errors.append(f"current branch is '{branch}', expected develop-{change_id}-*")

    needs, must_not_exist = RULES[stage]
    for name, allowed in needs.items():
        path = folder / f"{name}.md"
        if not path.exists():
            errors.append(f"{name}.md is missing (create it first)")
            continue
        status = status_of(path)
        if status is None:
            errors.append(f"{name}.md has no '- **Status:**' line")
        elif allowed and status not in allowed:
            errors.append(f"{name}.md status is '{status}', must be {' or '.join(sorted(allowed))}")
    if must_not_exist and (folder / f"{must_not_exist}.md").exists():
        errors.append(f"{must_not_exist}.md already exists (use the update skill instead)")

    if stage == "wrap-up" and not any_branch and not errors:
        if not run("git", "log", "--oneline", "develop..HEAD", "--grep", f"^knowledge({change_id})"):
            errors.append(f"no 'knowledge({change_id})' commit on this branch; run /update-knowledge and commit it first")

    if stage == "knowledge" and not errors:
        commits = run("git", "log", "--oneline", "develop..HEAD", "--grep", f"^impl({change_id})")
        if not commits:
            warnings.append(f"no 'impl({change_id})' commit on this branch; the code may not be implemented yet")
        for name in ORDER[:2]:
            if status_of(folder / f"{name}.md") == "draft":
                warnings.append(f"{name}.md is still draft")

    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}")
    if not errors:
        print(f"OK: change {change_id} may run stage '{stage}'")
    return 1 if errors else 0


def demote(change_id: str, source: str) -> int:
    folder = find_dir(change_id)
    if folder is None:
        print(f"ERROR: no folder changes/{change_id}-*")
        return 1
    for name in ORDER[ORDER.index(source) + 1:]:
        path = folder / f"{name}.md"
        if not path.exists():
            continue
        status = status_of(path)
        if status == "approved":
            text = STATUS_RE.sub(lambda m: m.group(1) + "draft", path.read_text(encoding="utf-8"), count=1)
            path.write_text(text, encoding="utf-8")
            print(f"{name}.md: approved -> draft (revise it to match the updated {source}, then re-approve)")
        elif status == "implemented":
            print(f"WARNING: {name}.md is implemented; the updated {source} may no longer match the built code")
        else:
            print(f"{name}.md: status '{status}' left unchanged")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("id", help="change id, e.g. 001")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stage", choices=sorted(RULES))
    group.add_argument("--demote-from", choices=ORDER[:2])
    parser.add_argument("--any-branch", action="store_true", help="skip the branch rule")
    args = parser.parse_args()
    change_id = args.id.zfill(3)
    return check_stage(change_id, args.stage, args.any_branch) if args.stage else demote(change_id, args.demote_from)


if __name__ == "__main__":
    sys.exit(main())
