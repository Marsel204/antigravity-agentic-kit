---
name: engineering-lifecycle
description: >-
  Enforce a strict, high-discipline Software Development Life Cycle (SDLC) workflow for AI agents.
  Activate whenever planning, building non-trivial features, refactoring critical code, or fixing complex bugs.
  Guarantees that no code is modified before specifications, edge cases, and failing tests are verified.
---

# High-Discipline Engineering Lifecycle Skill

This skill enforces a structured **Spec → Plan → Test (TDD) → Build → Review → Ship** workflow across all tasks.
Agents MUST execute each phase sequentially. In interactive sessions, do NOT skip ahead to implementation without user approval of the plan and failing tests. In autonomous sessions (`/goal`, subagents), emit the plan artifact and proceed without deadlock.

---

## Phase 1: Specification (/spec)
* **Impact Surface:** Identify every module, function, and configuration file touched.
* **Edge Cases & Failure Modes:** Enumerate boundary conditions, network timeouts, invalid inputs, and resource exhaustion scenarios.
* **Architecture Contracts:** For embedded/edge runtimes, verify non-blocking I/O, deterministic latency budgets, and thread safety.
* **Exit Criteria:** A clear, written specification highlighting open design questions.

---

## Phase 2: Implementation Plan (/plan)
* **Milestone Decomposition:** Break the task into discrete, independent milestones (1–3 files per milestone).
* **Acceptance Criteria:** Define exact pass/fail criteria for each milestone.
* **Rollback Plan:** Ensure changes can be reverted cleanly without side effects.
* **Artifact Output:** Render plan as an artifact with `RequestFeedback: true` in `<appDataDir>/brain/<conversation-id>/`.
* **Exit Criteria:** User explicitly reviews and approves the plan (via Proceed button or chat). In autonomous mode (`/goal`, subagent), emit the plan artifact and proceed automatically.

---

## Phase 3: Test-Driven Scaffold (/test)
* **Test-First Mandate:** Author unit/integration tests in the appropriate test suite (e.g. tests/test_*.py or pytest) *before* touching implementation files.
* **Reproduce Failure:** Run the test suite using the project's test runner (pytest, npm test, cargo test, etc.).
* **Failing Verification:** Confirm that tests fail with the expected error or assertion failure (proving test validity).
* **Exit Criteria:** A reproducible failing test proving the requirement or bug.

---

## Phase 4: Minimal Implementation (/build)
* **Laser-Focused Edits:** Write only the minimal implementation required to make the failing tests turn green.
* **Scope Guard:** Do not refactor unrelated code, modify formatting, or add gratuitous comments to existing untouched functions.
* **Exit Criteria:** All written tests pass cleanly with zero regressions.

---

## Phase 5: Self-Audit & Security Review (/review)
* **Static Analysis:** Check for unhandled exceptions, null pointer dereferences, resource leaks (unclosed sockets/files/database handles), and concurrency race conditions.
* **Security & Input Validation:** Verify that all external inputs are bounded and sanitized.
* **Diff Audit:** Produce a clean, concise diff summary explaining the rationale of changes.

---

## Phase 6: Release & Verification (/ship or /verify)
* **Full Suite Run:** Run the entire test suite to guarantee zero regression across other components.
* **Ship Gate:** Verify clean working tree, commit via Conventional Commits, push branch, and open PR via `/ship`. If no remote or `gh` CLI is configured, export a patch or diff summary artifact.
* **Metrics/Ledger:** For edge or algorithmic systems, record execution latency, memory footprint, or ledger updates.
