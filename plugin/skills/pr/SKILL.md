---
name: pr
description: Create a reviewable pull request using the project's publishing policy and include current verification evidence.
---

# Pull request

In an AEK-enrolled project, publish through `aek ship` after an exact-commit review and independently approved harness verification. Use a separate test-proposal PR for harness authoring. Publishing uses the configured restricted agent identity and opens a draft; do not bypass its checks by calling GitHub directly with human credentials.

Return the created PR link. Do not merge or deploy unless separately requested.

## Unenrolled projects

Publish only when publishing is authorized. Follow project conventions and disclose the absence of AEK enforcement. Use `verify` for required checks and review the exact implementation before publishing; unresolved failures or missing required evidence prevent shipping.

Inspect `git status`, the full diff, and the staged diff. Stage explicit intended paths and commit only the intended changes; never automatically stage unrelated or untracked files. If on the default branch, create a descriptive feature branch before committing. Use a Conventional Commit message.

Check `git remote -v` and `gh auth status`. With a GitHub remote and authenticated `gh`, push with `git push -u origin <branch>`. Write the PR body to a temporary file and use `gh pr create --draft --title "<title>" --body-file <tmpfile>`. Draft is the default unless the user or project convention requests ready status. Never pass a multiline body through `--body`.

If there is no GitHub remote or `gh` is unavailable or unauthenticated, provide the drafted title/body and exact branch, commit, push, and PR commands for the remaining steps instead of claiming publication.

Use this PR body structure:

```markdown
## Summary
Explain the problem and resulting behavior.

## Changes
- Describe the intended changes.

## Verification
- Record exact commands and results actually observed.

## Limitations
- State unresolved constraints or missing validation, or say none observed.
```

Tick checklist boxes only for evidence actually observed. Return the PR link when created. Merging and deployment require separate user requests.
