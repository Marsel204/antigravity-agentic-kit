---
name: engineering-lifecycle
description: Coordinate specification, planning, approved test proposals, implementation, verification, review, and draft-PR delivery for substantial engineering work.
---

# Engineering lifecycle

Use **Spec → Plan → Test proposal → Human approval → Frozen harness → Implementation → Verification → Review → Draft PR** for enrolled projects.

Inspect the project before proposing work. State requirements, failure modes, scope, architecture constraints, and measurable acceptance criteria. Resolve material uncertainty with the user before planning implementation.

Prepare tests in a separate proposal workspace and obtain approval of their exact snapshot through AEK's GitHub review flow. A skill or local approval flag cannot establish authority. Freeze the approved snapshot before feature implementation. Obtain a new human approval for any harness or architecture boundary change.

Load `aek context` at task start and after resume, compaction, or a worktree switch. Keep architecture decisions versioned and task state worktree-specific. Graphify is optional retrieval; check freshness and inspect its source evidence.

Run `aek verify` on the committed implementation. Review specification coverage, edge cases, architecture, security, and concurrency. Disclose self-review; use independent agents only when requested. Record the exact reviewed commit with `aek review`.

When publishing is authorized, `aek ship` pushes through the restricted agent identity and opens a draft PR. Independent CI verifies the integration result before merge. Merging, deployment, and launching parallel agents require their own user instruction.

On unenrolled projects, follow the existing project workflow and disclose the absence of AEK enforcement rather than claiming a locked harness.
