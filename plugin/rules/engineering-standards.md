# Global Engineering & Quality Standards

## 1. Test-Driven Development (TDD) Mandate
- Before modifying core business logic, algorithms, or fixing reported bugs, check for or create corresponding test cases in `tests/`.
- Ensure tests fail initially when testing a bug fix or new requirement before writing implementation code.
- Always run the project's test runner (`pytest`, `npm test`, `cargo test`, etc.) to confirm tests pass with zero regressions.

## 2. Context Window & Token Efficiency
- Do not execute commands that dump unbounded stdout into the context window (e.g., raw `cat` on large datasets, `git log` without `-n`, or unfocused test logs).
- Use focused queries, specific grep patterns, or piped heads/tails to inspect logs.

## 3. High-Discipline Action Protocol
- Eliminate conversational pleasantries, filler phrases, and restating the prompt.
- Structure updates into numbered milestones, concrete diffs, and explicit verification statuses.
