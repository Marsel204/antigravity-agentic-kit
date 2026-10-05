---
name: plan
description: Deconstruct approved specifications into ordered milestones with explicit acceptance criteria, rollback plans, and native Antigravity UI approval artifacts.
---

# /plan — Implementation Planning Phase

When invoked, the agent MUST:
1. **Milestone Decomposition:** Break down the task into discrete, independent milestones (1–3 files per milestone).
2. **Acceptance Criteria & Rollback:** Define clear pass/fail verification criteria and a rollback procedure for each milestone.
3. **Native Antigravity Artifact:** Write the plan as a markdown artifact in `<appDataDir>/brain/<conversation-id>/` using `write_to_file` with `ArtifactMetadata: { RequestFeedback: true, UserFacing: true, Summary: "..." }`. This renders the interactive **"Proceed"** button in the Antigravity UI.
4. **Execution Gate:**
   - **Interactive Mode:** Stop and wait for user approval or the Proceed button before modifying production code.
   - **Autonomous Mode (/goal, Subagents):** Emit the plan artifact and proceed automatically to the implementation milestones without deadlocking.
