# Troubleshooting

Read the reported error and inspect status before retrying. Do not weaken tests, protection, or required checks to get a green result.

| Symptom | Resolution |
|---|---|
| `aek` not found | Add the installer's reported bin directory to PATH; reopen terminals/apps. Call the source launcher meanwhile |
| Python too old or missing | Use Python 3.11+; reinstall/update with a persistent interpreter |
| PowerShell script blocked | Run `py -3 scripts/aek.py install --agent both` directly |
| Unmanaged/modified file collision | Inspect conflicting paths. Preserve them or use backed-up `--replace` intentionally |
| Installed update cannot find fresh source | Supply `aek update --source /path/to/fresh/kit --agent both` |
| `doctor` says no enrolled project | Installation succeeded but that repository is not enrolled; propose enrollment there |
| `init --accept` returns 1 with `enrolled: true` | Local enrollment completed; owner CI/identity/protection setup is still incomplete |
| Project already enrolled | Do not rerun acceptance. Review policy through governance; new clones need local hook rebinding |
| Hooks configured but edits succeed | Trust Codex hooks/reload Antigravity and test actual tool coverage; disk configuration is not activation |
| Git guard does not run in one worktree | Inspect effective `core.hooksPath`, including worktree-local overrides; repair explicitly without discarding unrelated hooks |
| Intentional harness commit blocked | Commit only in the proposal workspace with exact `ALLOW_TEST_EDITS=1`; this provides no approval |
| Publishing identity is a human approver or repository admin | Configure an isolated restricted agent identity; do not use human approval credentials |
| App/environment/protection diagnostics fail | Owner must provision the designated App check, exact default-branch environment policy and sufficient read diagnostics permissions |
| Approval missing/stale/dismissed | Have an allowed human review the exact proposal commit and marker again; comments/local flags do not count |
| Target branch harness changed | Reconcile the proposal to the current protected content and obtain reapproval |
| Tests tampered with but restored tests pass | Failure is intentional. Revert unintended edits or propose/approve the intended change; original files are preserved |
| Required runner or dependency missing | Install/configure the real dependency locally and in the reviewed CI image; do not skip its check |
| Python dependencies exist only in a project venv | `{python}` uses AEK's interpreter. Use a reviewed explicit runner/environment arrangement |
| Cargo `--locked` fails | Review and commit the appropriate lockfile in the proposal; do not remove locked validation |
| Inline-test source cannot be edited | Whole-file protection is intentional. Move tests to separate protected files through approved governance/proposal before implementation |
| Container writes fail under tests/src/config parents | CI protects top-level harness parents read-only. Route generated files/caches outside them or to `/tmp` |
| Docker socket access unavailable locally | Local verify needs no Docker. Validate CI isolation on a host with Docker access; do not claim it ran from argument mocks |
| Graph index stale | Run refresh after source/policy changes and inspect source references; never relabel stale data current |
| Task revision conflict | Read current state, reconcile changes, and submit the current revision |
| Worktree ownership conflict | Agree on interfaces and separate scopes before creating workers |
| Shipping finds dirty/stale review | Commit intended source, reverify, and review the exact commit |
| Old successful CI result invalidated | A new request/proposal/review change requires revalidation. Push the feature or manually dispatch the trusted controller |
| Missing/skipped/cancelled check | Failure/incomplete evidence cannot satisfy the required App check |

Inspect local Git configuration without changing it:

```sh
git config --show-origin --get core.hooksPath
aek --json doctor
```

For online checks use `aek doctor --online` with restricted credentials. Diagnostics do not certify IDE activation or human/App credential isolation: the owner audits those separately.

Before uninstalling, disable Git hooks in each local enrolled repository. `aek init --disable` does not remove committed enrollment or CI. Leaving hooks pointed at a deleted runtime can prevent commits; restore the saved previous hook path rather than discarding all hooks.

For another device and existing clones, follow [Installation](INSTALLATION.md#clone-an-already-enrolled-project). For GitHub owner/bootstrap steps, follow [Enrollment](ENROLLMENT.md).
