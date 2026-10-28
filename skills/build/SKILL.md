---
name: build
description: Implement an approved feature against its frozen test harness and architecture boundaries, then verify the exact implementation.
---

# Implementation

Load `aek context` in enrolled projects at task start, resume, compaction, or a worktree switch. Read the approved plan, relevant source, architecture invariants, and test proposal. Revalidate approval before claiming verification.

Implement the scoped behavior without editing the frozen tests, fixtures, helpers, runner, or trusted policy. If a test is wrong, present a replacement proposal for human approval. If the design needs an architecture boundary change, present its concrete impact and wait for human approval before implementing against revised rules.

Use `aek graph query` only when Graphify is enabled and its worktree index is fresh; inspect cited source. Retrieve relevant detail rather than dumping the entire graph or repository into context.

Run configured checks with `aek verify`. Offline verification is a local diagnostic using cached references; it cannot satisfy independent CI approval. Never repair failing checks by skipping them or weakening their runner.

Keep parallel work sequential unless explicitly requested. When requested, use separate worktrees and declare ownership of shared interfaces before workers start.

## Unenrolled projects

Implement the agreed scope against existing or new tests using the project's conventions. Keep diffs minimal and avoid unrelated refactors. Run the project's checks and report their results; do not claim AEK harness protection.
