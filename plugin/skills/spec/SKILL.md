---
name: spec
description: Clarify requirements, impacted modules, edge cases, and hardware/API constraints before planning or coding.
---

# /spec — Specification & Requirements Phase

When invoked, the agent MUST:
1. Inspect existing code to identify the exact files and modules that will be affected.
2. Enumerate edge cases, failure states, network/serial timeouts, and boundary conditions.
3. For edge/embedded systems, verify non-blocking I/O and resource/memory constraints.
4. Stop and present the specification with any open questions for user review before proceeding.
