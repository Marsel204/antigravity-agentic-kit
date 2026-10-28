---
name: verify
description: Verify the current implementation with the project's required checks before review or shipping.
---

# Verification

Verify the current implementation before review or shipping. Missing, skipped, timed-out, or stale required checks are not success. Never weaken or skip checks to obtain a green result.

## AEK-enrolled projects

For projects with `.aek/project.json`, load `aek context` and run `aek verify` against the current implementation and approved frozen harness. Preserve the exact human GitHub approval and architecture boundaries. `aek verify --offline` is for local diagnostics only; it cannot authorize shipping or satisfy independent CI.

## Unenrolled projects

Run the project's full test suite and applicable build, type, and lint checks. Report exact commands and observed results, including failures, skips, and limitations. Record benchmarks only when performance is in scope. Do not claim AEK enforcement.

Verification does not authorize committing, publishing, or merging. Hand off to `review`, then `ship` or `pr` only when requested.
