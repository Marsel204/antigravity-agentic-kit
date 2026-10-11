---
name: review
description: Review a committed implementation against its specification, approved harness, and architecture; disclose whether review is independent or self-review.
---

# Review

Inspect the actual diff and relevant source for requirement coverage, edge cases, unsafe inputs, resource leaks, and concurrency failures. Check that tests exercise meaningful behavior and architecture boundaries remain approved. Do not change frozen harness files to make the review pass.

For enrolled projects, require current verification and record a concise evidence-based summary with `aek review --summary "..."`. Reports bind to the exact commit; edits require a new review.

Disclose self-review by default. If independent review is explicitly requested, use a separate reviewer with the specification and raw diff/source. Do not coach it toward a preferred answer. Use `--independent --requested` only after that review actually occurs; the flag does not launch a reviewer or prove independence.

List actionable findings and material unverified behavior. Never label missing or skipped required checks as success.
