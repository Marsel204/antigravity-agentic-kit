# Project configuration

Use `aek init --human-id NUMBER` to generate a candidate, then review its printed JSON path. Examples here describe fields; they are not approval records. Use the full generated schema rather than replacing it with an excerpt.

## Fields

| Field | Meaning |
|---|---|
| `schema_version` | Currently `1` |
| `profiles` | Detected language profiles; commands still need review |
| `modules` | Mandatory `harness`; optional `context`, `coordination`, `release`. Coordination needs context |
| `protected_paths` | Repository-relative patterns for complete protected files |
| `ignored_artifacts` | Reviewed exclusions for ignored, untracked dependency/build artifacts only |
| `checks` | Nonempty required command definitions; at least one test check |
| `github.repository` | `owner/repository` on github.com |
| `github.human_ids` | Numeric IDs allowed to approve exact harness reviews |
| `github.agent_login` | Separate restricted publishing account |
| `github.check_app_id` | Dedicated verification App's ID |
| `github.base_branch` | Empty discovers default branch; set only for an intentional destination |
| `github.test_proposal` | Optional proposal ID; frozen local state normally supplies it |
| `github.verification_image` | Public image reference pinned with `@sha256:...` |
| `architecture.documents` | Summary/decision paths to protect and load |
| `architecture.rules` | Descriptions, optionally linked to required executable checks |
| `graphify` | `enabled`, `semantic`, and explicit semantic `backend` |

All test/test fixture/snapshot directories, spec/test filename patterns, Python/Go test names, and configured runner paths are candidates. Governance files and `.gitattributes` are protected independently. Add custom helpers and runners outside discovered paths. Patterns are case-insensitive and accept normalized Windows separators; use forward slashes in versioned configuration. Protection applies to whole files, not selected lines.

Inline Rust tests propose protection of the containing source file. Move them to protected integration-test files before enrollment if implementation must change that file. Apply the same judgment to other inline test systems.

Ignored exclusions normally cover node_modules, virtual environments, target, dist, build and test caches. Tracked protected files still count even inside an excluded folder. Ignored test additions elsewhere still fail. Do not exclude your actual harness. Widening exclusions, removing protection, and identity/security changes require owner-managed governance; normal proposals can extend protection.

## Required commands

A check example:

```json
{
  "name": "python-tests",
  "kind": "test",
  "required": true,
  "argv": ["{python}", "-m", "pytest", "tests"],
  "timeout": 300
}
```

`argv` is an argument array, not a shell string. Commands execute in the disposable project root unless `cwd` specifies a repository-relative directory. `{python}` selects the running AEK interpreter. Timeout is 1–7200 seconds. Names are unique. Use descriptive kinds such as `test`, `build`, `typecheck`, `e2e`, `architecture`, `smoke`, or `custom`. At least one check must have kind `test`. All declared checks are required.

Platform-specific arguments can use `linux`, `darwin`, `win32`, and `default`:

```json
{
  "name": "workflow-smoke",
  "kind": "smoke",
  "required": true,
  "argv": {
    "linux": ["{python}", "scripts/smoke.py"],
    "darwin": ["{python}", "scripts/smoke.py"],
    "win32": ["{python}", "scripts/smoke.py"]
  },
  "timeout": 60
}
```

Protect any declared smoke/architecture/helper scripts. Supply real startup and basic-workflow smoke checks for applications. Commands missing on the selected platform fail; unexecutable architecture descriptions explicitly need review.

Discovery proposes pytest, package.json test/build/typecheck/test:e2e scripts with npm/pnpm/yarn, `go test`/`go build`, and locked Cargo test/check. It does not prove coverage or install dependencies. Add missing build, integration, type and smoke commands explicitly.

CI runs Linux commands with network disabled and no private pull credentials. Bake dependencies into the reviewed image and support non-root execution. Protected files and their top-level parent directories are read-only in CI; put generated files/caches elsewhere or under `/tmp`.

## Architecture and graph policy

Record module responsibilities, interfaces, dependency boundaries, and invariants in `.aek/architecture.md`; detailed decisions go under `.aek/decisions/`. A rule may refer to a check:

```json
{"description": "Domain modules cannot import the HTTP layer", "check": "architecture-imports"}
```

Without `check`, it is a review obligation. Architecture changes go through the human-reviewed proposal before implementation.

Graphify defaults to disabled local parsing policy. Enable it through a reviewed policy proposal. Semantic extraction additionally needs `semantic: true`, an explicit backend, and `aek graph refresh --semantic`; credentials/provider setup are separate. Global Graphify installation does not opt a project into extraction.
