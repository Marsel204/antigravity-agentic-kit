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

## Unenrolled projects

Write a requirement-focused unit or integration test in the project's standard location before changing implementation. Run the project's test runner and confirm the failure is the expected assertion, not an import, syntax, collection, or environment error. Only then implement the minimal change and run the tests again to establish red-green evidence.

For a greenfield project without a test framework, use a self-contained test with `python -m unittest` or `node --test`. Follow the project's existing conventions and do not claim frozen-harness protection.
