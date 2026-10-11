---
name: plan
description: Turn a reviewed specification into implementable milestones with acceptance checks, dependencies, and rollback behavior.
---

# Implementation plan

Inspect the specification and existing project before planning. In enrolled projects, include the test proposal/approval checkpoint, frozen harness, approved architecture boundaries, verification, and review requirements.

Define milestones around independently reviewable behavior, with concrete acceptance checks, dependency order, and rollback procedures. Identify owner-provisioned prerequisites such as separate credentials or CI protection rather than inventing approval authority.

Resolve material scope or design choices before presenting the plan. Honor an already approved plan or explicit implementation request; do not ask for the same permission again. Material architecture or harness changes still require their specified human review.

Do not assume authorization to publish, merge, deploy, or launch parallel agents merely because those actions are available in the toolkit.

## Retained workflow for unenrolled projects

The following workflow applies only to projects without `.aek/project.json`. It preserves the existing kit behavior; its autonomous-mode shortcuts never grant approval in enrolled projects. Antigravity native artifacts apply when that surface is available; otherwise save a reviewable local plan/report and use the current agent interface.

# /plan — Implementation Planning Phase

When invoked, the agent MUST:
1. **Milestone Decomposition:** Break down the task into discrete, independent milestones (1–3 files per milestone).
2. **Acceptance Criteria & Rollback:** Define clear pass/fail verification criteria and a rollback procedure for each milestone.
3. **Native Antigravity Artifact:** Write the plan as a markdown artifact in `<appDataDir>/brain/<conversation-id>/` using `write_to_file` with `ArtifactMetadata: { RequestFeedback: true, UserFacing: true, Summary: "..." }`. This renders the interactive **"Proceed"** button in the Antigravity UI.
4. **Execution Gate:**
   - **Interactive Mode:** Stop and wait for user approval or the Proceed button before modifying production code.
   - **Autonomous Mode (/goal, Subagents):** Emit the plan artifact and proceed automatically to the implementation milestones without deadlocking.
