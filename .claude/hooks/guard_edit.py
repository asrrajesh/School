"""PreToolUse hook for Edit|Write: edits to app code need an approved plan.

For files under edukoreaiapi/ or edukoreaiui/ (excluding venvs, .github and .env files):
  - on a develop-<id>-* branch: run check_change.py <id> --stage impl; deny if it fails
  - on main or develop: ask for confirmation (code changes belong on a change branch)
  - on any other branch (docs/*, hotfix branches): allow
Standard library only.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIRS = ("edukoreaiapi", "edukoreaiui")
SKIP_PARTS = {"apivenv", "uivenv", "__pycache__", ".github"}


def is_app_code(file_path: str) -> bool:
    try:
        rel = Path(os.path.relpath(os.path.abspath(file_path), ROOT))
    except ValueError:
        return False
    parts = rel.parts
    if not parts or parts[0] not in APP_DIRS or SKIP_PARTS & set(parts):
        return False
    return not rel.name.startswith(".env")


def verdict(file_path: str, branch: str) -> tuple[str, str] | None:
    """Return (decision, reason) or None to allow."""
    if not is_app_code(file_path):
        return None
    if branch in ("main", "develop"):
        return "ask", f"Editing app code on '{branch}'. Code changes belong on a develop-<id>-<desc> branch."
    match = re.match(r"develop-(\d{3})-", branch)
    if not match:
        return None
    result = subprocess.run(
        [sys.executable, str(ROOT / ".claude" / "scripts" / "check_change.py"), match.group(1), "--stage", "impl"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return "deny", "Workflow check failed: " + " ".join(result.stdout.split()).strip()
    return None


def main() -> int:
    payload = json.load(sys.stdin)
    file_path = (payload.get("tool_input") or {}).get("file_path", "")
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    result = verdict(file_path, branch) if file_path else None
    if result:
        decision, reason = result
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
