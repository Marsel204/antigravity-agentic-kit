---
name: test
description: Scaffold failing unit/integration tests (TDD) that prove a bug or define a new feature before touching implementation.
---

# /test — Test-Driven Development (TDD) Scaffold

When invoked, the agent MUST:
1. **Author Failing Test:** Write unit or integration tests in `tests/` (or standard project test location) defining the new requirement or reproducing the bug.
2. **Execute Test Runner:** Run the project's test runner (`pytest`, `npm test`, `cargo test`, `go test`, etc.).
   * *Greenfield / Scratchpad Fallback:* If no test framework or configuration exists (e.g., in a scratch directory or single-file script), write a self-contained assertion test script (e.g., `python -m unittest test_*.py` or `node --test test_*.js`) and run it directly.
3. **Verify Expected Failure:** Confirm that the test FAILS with the expected assertion error (proving test validity, not an environmental or syntax error).
4. **Implementation Gate:** Do NOT modify implementation files until the failing test is verified.
