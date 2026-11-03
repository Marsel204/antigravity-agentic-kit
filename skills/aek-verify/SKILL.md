---
name: aek-verify
description: Verify committed code and record exact-commit review evidence for an AEK-enrolled project.
---

# AEK verification and review

Use for AEK-enrolled repositories. For other projects, run their own declared checks and review the actual change without claiming AEK protection.

Load `aek context` and inspect the configured required checks. Commit the intended implementation before final verification: `aek verify` evaluates committed source in a disposable checkout. Preserve unrelated working changes. Missing, skipped, timed-out, stale, or failed checks are not success. Never change protected files or weaken a runner to make a check pass.

`aek verify --offline` is diagnostic and relies on cached references; it cannot authorize shipping or independent CI. Revalidate live approval before claiming current verification.

Review the diff and relevant source against the specification, edge cases, approved harness and architecture, unsafe inputs, resource lifetimes, and concurrency. Use `code-review` for its Standards and Spec lenses when helpful; self-review is the default and must be disclosed.

Record the review for the exact clean commit with `aek review --summary 'Self-review: ...'`. Only when an independent reviewer was explicitly requested and actually assessed that commit may `--independent --requested` be used. A new commit requires new verification and review evidence. These flags do not launch agents or establish human harness approval.

Report concrete checks, findings, and unverified behavior. Continue to `aek-ship` only when publishing is authorized.
