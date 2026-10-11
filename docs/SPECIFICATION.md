# Agentic Engineering Kit specification

One shared, Python 3.11+ core supports Codex and Antigravity, with Linux/macOS/native-Windows launchers. Tools and skills install globally; Git protection requires explicit repository enrollment. Existing settings/hooks are preserved, colliding files require explicit replacement and backup, and plugin skills are generated from canonical `skills/` sources.

The lifecycle is **Spec → Plan → Test proposal → Human approval → Frozen harness → Implementation → Verification → Review → Draft PR**. Each protected change requires human approval of its exact snapshot, including fixtures, helpers, runner configuration, and architecture documents. Test authoring happens in a dedicated clone; implementation clones/worktrees remain locked. An intentional `ALLOW_TEST_EDITS=1` commit is not approval.

Approval is a GitHub APPROVE review by an allowlisted numeric human ID. Its body identifies the exact commit, baseline, and digest. Proposal PRs remain open until feature merge. Bot reviews, dismissed reviews, stale snapshots, changed target harnesses, implementation changes in test proposals, security identity changes, and narrowing protected patterns are rejected. Commands/rules may change only in a new exactly approved proposal.

Local verification preserves user working files and executes committed source with restored approved harness content in a disposable clone. Preexisting tampering is failure even if restored tests pass. Recheck integrity after execution. Offline cache use is disclosed and never authorizes shipping or CI.

CI authority is independent: trusted default-branch controller, exact human review revalidation, synthetic integration commit, credential-free Docker checks, and a separate GitHub App reporting the required check. Candidate code sees only its disposable checkout, with `.git` read-only; it sees no App key, host controller, or Docker socket. Missing/skipped/failed/cancelled/timeout checks cannot pass. Preparation invalidates previous results before fallible work, proposal/review events invalidate dependent checks, and publication rejects superseded requests. GitHub event delivery is asynchronous; this does not provide an atomic approval-and-merge transaction. Branch protection requires the designated App and an up-to-date branch. Credentials and protection are owner-provisioned prerequisites, not claims a local installer can establish.

The configured Linux toolchain image must be digest-pinned and contain required toolchains/dependencies. Dependency credentials are not provided to candidate jobs; build the reviewed image separately. Checks execute with network disabled. Projects declare their appropriate smoke command; application projects include a startup/basic-workflow smoke check executed inside the image.

Store the App key only in environment `aek-authority`, restricted by one custom branch rule to the repository default branch. Trusted preparation/publication jobs use that environment; manual dispatch from other branches is excluded. Administration/Actions read permissions inspect protection, while agent credentials cannot administer it. The owner must ensure no candidate-accessible copy of the key exists.

Architecture summaries and decisions are versioned. Load bounded architecture, task and harness context at task start, resume, compaction and worktree changes. Executable architecture rules reference required checks; other rules explicitly require review. Boundary changes are proposed and approved before implementation. GitHub approval of a snapshot containing those documents is the approval record.

Task state is namespaced by worktree/task, written atomically with revision conflict checks. Explicit parallel requests can create isolated worktrees with declared interface/file ownership. The CLI does not launch agents. Independent review is also explicitly requested; otherwise disclose self-review.

Graphify 0.9.85 is optional and installed in an isolated environment. Default extraction uses `--code-only` and one worker. Semantic extraction requires a live human-approved project opt-in and an explicit backend. Provenance includes repository/worktree, commit, source fingerprint, dependency version, and graph digest. Stale or modified indexes cannot be queried as current evidence; source citations still need inspection.

Shipping reruns approval and verification, records the exact reviewed commit, uses the restricted agent identity and opens/updates a draft PR referencing its proposal. Remote integration verification remains mandatory. There is no automatic merging, deployment, or implicit parallel execution.

Delivery includes four increments: foundation/CI, context/Graphify, requested coordination, and release gates. Acceptance covers actual Python/JS/Go/Rust runner fixtures and a Linux/macOS/Windows CI matrix. Live platform/agent/container checks must be distinguished from mocked or pending checks.
