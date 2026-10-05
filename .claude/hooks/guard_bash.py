"""PreToolUse hook for Bash: protect main/develop and block release/deploy commands.

Reads the hook JSON on stdin. Blocks (permissionDecision "deny"):
  - git commit / git push while on main or develop, or pushing to main/develop explicitly
  - any force push
  - git merge while on main
  - creating git tags (releases are tagged manually by the repo owner)
  - gcloud ... deploy, gh workflow run, gh release create
Standard library only.
"""
import json
import re
import shlex
import subprocess
import sys

PROTECTED = {"main", "develop"}
SEPARATORS = {"&&", "||", ";", "|", "&", "(", ")"}


def current_branch(cwd: str | None) -> str:
    for directory in (cwd, None):
        try:
            out = subprocess.run(["git", "branch", "--show-current"], cwd=directory, capture_output=True, text=True)
            return out.stdout.strip()
        except OSError:
            continue
    return ""


def segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    segs, cur = [], []
    for token in lexer:
        if token in SEPARATORS:
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(token)
    if cur:
        segs.append(cur)
    return segs


def git_args(tokens: list[str]) -> tuple[str, list[str]]:
    """Return (subcommand, remaining args) for a `git ...` token list, skipping global options."""
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        i += 2 if tokens[i] in ("-C", "-c", "--git-dir", "--work-tree") else 1
    return (tokens[i], tokens[i + 1:]) if i < len(tokens) else ("", [])


def decide(command: str, branch: str) -> str | None:
    """Return a reason to block the command, or None to allow it."""
    try:
        segs = segments(command)
    except ValueError:
        segs = []
        if re.search(r"\bgit\s+(commit|push)\b", command) and branch in PROTECTED:
            return f"git commit/push is blocked on '{branch}' (could not parse the command)"
    for tokens in segs:
        while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
            tokens = tokens[1:]
        if not tokens:
            continue
        tool = tokens[0]
        if tool == "git":
            sub, args = git_args(tokens)
            if sub == "commit" and branch in PROTECTED:
                return f"Do not commit on '{branch}'. Create or switch to a develop-<id>-<desc> change branch."
            if sub == "push":
                if any(a in ("-f", "--force", "--force-with-lease") or a.startswith("--force-with-lease=") for a in args):
                    return "Force-push is not allowed."
                if any(a.startswith("+") for a in args if not a.startswith("-")):
                    return "Force-push (+refspec) is not allowed."
                if branch in PROTECTED:
                    return f"Do not push from '{branch}'. Push the change branch and open a PR into develop."
                targets = [a.split(":")[-1] for a in args if not a.startswith("-")]
                if any(t in PROTECTED for t in targets):
                    return "Pushing directly to main/develop is not allowed; open a PR instead."
            if sub == "merge" and branch == "main":
                return "Merging into main is done manually by the repo owner (release)."
            if sub == "tag":
                listing = not args or any(
                    a in ("-l", "--list", "-n", "--contains", "--merged", "--no-merged", "-v") for a in args
                )
                if not listing:
                    return "Release tags are created manually by the repo owner, not by Claude."
        elif tool == "gcloud" and "deploy" in tokens:
            return "Deployments need explicit release authorization from the repo owner."
        elif tool == "gh":
            if tokens[1:3] in (["workflow", "run"], ["release", "create"]):
                return "Triggering workflows or creating releases is done manually by the repo owner."
    return None


def main() -> int:
    payload = json.load(sys.stdin)
    command = (payload.get("tool_input") or {}).get("command", "")
    reason = decide(command, current_branch(payload.get("cwd")))
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{reason} (see CLAUDE.md, Feature workflow)",
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
