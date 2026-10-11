---
name: test
description: Propose requirement-focused failing tests in a separate workspace and prepare their exact harness for human approval before implementation.
---

# Test proposal

For an AEK-enrolled project, keep its frozen harness untouched. Run `aek harness workspace --task TASK --branch codex/test-TASK` to create a dedicated test-authoring clone using the kit's repository-specific runner and protected-path configuration. Author tests, fixtures, or helpers there; do not implement the feature in the proposal.

Run proposed tests against pre-feature code. Explain the expected requirement failure and distinguish it from missing dependencies, invalid collection, or runner errors. Inspect removed assertions, skips, mocks, and fixture changes for lost coverage.

Commit intentional protected changes with `ALLOW_TEST_EDITS=1`, which is only a local commit exception. Run `aek harness propose --expect-failure CHECK_NAME --branch codex/test-TASK --publish` after authorization to publish. An initial unchanged baseline may be proposed without an expected failure.

Present the concrete test diff, failure evidence, audit, and exact approval marker in the draft proposal PR. The configured human must include that marker in an APPROVE review. Never submit approval as the human, edit an approval cache to bypass checks, or use the commit exception as approval.

After the human review, run `aek harness freeze --proposal NUMBER --feature-branch codex/TASK`. Changes to the frozen harness require another proposal and approval. Keep the proposal PR open until the implementation is merged.

For unenrolled projects, use their existing test workflow and clearly distinguish test scaffolding from enforced harness protection.

## Retained workflow for unenrolled projects

The following workflow applies only to projects without `.aek/project.json`. It preserves the existing kit behavior; its autonomous-mode shortcuts never grant approval in enrolled projects. Antigravity native artifacts apply when that surface is available; otherwise save a reviewable local plan/report and use the current agent interface.

# /test — Test-Driven Development (TDD) Scaffold

When invoked, the agent MUST:
1. **Author Failing Test:** Write unit or integration tests in `tests/` (or standard project test location) defining the new requirement or reproducing the bug.
2. **Execute Test Runner:** Run the project's test runner (`pytest`, `npm test`, `cargo test`, `go test`, etc.).
   * *Greenfield / Scratchpad Fallback:* If no test framework or configuration exists (e.g., in a scratch directory or single-file script), write a self-contained assertion test script (e.g., `python -m unittest test_*.py` or `node --test test_*.js`) and run it directly.
3. **Verify Expected Failure:** Confirm that the test FAILS with the expected assertion error (proving test validity, not an environmental or syntax error).
4. **Implementation Gate:** Do NOT modify implementation files until the failing test is verified.
