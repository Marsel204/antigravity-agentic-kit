---
name: plan
description: Turn a reviewed specification into implementable milestones with acceptance checks, dependencies, and rollback behavior.
---

# Implementation plan

Inspect the specification and existing project before planning. Reuse accepted requirements and the initial setup/baseline from `init` rather than repeating initialization. In enrolled projects, include the test proposal/approval checkpoint, frozen harness, approved architecture boundaries, verification, and review requirements.

Define milestones around independently reviewable behavior, with concrete acceptance checks, dependency order, and rollback procedures. Identify owner-provisioned prerequisites such as separate credentials or CI protection rather than inventing approval authority.

Resolve material scope or design choices before presenting the plan. Honor an already approved plan or explicit implementation request; do not ask for the same permission again. Material architecture or harness changes still require their exact human GitHub approval in enrolled projects. A plan or local approval flag does not grant harness authority. Continue independent planning and preparation while required approval is pending; dependent implementation waits for the approved frozen snapshot.

Do not assume authorization to publish, merge, deploy, or launch parallel agents merely because those actions are available in the toolkit.

## Unenrolled projects

Define reviewable milestones with acceptance criteria, dependency order, and rollback procedures using the project's conventions. Include red-green TDD, minimal implementation diffs, self-audit of resource leaks, input validation and concurrency, and a full-suite run through `verify`.

If the user asked only for a plan, deliver it. If implementation is already authorized, explain the approach and continue without asking for the same approval again. Resolve material missing decisions while continuing independent work. Do not infer additional authorization from slash commands or claim AEK protection.

If the host offers a native plan or review artifact (for example, Antigravity `write_to_file` with RequestFeedback), use it; otherwise present the plan in chat or save local Markdown when persistence helps.
