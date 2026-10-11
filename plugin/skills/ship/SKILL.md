---
name: ship
description: Publish an exactly verified and reviewed feature through its restricted agent identity and open a draft PR without merging or deploying.
---

# Ship

On AEK-enrolled projects, use `aek doctor --online` to check publishing identity and repository protection. Human approval credentials and the verification App's credentials must remain outside the coding agent's environment.

Require a clean committed feature branch, a recorded review for that commit, and independently verified harness approval. Run `aek ship --title "..."`; it reruns local checks rather than accepting an editable report file as authority.

The draft implementation PR references its test proposal and includes the exact commit, harness digest, runner results, and disclosed review mode. It remains unverified remotely until the dedicated App's required CI check passes against the current integration result. New code invalidates old reports.

Return the PR link and current verification limitations. Do not merge, deploy, or promote the PR out of draft without a user request.

For unenrolled projects, follow the project's checks and publishing workflow, and disclose that AEK enforcement is absent.

## Retained workflow for unenrolled projects

The following workflow applies only to projects without `.aek/project.json`. It preserves the existing kit behavior; its autonomous-mode shortcuts never grant approval in enrolled projects. Antigravity native artifacts apply when that surface is available; otherwise save a reviewable local plan/report and use the current agent interface.

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
