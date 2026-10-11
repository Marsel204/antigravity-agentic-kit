---
name: pr
description: Create a reviewable pull request using the project's publishing policy and include current verification evidence.
---

# Pull request

In an AEK-enrolled project, publish through `aek ship` after an exact-commit review and independently approved harness verification. Use a separate test-proposal PR for harness authoring. Publishing uses the configured restricted agent identity and opens a draft; do not bypass its checks by calling GitHub directly with human credentials.

In unenrolled projects, follow their existing checks and publishing conventions. Inspect the final diff, include relevant validation and limitations, and create a PR only when publishing is authorized. Keep multiline bodies in a temporary file and pass `--body-file` to `gh`.

Return the created PR link. Do not merge or deploy unless separately requested.

## Retained workflow for unenrolled projects

The following workflow applies only to projects without `.aek/project.json`. It preserves the existing kit behavior; its autonomous-mode shortcuts never grant approval in enrolled projects. Antigravity native artifacts apply when that surface is available; otherwise save a reviewable local plan/report and use the current agent interface.

# /pr — GitHub Pull Request Automation

Use this skill to automate opening production-ready GitHub Pull Requests.

## Execution Steps

1. **Branch Verification:** Check current branch (`git branch --show-current`).
   * If on `main` or `master`, create and switch to a descriptive branch:
     `git checkout -b <type>/<short-description>` (e.g., `feat/emergency-vehicle-preemption`, `fix/serial-timeout`).
2. **Commit Uncommitted Work:** If uncommitted changes exist, stage and commit them using Conventional Commits (`feat: ...`, `fix: ...`, `refactor: ...`).
3. **Push to Remote:**
   * Verify remote exists (`git remote -v`). If origin exists, push: `git push -u origin <branch>`.
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
5. **Submit via GitHub CLI or Fallback:**
   * **If `gh` CLI is available and authenticated (`gh auth status` passes):**
     Execute `gh pr create --title "<title>" --body "<body>"` (or use GitHub MCP).
     Display the clickable PR link: `[PR #X](https://github.com/...)`.
   * **Fallback (No remote / unauthenticated `gh`):**
     Write the drafted PR title and body to an artifact markdown file in `<appDataDir>/brain/<conversation-id>/` with instructions for manual PR submission.
