---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
metadata:
  source-repository: https://github.com/mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  source-path: skills/engineering/implement
---

Implement the behavior described by the user's spec, tickets, or sufficiently clear request. Reuse existing decisions and inspect the relevant code and repository instructions. When a ticket is supplied, fetch it from the configured tracker and state its title; resolve ambiguity only when necessary.

If `.aek/project.json` exists, load `aek-workflow` before edits. Use its frozen-harness and exact approval requirements instead of writing protected tests in the implementation tree. For unenrolled projects, use `tdd` where behavior warrants tests; honor already agreed testing boundaries and keep small implementation cycles.

Load skills through the agent's native skill mechanism. If no Skill tool exists, read the named skill's `SKILL.md` and relevant resources directly. Skill loading does not grant new authorization.

Run relevant type checks and focused tests during implementation, then the declared final suite. Load `code-review` to review the complete change, including staged, unstaged, and untracked work. Fix findings and rerun checks affected by fixes.

Commit when the task authorizes commits or PR delivery. Publishing follows the repository's policy; enrolled repositories use `aek-verify` and `aek-ship`. Merging, deployment, and delegation need their own authorization.
