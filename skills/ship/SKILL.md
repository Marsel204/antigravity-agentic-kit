---
name: ship
description: Complete the final release phase of the engineering lifecycle. Runs test suites, verifies zero regressions, commits atomic changes, pushes to GitHub, and opens a Pull Request.
---

# /ship — Release & Ship Phase

The final stage of the **Spec → Plan → Test → Build → Review → Ship** lifecycle.

## Execution Checklist

1. **Test Verification (Mandatory Gate):**
   * Run the test suite (`npm test`, `pytest`, `cargo test`, etc.).
   * If any test fails, STOP immediately. Do NOT push failing code.
2. **Working Tree Cleanliness:**
   * Run `git status` to ensure no temporary files (`.bak`, `.pyc`, debug logs, or unignored secrets) are staged.
3. **Branch & Commit:**
   * Ensure changes are committed on a feature branch with a Conventional Commit message.
4. **Push to Origin:**
   * Run `git push -u origin <branch>`.
5. **Open Pull Request:**
   * Create the PR via `gh pr create` with test logs and verification notes.
   * Provide the clickable PR link to the user.
