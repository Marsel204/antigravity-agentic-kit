# Antigravity Agentic Engineering Kit

One engineering toolkit for **Codex and Google Antigravity**, with a shared Python core and separate agent adapters. Install it once per device, then enroll each project explicitly.

**Spec → Plan → Test proposal → Human approval → Frozen harness → Implementation → Verification → Review → Draft PR**

AEK protects approved tests, fixtures, helpers, runner configuration, and architecture decisions. Local hooks catch accidental edits; independently controlled GitHub CI verifies the approved harness and current integration result. Installation alone does not approve tests or establish enforcement.

## Documentation

| Task | Guide |
|---|---|
| Install, activate, update, or uninstall | [Installation](docs/INSTALLATION.md) |
| Enroll a project and configure GitHub authority | [Enrollment](docs/ENROLLMENT.md) |
| Configure runners, protected paths, and modules | [Configuration](docs/CONFIGURATION.md) |
| Implement features and use optional modules | [Usage](docs/USAGE.md) |
| Resolve hook, credential, or verification failures | [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Understand requirements and authority boundaries | [Specification](docs/SPECIFICATION.md) |

## Requirements

| Component | Required for |
|---|---|
| Python **3.11+** and Git | Installation and local commands |
| Git for Windows | Native Windows Git hooks |
| Codex and/or Antigravity | Selected agent integrations |
| Project runtimes and dependencies | Required tests/build/type/E2E/smoke checks |
| GitHub CLI (`gh`) and restricted agent credentials | Online approval, diagnostics, proposals, shipping |
| Owner-controlled GitHub App and repository/environment protection | Independent required CI gate |
| Public, reviewed, digest-pinned Linux toolchain image | Credential-free candidate execution in GitHub Actions |

Local verification does not require Docker; independent CI executes candidate checks in Docker on Linux. Graphify is optional. Native hardware tests, other CI providers, merging, and deployment are outside the built-in workflow.

## 1. Install on each device

Linux or macOS:

```sh
git clone https://github.com/Marsel204/antigravity-agentic-kit.git
cd antigravity-agentic-kit
python3 --version
python3 scripts/aek.py install --agent both
export PATH="$HOME/.local/bin:$PATH"
aek --help
```

Use Python 3.11 or newer. Add the reported bin directory to your shell's startup PATH once if needed.

Native Windows PowerShell:

```powershell
git clone https://github.com/Marsel204/antigravity-agentic-kit.git
Set-Location antigravity-agentic-kit
py -3 --version
.\install.ps1 --agent both
$env:Path = "$env:LOCALAPPDATA\AEK\bin;$env:Path"
aek --help
```

If PowerShell blocks the script, run `py -3 scripts/aek.py install --agent both` directly. If `py` is unavailable, use a Python 3.11+ `python` command. Add the reported bin directory to your user PATH for future terminals.

Choose `--agent codex`, `--agent antigravity`, or `--agent both`. A source ZIP can be unpacked instead of cloned. Until the implementation PR merges, use its branch or source bundle; a checkout without `scripts/aek.py` contains the older kit.

The installer preserves unrelated settings and refuses unmanaged/modified file collisions. Review the paths before using `--replace`, which backs up replaced content. It does not install project dependencies or enroll repositories. [Installation](docs/INSTALLATION.md) also covers wheels, virtual environments, existing clones, and removal.

## 2. Activate the integrations

**Codex:** skills are installed to `~/.agents/skills`, hooks to `~/.codex/hooks.json`, and a managed instruction block to `~/.codex/AGENTS.md`. In the Codex CLI, use `/hooks` to review and trust the current definitions. New or changed non-managed hooks need review again. See [official OpenAI hook documentation](https://learn.chatgpt.com/docs/hooks).

**Antigravity:** skills, `hooks.json`, and a managed `GEMINI.md` block are installed under `~/.gemini/config`. Reload the app and check that your version loads the AEK definitions.

Validate a live protected-file edit denial in a disposable enrolled project in each agent. `doctor` reports configuration and project prerequisites; it does not certify IDE activation. Shell writes and disabled hooks can bypass local guards. The independent CI gate provides enforcement beyond those guards.

## 3. Enroll a project

Run this inside the target Git repository with a GitHub `origin`; do not enroll your home directory.

```sh
cd /path/to/your-project
aek init --human-id 12345678
```

Replace the number with your human GitHub account ID. Look it up without using that account's approval credentials:

```sh
gh api users/YOUR_HUMAN_LOGIN --jq .id
```

`init` prints the path of a proposed configuration. It does **not** activate protection. Review:

- Tests, fixtures, helpers, runner/configuration files, and ignored dependency artifacts.
- Required test/build/type/E2E/architecture/smoke commands and timeouts.
- Allowed human IDs, restricted agent login, and verification App ID.
- A real digest-pinned CI image containing the project's toolchains/dependencies.
- Selected modules and architecture references; Graphify is disabled by default.

Accept the reviewed file:

```sh
aek init --accept /path/printed/by/init/enrollment-proposal.json --ci
aek doctor --online
```

`enrolled: true` with `enforcement_complete: false` and exit code **1** means local files were created but enforcement needs setup. Inspect the report before retrying initialization.

The owner must review and bootstrap `.aek/` and generated workflows on the default branch, isolate credentials, configure `aek-authority`, and require `aek/verification` from the designated App. **Complete [Enrollment](docs/ENROLLMENT.md) before implementing features.** The default branch is discovered; it need not be `main`.

Git protection applies across a repository's worktrees through its common Git directory. Existing hooks are preserved/forwarded. Other repositories retain their workflow.

## 4. Implement a feature

### Propose tests and architecture

After owner bootstrap, create a dedicated authoring workspace:

```sh
aek harness workspace --task add-search --branch codex/test-add-search
cd /workspace/printed/by/aek
```

Add requirement-focused tests and proposed architecture/runner changes there; keep feature implementation out of this branch. Stage the intended files:

```sh
git add tests/search.test.js
ALLOW_TEST_EDITS=1 git commit -m 'test: define search behavior'
aek harness propose --expect-failure js-tests --branch codex/test-add-search --publish
```

Use your actual configured check name: commonly `python-tests`, `js-tests`, `go-tests`, or `rust-tests`. Repeat `--expect-failure` for multiple failures. For initial baselines or passing maintenance proposals, omit it. Inspect expected requirement failures; broken dependencies and runner setup are rejected.

PowerShell intentional commit:

```powershell
$env:ALLOW_TEST_EDITS = '1'
try { git commit -m 'test: define search behavior' }
finally { Remove-Item Env:ALLOW_TEST_EDITS }
```

The exact exception permits a local commit only. It does not grant approval or satisfy CI.

### Approve and freeze

The proposal command opens a test-only draft PR. From a separate human session, review the complete harness/audit and submit an **Approve** review containing the exact generated `AEK-HARNESS ...` marker line. Comments, local flags, and bot approvals cannot replace it.

In that authoring workspace:

```sh
aek harness freeze --proposal 123 --feature-branch codex/add-search
aek context --task add-search
```

Replace `123` with the proposal PR number. Freeze exits authoring mode. Continue on the new feature branch in this workspace. Every further protected change needs another reviewed proposal. Keep the proposal PR open and unchanged until implementation merge.

### Implement, verify, review, ship

```sh
# Edit implementation source first.
git add src/search.js
git commit -m 'feat: implement search'
aek verify
aek review --summary 'Self-review: checked behavior, architecture, and error handling.'
aek ship --title 'feat: implement search'
```

Verification compares committed, staged, and working harness content, then runs committed source with approved tests in a disposable checkout. Working files are preserved. Detected tampering fails even if restored tests pass.

Review/shipping require a clean committed tree. Shipping checks live approval, reruns checks for the exact commit, uses the restricted identity, and opens/updates a **draft PR**. Independent CI verifies the current integration result. Merging/deployment remain separate requests.

`aek verify --offline` uses a previously frozen cache for explicitly untrusted local diagnostics. It cannot authorize shipping or satisfy CI.

## Optional modules

Load relevant architecture and task context at task start, resume, compaction, and worktree changes:

```sh
aek context --task add-search --limit 12000
```

Install Graphify separately; approve `graphify.enabled: true` in project policy before refresh/query:

```sh
aek graph install
aek graph refresh
aek graph query 'which callers depend on the search interface?'
```

Graphify is pinned to `graphifyy==0.9.85`. Extraction parses code locally by default. Stale/modified indexes are rejected; inspect cited source. Semantic extraction additionally needs approved opt-in, an explicit backend, and `--semantic`.

Only after an explicit request for parallel work:

```sh
aek coordinate --task search-worker --branch codex/search-worker --owns 'src/search/**' --requested
```

This creates a worktree; it does not launch agents. State is separate per task/worktree, and overlapping ownership is rejected. See [Usage](docs/USAGE.md) for task payloads and review reporting.

## Command reference

Global options precede the command: `aek --json --path /path/to/project verify`.

| Command | Responsibility |
|---|---|
| `install`, `update`, `uninstall` | Runtime, adapters/skills, backups, cleanup |
| `init`, `doctor` | Reviewed enrollment, hook disablement, diagnostics |
| `harness workspace/propose/freeze` | Authoring clone, proposal, human approval import |
| `context`, `task show/put` | Architecture context and revisioned task state |
| `graph install/refresh/query` | Optional graph retrieval |
| `coordinate` | Requested worktree ownership |
| `verify` | Harness integrity and required checks |
| `review`, `ship` | Exact-commit review and draft PR |

Use `aek COMMAND --help` or `aek harness OPERATION --help` for current arguments. JSON reports contain evidence/status, never approval authority. Errors, failed checks, and incomplete enforcement return nonzero.

## Update, another device, and uninstall

Download a fresh checkout/bundle:

```sh
aek update --source /path/to/fresh/antigravity-agentic-kit --agent both
```

Review changed hooks and reload agents. Updates use the supplied source; they do not download releases automatically or update enrolled CI runtimes. Controller updates require an owner-reviewed governance change.

On another device, install AEK, clone each project, establish restricted credentials, and restore local Git guards. Follow [existing-project installation](docs/INSTALLATION.md#clone-an-already-enrolled-project); do not overwrite committed policy with `init --accept`. Git clone does not transfer local approvals, task state, graph indexes, hooks, or trust.

Before removal, run this in **each** enrolled local repository, then uninstall once:

```sh
aek init --disable
aek uninstall
```

Disablement restores the old Git hooks path and preserves policy for audit. It does not remove CI or disable loaded adapters while enrollment metadata remains. Uninstall preserves unrelated settings and modified owned files. Full de-enrollment is an owner-managed governance change.

The older standalone global Harness Lock migrates only with `aek install --agent both --migrate-legacy`; ordinary installation leaves it alone. Migration restores that tool's saved global hooks setting and removes its owned Antigravity entry.

## Development

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install pytest PyYAML build
python -m unittest discover -s tests -v
python scripts/sync_bundle.py --check
python -m build --wheel
```

Windows: use `.\.venv\Scripts\Activate.ps1` or its `python.exe` directly. Install npm, Go, and Rust/Cargo for all runner fixtures; set `AEK_REQUIRE_PROFILES=1` to fail instead of skipping missing runtimes.

Canonical skills live in `skills/`; `python scripts/sync_bundle.py` generates plugin copies. Lifecycle, debug, diagramming, context, and formatting skills share this repository. Separate Codex/Antigravity repositories are unnecessary.

The configured matrix covers Linux/macOS/Windows on Python 3.11/3.13. Linux implementation validation ran 100 tests: 99 passed; one native-Windows junction case skipped. Native platform, live IDE/container, and owner-provisioned GitHub enforcement validation remain prerequisites before adopting the kit in real projects.

MIT © Marselinus Nugraha
