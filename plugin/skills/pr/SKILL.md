---
name: pr
description: Create, update, or inspect GitHub Pull Requests (PRs). Automates branch verification, pushing to remote, drafting structured PR descriptions, and submitting via GitHub CLI (gh pr create) or GitHub MCP.
---

# /pr — GitHub Pull Request Automation

Use this skill to automate opening production-ready GitHub Pull Requests.

## Execution Steps

1. **Branch Verification:** Check current branch (`git branch --show-current`).
   * If on `main` or `master`, create and switch to a descriptive branch:
     `git checkout -b <type>/<short-description>` (e.g., `feat/emergency-vehicle-preemption`, `fix/serial-timeout`).
2. **Commit Uncommitted Work:** If uncommitted changes exist, stage and commit them using Conventional Commits (`feat: ...`, `fix: ...`, `refactor: ...`).
3. **Push to Remote:** Push the branch to origin:
   `git push -u origin <branch>`
4. **Author Structured PR Description:**
   * **Title:** Concise `<type>(<scope>): <summary>` (e.g., `feat(atsc): add emergency vehicle preemption detection`).
   * **Body Format:**
     ```markdown
     ## Summary
     Brief 2-3 sentence overview of why this change is needed and what it accomplishes.

     ## Changes
     - Detailed list of modified modules and new capabilities.

     ## Verification & Testing
     - Test runner executed (`pytest`, `npm test`, etc.) with output status.
     - Confirmation of zero regressions.

     ## Checklist
     - [x] Unit/Integration tests passing
     - [x] Non-blocking I/O & safety constraints verified
     - [x] Documentation & types updated
     ```
5. **Submit via GitHub CLI:**
   Execute `gh pr create --title "<title>" --body "<body>"` (or use GitHub MCP).
6. **Return URL:** Display the clickable PR link: `[PR #X](https://github.com/...)`.
