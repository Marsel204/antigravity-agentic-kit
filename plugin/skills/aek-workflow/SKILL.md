---
name: aek-workflow
description: Coordinate implementation within an AEK-enrolled repository, preserving approved harnesses, architecture, and publishing controls.
---

# AEK enrolled-project workflow

Use this only for repositories with `.aek/project.json`. Unenrolled projects use their existing workflow and the individual engineering skills; installing this kit does not require enrollment.

Load `aek context` at task start, resume, compaction, and worktree switches. Inspect the current policy, relevant architecture, task state, and existing approved harness before planning. Reuse requirements and authorization already provided; scale specification and planning to the change.

If tests, fixtures, helpers, runners, policy, or architecture need protected changes, use `aek-harness` to prepare a concrete proposal in a dedicated `aek harness workspace`. Dependent implementation waits for the exact human GitHub approval and frozen snapshot. A task request, local flag, editable report, or skill cannot grant that approval.

Implement only within the approved harness and architecture. If a test is wrong or a boundary must change, prepare a new proposal rather than weakening checks or editing the frozen snapshot. Optional Graphify queries require an approved opt-in and fresh provenance; inspect cited source.

Use `aek-verify` for committed-source checks and exact-commit review recording. Disclose self-review. Independent review and parallel agents require the user's explicit request; flags never prove that a reviewer actually ran.

For authorized draft-PR delivery, use `aek-ship` with the restricted publishing identity. Required independent CI remains the merge gate. Merging and deployment require separate requests.
