---
name: ship
description: Complete the final release phase of the engineering lifecycle. Runs test suites, verifies zero regressions, commits atomic changes, pushes to remote, and opens a Pull Request or exports patch.
---

# /ship — Release & Ship Phase

The final stage of the **Spec → Plan → Test → Build → Review → Ship** lifecycle.

## Execution Checklist

1. **Test Verification (Mandatory Gate):**
   * Run the test suite (`npm test`, `pytest`, `cargo test`, etc.).
   * If any test fails, STOP immediately. Do NOT ship failing code.
2. **Working Tree Cleanliness:**
   * Run `git status` to ensure no temporary files (`.bak`, `.pyc`, debug logs, or unignored secrets) are staged.
3. **Branch & Commit:**
   * If git repository is initialized: Ensure changes are committed on a feature branch with a Conventional Commit message.
4. **Push to Origin & Pull Request:**
   * Verify remote: Check `git remote -v`.
   * Check GitHub CLI: Check `gh auth status`.
   * **If remote and authenticated `gh` exist:**
     * Run `git push -u origin <branch>`.
     * Create the PR via `gh pr create` with test logs and verification notes.
     * Provide the clickable PR link: `[PR #X](...)`.
   * **Fallback (No remote / No authenticated `gh` / Local-only):**
     * Commit changes locally and emit a release summary artifact with `git diff HEAD~1` or patch instructions.
