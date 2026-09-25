---
name: review
description: Perform a rigorous self-audit on recent diffs for security, null safety, memory leaks, and concurrency deadlocks.
---

# /review — Quality & Security Audit Phase

When invoked, the agent MUST:
1. Audit the git diff for unhandled exceptions, resource leaks, and concurrency deadlocks.
2. Verify input validation and boundaries.
3. Provide a line-by-line summary of changes with explicit verification status.
