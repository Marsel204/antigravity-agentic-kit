---
name: verify
description: Full test suite verification, regression check, and release gating (alias for /ship phase).
---

# /verify — Full Suite Verification & Release Gate

When invoked, the agent MUST:
1. **Full Test Suite Run:** Execute the complete test runner (`pytest`, `npm test`, `cargo test`, etc.) across all project modules.
2. **Zero Regressions Check:** Verify all existing and new tests pass cleanly with zero regression.
3. **Artifact / Metrics:** For algorithmic or performance-critical tasks, record latency, memory, or throughput benchmarks.
4. **Transition to Ship:** If committing or opening a PR, proceed to the `/ship` or `/pr` skill checklist.
