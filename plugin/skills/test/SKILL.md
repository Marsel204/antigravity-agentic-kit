---
name: test
description: Scaffold failing unit/integration tests (TDD) that prove a bug or define a new feature before touching implementation.
---

# /test — Test-Driven Development (TDD) Scaffold

When invoked, the agent MUST:
1. Write unit or integration tests in `tests/` defining the new requirement or reproducing the bug.
2. Run the test runner (`pytest`, `npm test`, `cargo test`, etc.).
3. Confirm that the test FAILS with the expected assertion error (proving test validity).
4. Do NOT modify implementation files until the failing test is verified.
