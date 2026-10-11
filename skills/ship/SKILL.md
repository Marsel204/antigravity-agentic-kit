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
