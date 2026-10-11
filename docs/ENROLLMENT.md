# Enrolling a project

Run commands in the target Git repository. Do not enroll your home directory.

## 1. Review the proposed configuration

```sh
aek init --human-id YOUR_NUMERIC_GITHUB_ID
```

This saves a candidate configuration in the worktree's Git state directory; it does not enable hooks or approve a harness. Review protected paths, fixtures/helpers, runner scripts, architecture documents and commands. Supply custom commands for unsupported stacks. Command `argv` values are argument arrays; `{python}` means the running interpreter. A platform-specific command may use keys `linux`, `darwin`, `win32`, and `default`.

Each check declares a unique `name`, `kind` (`test`, `build`, `typecheck`, `e2e`, `architecture`, `smoke`, or `custom`), `argv`, `timeout`, and `required: true`. At least one test check is mandatory. Smoke/build/type checks are explicit requirements, not silently inferred substitutes for one another. Dependencies must already be available locally and in the configured CI image.

Review language-specific coverage too. Discovery proposes whole-file protection for Rust files containing inline test modules. Move tests to protected integration-test files when those source files need feature edits. Other inline tests also need whole-file protection or relocation: filename discovery cannot freeze only part of a source file. Add project-specific helpers and configuration outside the discovered paths explicitly. Review `ignored_artifacts` exclusions for dependency/build folders such as `node_modules/`, `.venv/`, and `target/`. Only ignored, untracked artifacts are excluded: tracked protected files remain locked, and ignored test additions elsewhere still fail integrity checks. Widening these exclusions requires administrator-managed enrollment. Approved Git text/EOL conversions are normalized without executing custom clean filters, and `.gitattributes` files are protected.

Select `modules` per project: `harness` is mandatory; `context`, `coordination`, and `release` are optional. Graphify has its own `graphify.enabled` opt-in. Commands for disabled modules fail instead of implicitly enabling them.

Fill in `github.agent_login`, `check_app_id`, and `verification_image`. Set `base_branch` when intentionally targeting a particular branch; otherwise GitHub's default branch is used. `test_proposal` can remain zero because frozen task state records the proposal ID.

The CI image must use `repository@sha256:...`, provide Python and the project's toolchains/dependencies, support non-root execution, and not require private pull credentials. A project's image/Dockerfile is reviewed infrastructure; the toolkit does not guess its dependencies. Candidate checks run without network access. For applications, add a smoke check that starts the application and exercises a basic operation inside the container.

CI mounts protected content read-only. For nested protected files, their top-level parent directory is read-only too, preventing directory rename/recreation from replacing the harness during a run. Write generated build/test artifacts to other directories or `/tmp`, and configure dependency caches outside those parents. Local verification checks before/after content; it is not a sandbox for hostile source.

Architecture rules are objects with `description` and an optional `check` naming an executable required check. Rules without a check are shown as requiring human review. Replace the initial summary with real responsibilities, dependency rules, interfaces and invariants before adopting a baseline.

## 2. Accept and bootstrap through the owner

```sh
aek init --accept /path/to/reviewed-enrollment-proposal.json --ci
```

Enrollment installs shared repository hooks, configuration, architecture summary and CI templates. Its nonzero/incomplete-enforcement result is intentional until remote prerequisites are established. This operation does not enroll unrelated repositories.

The human owner reviews and bootstraps these files on the default branch before feature work, using credentials unavailable to the coding agent. Security identity changes use this administrator-managed process; test proposals cannot change reviewer IDs, publishing identity, check App, or destination branch. Ordinary runner or architecture changes use a new test proposal. Protection can be extended but not narrowed through a test proposal.

Create two separate identities:

- A restricted publishing machine account/token: repository contents and pull requests sufficient to push feature branches and create PRs; no repository administrator role, Administration write, Workflows write, Actions write, Checks write, protection bypass, or human approval credentials. Diagnostics need read access to branch protection and environment policies (Administration read and Actions read for fine-grained tokens). If those read permissions are unavailable, diagnostics report incomplete enforcement. For full separation, use an isolated agent OS account/device; do not leave a human `gh` login or App key within the agent's readable files.
- A verification GitHub App: Checks write, Contents read, Pull requests read, Administration read, and Actions read. Install it only on intended repositories and set repository variable `AEK_CHECK_APP_ID`. Create environment `aek-authority`, enable custom deployment branch rules, and allow exactly the default branch with type `branch`. Store `AEK_CHECK_PRIVATE_KEY` as a secret **only in that environment**; remove any repository/organization copy accessible to candidate workflows. The key is used only in trusted preparation and publication jobs. Read permissions inspect protection; they confer no ability to change it.

The environment restriction also covers manual dispatch: changing a candidate workflow cannot expose the App key. An unrestricted repository secret would defeat that boundary. See [GitHub environment access controls](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments) and [environment policy API permissions](https://docs.github.com/en/rest/deployments/environments).

Configure protected-branch rules to require `aek/verification` from that App, require an up-to-date branch, apply protection to administrators, and prevent publishing agents from pushing directly or bypassing checks. Some repository plans do not provide these controls; enrollment is incomplete in that case. `aek doctor --online` checks the configured identity and classic branch protection, but the owner must independently audit token permissions and credential isolation. It does not certify account isolation from a filesystem scan.

Controller runtime changes are reviewed protected changes. Candidate workflows and verification reports do not establish authority. If approval or preparation fails, the required independent check cannot pass. The controller uses `workflow_run` from the default branch and manual dispatch; it never relies on the request workflow's reported success.

## 3. Propose and freeze tests

```sh
aek harness workspace --task feature-name --branch codex/test-feature-name
# cd into the returned authoring workspace
# write tests or propose architecture/runner changes; keep source implementation untouched
ALLOW_TEST_EDITS=1 git commit -am 'test: define feature behavior'
aek harness propose --expect-failure python-tests --branch codex/test-feature-name --publish
```

For newly added files, stage them before committing. On PowerShell, set `$env:ALLOW_TEST_EDITS='1'` for the commit, then remove it with `Remove-Item Env:ALLOW_TEST_EDITS`.

The dedicated clone allows authoring through file tools; local mode does not authorize CI. The workspace commits a protected proposal record naming its baseline, giving even an unchanged initial test snapshot a concrete reviewable diff. For initial baselines or passing maintenance/architecture changes, omit `--expect-failure`. New requirement failures must be explicitly declared. Rust failures for missing proposed functions, methods, or fields are flagged for human inspection; dependency and runner failures are rejected. Inspect expected assertion failures: automatic heuristics cannot prove that a test is meaningful.

The human approves the test-only draft PR through a separate session/device, including the exact generated `AEK-HARNESS ...` line in an APPROVE review. Then:

```sh
aek harness freeze --proposal 123 --feature-branch codex/feature-name
aek context
# implement source code
aek verify
aek review --summary 'Reviewed behavior, architecture, inputs, and concurrency; remaining limitations: ...'
aek ship --title 'feat: implement feature behavior'
```

Freeze exits authoring mode. Every harness/architecture change requires another reviewed snapshot. Keep its proposal PR open and unmodified until implementation merge. An implementation PR includes `AEK-PROPOSAL: 123`; CI reruns on pushes and PR/review events. Preparation first invalidates the App’s prior result; proposal changes and withdrawn reviews invalidate dependent implementation checks. Superseded workers cannot publish over a newer verification request. GitHub event delivery is asynchronous, so approval and merge remain distinct human actions. After a proposal approval, push the feature or manually dispatch the controller with its implementation PR and proposal numbers. A failure or missing check blocks merge; absence of an informative failure report is not success.

`aek verify --offline` is explicitly cached/untrusted local diagnostics. `aek ship` revalidates GitHub approval and reruns checks; it never accepts an editable local report as authority. It opens a draft PR and leaves merging/deployment to you.

## 4. Context and optional graph retrieval

```sh
aek graph install
# propose graphify.enabled=true in project policy and approve it
aek graph refresh
aek graph query 'which callers depend on this interface?'
```

Graphify is optional. `refresh` uses local code parsing. External semantic extraction also needs an approved `semantic: true`, an explicit `backend`, and `--semantic`; provider credentials are separately configured. Do not use an assistant's unrestricted Graphify skill as a substitute for AEK's data policy.

Task state commands use JSON input and compare-and-swap revisions:

```sh
aek task put task-name --input task.json --revision 0
aek context --task task-name
aek coordinate --task worker-one --branch codex/worker-one --owns 'src/service/**' --requested
```

The last command creates a worktree; it does not launch an agent. Use it only after an explicit parallel-work request. Shared decisions remain versioned, and overlapping ownership must be resolved before creating another task. Task state and graph indexes are local to each worktree; cloning on another device requires enrollment and approval import there.

## Disable and migration

Run `aek init --disable` in enrolled repositories before uninstalling the runtime. This restores the saved previous hooks path; configuration is preserved for audit. `aek uninstall` removes unchanged owned files and hook entries, restores backups of replaced unmanaged files, and preserves local modifications.

The old standalone Harness Lock may have a global `core.hooksPath` and a separate `harness-lock` Antigravity hook. Use `aek install --migrate-legacy` (or the source launcher) to explicitly migrate that known tool to enrollment-only protection. Migration verifies its ownership, saves a record/backup, restores its previous global hook path, and removes only its owned Antigravity entry. Other hooks are preserved. Without the flag, the older global guard remains active.
