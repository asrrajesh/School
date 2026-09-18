---
name: update-spec
description: Reviews code changes and updates knowledge/SPEC.md to reflect the current state of the project. Use after completing a feature, or periodically to catch any drift.
---

# Update SPEC.md

1. Run `git log` to check how long it's been since SPEC.md was last modified, and run `git diff`/`git log -p` since that point to see what's changed in the code.
2. Read the current knowledge/SPEC.md.
3. If the changes are small/recent (a normal "just finished a feature" update):
   - Update only the sections affected by those changes.
4. If it's been a while (multiple unrelated commits, or I say "full review"):
   - Do a fuller comparison: check each section of SPEC.md against the actual current code in edukoreaiapi/ and edukoreaiui/, not just recent diffs.
   - List anything outdated or missing before editing.
5. Do not touch Overview or Out of scope unless I explicitly ask — those reflect intent, not implementation.
6. Show me a summary of what changed (or would change) before finalizing. For a full review, show me the list first and wait for my go-ahead before editing.