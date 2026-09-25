---
name: build
description: Execute minimal, laser-focused implementation strictly scoped to make failing tests turn green with zero regressions.
---

# /build — Implementation Phase

When invoked, the agent MUST:
1. Write the minimal code required to turn all failing tests green.
2. Avoid refactoring untouched code or adding gratuitous stylistic modifications.
3. Run the test suite to confirm green pass status with zero regressions.
