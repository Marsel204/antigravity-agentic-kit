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

## Unenrolled projects

Follow the project's conventions without claiming AEK enforcement. Inspect requirements, affected components, edge cases, and failure modes. Define milestones, acceptance criteria, dependencies, and rollback procedures. If the user asked only for a plan, deliver it. If implementation is already authorized, explain the approach and continue without asking for the same approval again.

Use red-green TDD: reproduce the requirement with an expected failing assertion before minimal implementation, then make it pass. Keep the diff focused. Self-audit resource leaks, input validation, exception handling, and concurrency. Use `verify` for the full suite and applicable project checks, then review the result. Publish only when authorized through `ship` or `pr`.

If the host offers a native plan or review artifact (for example, Antigravity `write_to_file` with RequestFeedback), use it; otherwise present the plan in chat or save local Markdown when persistence helps.
