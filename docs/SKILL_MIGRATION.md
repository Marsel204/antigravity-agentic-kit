# Composable skills migration

Everyday engineering now uses selected skills from [mattpocock/skills](https://github.com/mattpocock/skills), vendored at commit `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`. Installation requires no upstream download: each skill's references, invocation metadata, source notice, and MIT license travel with the kit. Updates remain reviewed changes to this repository rather than automatic upstream updates.

## Update another machine

Fetch and check out the reviewed branch or release containing this migration in a clean kit checkout. Run its **source launcher**, since an older installed `aek` does not recognize the new flag:

```sh
python3 scripts/aek.py update --agent both --migrate-skills
```

PowerShell:

```powershell
py -3 scripts/aek.py update --agent both --migrate-skills
```

Use `--agent codex` or `--agent antigravity` to update only that integration. The shared runtime is updated either way. For a first installation, use `install --agent ...` without the migration flag. For a disposable rehearsal, add `--home /path/to/temporary-home`.

Inspect the returned `skill_migration.retired`, `skill_migration.preserved`, and `backup` fields. Backups live alongside the runtime under `aek-backups-*`; retired directories retain their files and local additions under `retired-skills/<integration>/<name>`. `skill-migration.json` maps every retired path to its archive, `file-backups.json` maps replaced files to their saved contents, and `installation-before.json` records the previous installation manifest when directories are retired. Keep those files until the update has been accepted on the machine.

The migration retires only manifest-owned AEK skills, exact known older AEK entry points, or adaptations declaring the AEK source repository in their frontmatter. It also checks older Codex copies under `~/.codex/skills`, including `agentic-plan`. Unknown same-named skills and symlinked directories are preserved and reported for manual review. An AEK marker in unrelated prose does not establish ownership. Selected integrations' other skills are updated through the ordinary installer rules; locally modified or unmanaged collisions still stop the update before any retirement. Resolve those specific differences before retrying. `--replace` remains a separate, broad, backed-up replacement option; it is not needed for a normal owned migration.

Reload the agent after installation; Codex discovers the replacement skills on the next turn or session. If hook definitions change, review them through the agent's normal hook trust mechanism. Device installation changes no repository enrollment, frozen approvals, GitHub permissions, or enrolled CI controller.

## Skill mapping

| Retired everyday entry point | Replacement |
| --- | --- |
| `engineering-lifecycle` | Individual skills as needed; no mandatory universal wrapper |
| `spec` | `grill-with-docs` when exploration is requested, then `to-spec` |
| `plan`, older `agentic-plan` | Native planning; `to-tickets` for larger work |
| `test` | `tdd` |
| `build` | `implement` |
| `review` | `code-review` |
| Duplicate `systematic-debugging` entry | Existing `debug` skill |
| AEK's `pr` | Matt's `pr` for body writing; publishing follows project tooling |
| `init` | `aek-init` for AEK setup/enrollment; ordinary setup uses the project's conventions |
| `verify` | Project checks; `aek-verify` for enrolled verification/review evidence |
| `ship` | Project publishing; `aek-ship` for enrolled restricted draft-PR delivery |

Supporting skills are included so the entry points are self-contained: `grilling`, `domain-modeling`, `codebase-design`, and optional `setup-matt-pocock-skills`. The latter can configure tracker/domain-document conventions but is not a prerequisite for local specs, tickets, implementation, or review.

`debug`, `context-mode`, `terse-action`, `ui-workflow`, `impeccable`, `archify`, and `flowchart` remain. The UI workflow now points to the replacement engineering skills. Other installed UI, desktop, embedded, hardware, system, and plugin skills remain outside this migration's retirement list.

## Preserved AEK controls

AEK remains optional by repository. For an enrolled repository, `aek-workflow` coordinates `aek-harness`, `aek-verify`, and `aek-ship`; `aek-init` handles setup and initial enrollment. Exact human approval, protected architecture/harness snapshots, committed-source verification, honest review records, restricted publishing identity, and independent CI remain required. Generic TDD cannot edit a frozen harness in an implementation tree. Deleting skill files does not disable enrollment or confer approval.

## Local adaptations to upstream

- Existing authorization and settled decisions are reused; ordinary implementation does not pause to reapprove every testing boundary. Material unanswered choices and enrolled approval requirements remain explicit.
- Research and review are sequential by default. Independent reviewers require a request, and parallel agents require an explicit parallel request, including the design-alternatives reference.
- Skills load through the host's native mechanism or by reading their files when no Skill tool exists. Codex invocation policies live in the supplied `agents/openai.yaml` files.
- Specs/tickets can stay in local Markdown without running setup; external issue publication follows the user's authorized scope.
- Code review includes the selected committed changes, staged and unstaged work, and relevant untracked files. Self-review is disclosed. Enrolled release evidence is recorded separately against the exact committed implementation.
- The implementation skill follows the repository's commit/publishing policy. The PR skill writes descriptions and does not replace publishing controls.

## Recovery

The migration is repeatable. A second run does not rearchive removed directories, and subsequent local changes to replacement skills retain the installer's normal collision protection.

To recover a particular retired skill, close the agent, inspect its mapped backup, and copy that directory back to the original path after resolving any existing destination. Restore only the intended files; doing so makes the old entry point active again. Backups are retained after kit uninstall and are not automatically restored as active legacy skills. New skill files follow the installer's existing uninstall/restore behavior. Reverting to a complete older kit release is a separate explicit rollback; keep the backup manifest and original checkout for that purpose.
