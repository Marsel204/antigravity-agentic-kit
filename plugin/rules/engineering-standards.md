# Engineering rules

In AEK-enrolled projects, load architecture/task context at start, resume, compaction, and worktree changes. Preserve the exact approved harness and architecture boundaries. Propose changes in a separate workspace and obtain human approval; local exception flags and editable state files provide no approval authority.

Verify the committed implementation with configured required checks. Missing, skipped, timed-out, or stale checks are not success. Inspect source references before trusting graph relationships, and refresh stale indexes.

Launch parallel agents only when requested. Keep task state separate by worktree and resolve shared interface ownership explicitly.

Publishing uses the restricted agent identity and creates a draft PR. Independent CI controls the merge gate. Merging and deployment require a separate request.

For unenrolled projects, respect existing instructions and do not claim AEK protection. Keep logs and retrieved context focused on the current task.
