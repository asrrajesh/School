"""Self-test for the guard hooks. Run: python .claude/hooks/test_guards.py (exit 1 on failure)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import guard_bash as g  # noqa: E402
import guard_edit as e  # noqa: E402

CHANGE = "develop-001-ui-not-launching"
BASH_CASES = [
    ("git commit -m x", "develop", True),
    ("git commit -m x", "main", True),
    ("git commit -m x", CHANGE, False),
    ("git push origin develop-001-x", CHANGE, False),
    ("git push", "main", True),
    ("git push", "develop", True),
    ("git push --force origin x", "docs/a", True),
    ("git push -f", "docs/a", True),
    ("git push --force-with-lease", "docs/a", True),
    ("git push origin +x", "docs/a", True),
    ("git push origin HEAD:main", "docs/a", True),
    ("git push origin docs/a", "docs/a", False),
    ("git merge x", "main", True),
    ("git merge x", "develop", False),
    ("git tag v1.0", "docs/a", True),
    ("git tag -l", "docs/a", False),
    ("git tag", "docs/a", False),
    ("gcloud run deploy x", "docs/a", True),
    ("gh workflow run deploy.yml", "docs/a", True),
    ("gh release create v1", "docs/a", True),
    ("gh pr create --base develop", "docs/a", False),
    ("cd x && git commit -m y", "main", True),
    ("echo 'git commit'", "main", False),
    ("git commit -q -F - <<'EOF'\nmsg git push\nEOF", "docs/a", False),
    ("git -C . commit -m x", "develop", True),
    ("FOO=1 git push", "develop", True),
    ("git status", "main", False),
]
EDIT_CASES = [
    ("edukoreaiapi/main.py", "develop", "ask"),
    ("edukoreaiui/main.py", "main", "ask"),
    ("edukoreaiui/main.py", "docs/a", None),
    ("edukoreaiui/.env", "develop", None),
    ("README.md", "develop", None),
    ("edukoreaiui/uivenv/x.py", "develop", None),
    ("edukoreaiui/main.py", "develop-009-nope", "deny"),
]

failures = 0
for command, branch, blocked in BASH_CASES:
    reason = g.decide(command, branch)
    ok = (reason is not None) == blocked
    failures += not ok
    print("ok  " if ok else "FAIL", f"bash [{branch}] {command.splitlines()[0][:40]!r} -> {reason}")
for path, branch, expected in EDIT_CASES:
    result = e.verdict(str(e.ROOT / path), branch)
    got = result[0] if result else None
    ok = got == expected
    failures += not ok
    print("ok  " if ok else "FAIL", f"edit [{branch}] {path} -> {got}")
print("failures:", failures)
sys.exit(1 if failures else 0)
