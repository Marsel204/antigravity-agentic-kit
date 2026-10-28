---
name: ship
description: Publish an exactly verified and reviewed feature through its restricted agent identity and open a draft PR without merging or deploying.
---

# Ship

On AEK-enrolled projects, use `aek doctor --online` to check publishing identity and repository protection. Human approval credentials and the verification App's credentials must remain outside the coding agent's environment.

Require a clean committed feature branch, a recorded review for that commit, and independently verified harness approval. Run `aek ship --title "..."`; it reruns local checks rather than accepting an editable report file as authority.

The draft implementation PR references its test proposal and includes the exact commit, harness digest, runner results, and disclosed review mode. It remains unverified remotely until the dedicated App's required CI check passes against the current integration result. New code invalidates old reports.

Return the PR link and current verification limitations. Do not merge, deploy, or promote the PR out of draft without a user request.

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
