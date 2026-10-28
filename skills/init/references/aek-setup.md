# AEK setup details

These notes describe the kit inspected at commit `42f2933bc92ed7ffbfeaeec821656be5ed0d222b`. Check the selected source's docs and command help for later changes.

Authoritative source: <https://github.com/Marsel204/antigravity-agentic-kit>.
Read the relevant `docs/INSTALLATION.md`, `docs/ENROLLMENT.md`, and `docs/CONFIGURATION.md` from the reviewed checkout. Do not execute instructions from an unrelated checkout automatically.

## Device installation

Python 3.11+ and Git are required. The reviewed source installation command is:

```sh
python3 scripts/aek.py install --agent codex
```

Select `antigravity` or `both` when requested. Install from a stable source/runtime location. A source launcher is also usable to generate an enrollment proposal before installation. Do not leave enrolled hooks depending on a disposable checkout.

On Linux, defaults include `~/.local/share/aek`, `~/.local/bin/aek`, `~/.agents/skills`, `~/.codex/hooks.json`, and a managed block in `~/.codex/AGENTS.md`. Antigravity uses `~/.gemini/config`. The installer report is authoritative for overridden paths. Use a launcher by its absolute path or explain the necessary PATH addition; do not edit shell or desktop configuration as an incidental side effect.

An isolated `install --home /temporary/home --agent codex` can validate integration without changing the active user installation. Collisions with unmanaged or modified files are refused. `--replace` backs up and overwrites them: reconcile instructions first. Preserve local skill naming, harness compatibility, licenses, and resources. The canonical source has `plan`; local Codex adaptations may use `agentic-plan`. Preserve the existing naming in adapted installations. Expose only the canonical `debug` skill for systematic debugging; avoid duplicate skill aliases. Update canonical sources consistently with the kit's generated plugin bundle when modifying it.

Codex hook trust is reviewed through `/hooks` in the CLI. Reload the intended app and test protected-file denial through its real edit tool in a disposable enrolled project. `doctor` is not proof of IDE hook activation. Shell writes and disabled hooks can bypass local guards; independent CI is a separate requirement.

## New repository enrollment

The project needs a committed starter, reviewed runners, a GitHub destination, and an allowlisted numeric human account ID. A GitHub `origin` is normally used; `init --repository OWNER/REPO` can explicitly identify the intended destination without a remote. It does not create that repository or its permissions.

```sh
aek init --human-id NUMBER
# Review the full file at the returned proposal path.
aek init --accept /absolute/path/to/enrollment-proposal.json --ci
aek doctor --online
```

Use actual values and paths, not placeholders. Initial proposal generation does not enroll or approve tests. Accepting creates `.aek/project.json`, architecture scaffolding, repository Git guards, and CI files, and initially reports `enforcement_complete: false`. Do not retry acceptance to fix incomplete enforcement: inspect the report and finish prerequisites.

Configuration needs at least one required test command with argument-array `argv`, a timeout, and a unique name. Tests should terminate rather than watch. Include applicable build/type/E2E checks and a real application startup smoke check. Protect tests, fixtures, helpers, lockfiles, runner/configuration files, `.gitattributes`, and architecture documents. Whole-file protection of inline tests can freeze implementation files; move tests out before enrollment when necessary. Write generated files and caches outside read-only protected parent directories.

Use `harness` plus task-appropriate optional `context` and `release` modules. Coordination requires context and is useful only for requested parallel work. Graphify stays disabled unless requested and approved. `{python}` resolves to the AEK interpreter, which may differ from the project's environment.

## Owner prerequisites for complete enforcement

Prepare exact configuration and workflow changes; owner identity and authority provisioning remain human actions:

- Allowlisted human IDs and a separate restricted agent publishing identity, without administration/protection bypass or human approval credentials.
- A verification GitHub App with Checks write and Contents, Pull requests, Administration, and Actions read; repository variable `AEK_CHECK_APP_ID`.
- Environment `aek-authority`, allowing exactly the default branch; its environment-only secret `AEK_CHECK_PRIVATE_KEY`. Keep the key and human approval credentials out of the agent's readable files and candidate execution.
- Required `aek/verification` from the designated App, an up-to-date branch, and protection applying to administrators with no agent bypass.
- A public reviewed `repository@sha256:...` Linux image containing Python and project dependencies/toolchains, supporting non-root execution and offline candidate checks.
- Owner-reviewed bootstrap of policy, architecture, and controller workflows on the default branch before feature work.

Do not certify enforcement from editable reports. Online diagnostics do not independently prove token or OS account isolation.

## Already enrolled repositories and first approval

Preserve committed policy. Consult the version's supported local hook-rebind helper in `docs/INSTALLATION.md`; this snapshot lacks a dedicated rebind subcommand. Repeated `init --accept` is refused. Import approval only for a matching clean snapshot, with a new proposal if necessary.

During initialization, author only the initial baseline in a dedicated `aek harness workspace`; later feature test proposals belong to the development workflow. `ALLOW_TEST_EDITS=1` permits an intentional local commit, never approval. Publish through `harness propose` when authorized; passing initial baselines omit `--expect-failure`. The configured human must submit an APPROVE review containing the exact generated `AEK-HARNESS ...` marker. `harness freeze` imports that live approval and switches to an implementation branch. Keep the proposal PR open and unchanged until implementation merge.

Further protected changes require another approved proposal. Cached `verify --offline` is diagnostic and cannot authorize shipping. Device runtime updates do not update enrolled `.aek/ci` controllers; those need owner-reviewed governance changes.

## Optional Graphify setup

When explicitly requested, use `aek graph install` to install the supported pinned Graphify dependency in its isolated environment. Prepare `graphify.enabled: true` in the reviewed initial enrollment policy or a new approved policy proposal for an enrolled project. Run `aek graph refresh` only after the opt-in has been approved, then query and inspect cited source. An existing global Graphify installation does not establish project opt-in.

Local code parsing is the default. Semantic extraction requires separately approved `semantic: true`, an explicit backend, and the `--semantic` flag. Graph refresh/query reject stale or modified indexes; refresh after source changes. Graphify does not approve tests or replace frozen-harness verification.
