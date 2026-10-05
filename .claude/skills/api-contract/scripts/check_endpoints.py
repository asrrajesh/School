"""Check that every API router endpoint has a matching call in the UI's api_client.py.

Usage (from anywhere): python .claude/skills/api-contract/scripts/check_endpoints.py
Exit code 0 = in sync, 1 = mismatch. Standard library only.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ROUTERS = ROOT / "edukoreaiapi" / "routers"
CLIENT = ROOT / "edukoreaiui" / "services" / "api_client.py"

# Endpoints that exist in the API but have no client function today (see knowledge/api-specification.md).
# Remove an entry when the client gains the call.
API_ONLY = {"POST /api/auth/google-login"}

METHODS = "get|post|put|delete|patch"


def norm(path: str) -> str:
    return re.sub(r"\{[^}]*\}", "{}", path)


def api_endpoints() -> set[str]:
    found = set()
    for file in sorted(ROUTERS.glob("*.py")):
        text = file.read_text(encoding="utf-8")
        prefix = re.search(r'APIRouter\([^)]*prefix\s*=\s*"([^"]*)"', text)
        prefix = prefix.group(1) if prefix else ""
        for method, path in re.findall(rf'@router\.({METHODS})\(\s*"([^"]*)"', text):
            found.add(f"{method.upper()} {norm(prefix + path)}")
    return found


def client_calls() -> set[str]:
    text = CLIENT.read_text(encoding="utf-8")
    pattern = rf'httpx\.({METHODS})\(\s*f?"\{{API_BASE_URL\}}(/api/[^"?]*)"'
    return {f"{m.upper()} {norm(p)}" for m, p in re.findall(pattern, text)}


def main() -> int:
    api, client = api_endpoints(), client_calls()
    missing = sorted(api - client - API_ONLY)
    orphan = sorted(client - api)
    stale = sorted(API_ONLY & client)
    for label, items in (
        ("API endpoints with no call in api_client.py", missing),
        ("api_client.py calls with no matching router endpoint", orphan),
        ("API_ONLY allowlist entries that now have a client call (remove them)", stale),
    ):
        if items:
            print(f"{label}:")
            for item in items:
                print(f"  {item}")
    if missing or orphan or stale:
        return 1
    print(f"OK: {len(api)} API endpoints, {len(client)} client calls, {len(API_ONLY)} allowlisted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
