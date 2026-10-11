# Everyday usage

Complete [installation](INSTALLATION.md) and [owner enrollment](ENROLLMENT.md) first. The [README](../README.md#4-implement-a-feature) gives the full proposal/freeze/implement/verify/ship walkthrough.

## Before work and after compaction

```sh
aek context --task add-search --limit 12000
```

Load relevant architecture, approved harness reference and task state at task start/resume, compaction, and worktree changes. Automatic adapters help when active; manually run this if the lifecycle surface is unavailable. Context is bounded; references do not replace inspecting current source.

## Task state

Create a local JSON payload outside protected harness paths:

```json
{
  "objective": "Add search within approved boundaries",
  "status": "implementation",
  "references": [".aek/decisions/search.md"],
  "next": "Handle empty results and verify"
}
```

Then:

```sh
aek task put add-search --input /path/to/task.json --revision 0
aek task show add-search
aek context --task add-search
```

The initial revision is zero; the first write returns revision one. Use the returned current revision on subsequent writes. A stale revision fails instead of overwriting another update. Do not provide reserved `revision`, `worktree`, or `task` fields yourself. State is local per worktree/task; approved shared decisions belong in version control.

## Protecting a harness

Author in `aek harness workspace`, stage exact protected files, and use `ALLOW_TEST_EDITS=1` only for the intentional commit. Run `propose` with actual check names and repeat `--expect-failure` as necessary. The pre-feature run distinguishes expected failures from setup errors; missing Rust functions/methods/fields are flagged for human inspection.

For the initial reviewed baseline, retain the workspace's baseline record and omit `--expect-failure` if existing tests pass. Publish its test-only draft PR and have an allowlisted human APPROVE the exact generated marker. Freeze in the proposal workspace onto a separate feature branch; do not merge the proposal into the default branch first.

Keep that proposal open and unchanged until feature merge. Target-branch protected changes require reconciliation and reapproval. If approval is dismissed, its marker edited, or its protected commit changed, verification cannot reuse the old approval. Review/proposal events invalidate dependent checks asynchronously. Request fresh implementation verification after approval changes.

## Verification and review

```sh
aek verify
aek --json verify
aek verify --offline
```

The last command needs a cached frozen snapshot and explicitly lacks live authority. Verification runs committed source; commit implementation changes before evaluating the final result. Protected staged/untracked/working changes are still detected. Tests run in a disposable checkout, preserving original working files.

Record self-review of the clean committed implementation:

```sh
aek review --summary 'Self-review: behavior, diff, boundaries, failures, and limitations checked.'
```

Only when independent work was explicitly requested and actually performed, record its assessment:

```sh
aek review --independent --requested --summary 'Reviewer assessed commit ...; findings ...'
```

These flags do not launch a reviewer or prove independence. The report must accurately disclose who performed the review. A new commit invalidates the old review.

```sh
aek ship --title 'feat: add search'
```

Shipping verifies credentials/protection/live approval, reruns checks, and pushes exactly the verified commit into a draft PR. `--review-summary` records a self-review for that commit if supplied; it is not human harness approval. No automatic merge or deployment occurs.

## Requested parallel work

Only after a human explicitly asks for parallel agents:

```sh
aek coordinate --task search-worker --branch codex/search-worker --owns 'src/search/**' --requested
```

Declare repeated `--owns` arguments for exact files or directories ending in `/**`. Overlapping ownership is rejected. This creates a worktree and ownership state, not an agent. Assign interface ownership and resolve shared decisions before implementation; load context after switching worktrees.

## Optional graph

```sh
aek graph install
# Approve graphify.enabled=true in the project policy before proceeding.
aek graph refresh
aek graph query 'callers of search' --budget 2000
```

Refresh after changes. Provenance includes repository, worktree, commit, working content, dependency version, and graph digest. Stale/modified indexes fail instead of becoming verification evidence. Inspect cited source. External semantic extraction requires separately approved policy, backend configuration and `--semantic`; local code parsing remains the default.

## Automation reports

Global options go before the subcommand:

```sh
aek --json --path /absolute/project verify
```

Both output formats currently carry the same structured evidence; pretty JSON is the readable default. Exit zero means command success, not necessarily full project enforcement unless the reported status confirms it. Nonzero includes incomplete enrollment/doctor results. Never treat editable report files as approval.
