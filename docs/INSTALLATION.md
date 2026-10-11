# Installation and device setup

See [README](../README.md) for the complete feature workflow and [Enrollment](ENROLLMENT.md) for GitHub authority.

## Source installation

Install Python 3.11+ and Git; Windows needs Git for Windows. Obtain the source branch/bundle containing `scripts/aek.py`.

Linux/macOS:

```sh
python3 scripts/aek.py install --agent both
```

PowerShell:

```powershell
py -3 scripts/aek.py install --agent both
```

The Unix wrapper is `sh install.sh --agent both`; the Windows wrapper is `.\install.ps1 --agent both`. Arguments belong to `install`; for other commands use `aek` or `python3 scripts/aek.py` directly. Do not pipe an unreviewed download into a shell.

The selected Python interpreter is recorded in installed launchers and hook commands. Keep it available. Reinstall/update with a new interpreter if you remove or relocate it. `{python}` runner commands use that interpreter, not necessarily your project's activated virtual environment. Configure a project runner explicitly when its dependencies live elsewhere.

## Wheel installation

In a dedicated virtual environment:

```sh
python3 -m venv /path/to/aek-env
/path/to/aek-env/bin/python -m pip install /path/to/agentic_engineering_kit-0.1.0-py3-none-any.whl
/path/to/aek-env/bin/aek install --agent both
```

Windows uses `aek-env\Scripts\python.exe` and `aek-env\Scripts\aek.exe`. Keep the environment: installed launchers use its interpreter. Installing a wheel only installs the package; `aek install` configures the selected integrations. Prefer this isolated route when your OS blocks system-level pip installs.

## Locations and PATH

| Item | Linux/macOS | Native Windows |
|---|---|---|
| Runtime | `$XDG_DATA_HOME/aek`, normally `~/.local/share/aek` | `%LOCALAPPDATA%\AEK` |
| Launcher | `~/.local/bin/aek` | `%LOCALAPPDATA%\AEK\bin\aek.cmd` |
| Codex skills/hooks/instructions | `~/.agents/skills`, `~/.codex/hooks.json`, `~/.codex/AGENTS.md` | Same directories under the user profile |
| Antigravity skills/hooks/instructions | `~/.gemini/config/skills`, `hooks.json`, `GEMINI.md` | Same directories under the user profile |

The installer report is authoritative when environment variables override defaults. Add its bin directory to PATH. For the current Unix shell use `export PATH="$HOME/.local/bin:$PATH"`; persist it once in your shell startup file. On Windows add the reported directory to user environment PATH and reopen terminals. App processes may need restarting to see a changed PATH.

## Activation and collision handling

Codex non-managed hooks require review/trust through `/hooks` in the CLI; changed definitions require renewed review. [Official OpenAI hook documentation](https://learn.chatgpt.com/docs/hooks).

Reload Antigravity and verify that its version loads the installed definitions. Test real edit-tool denial in a disposable enrolled fixture in each app. Hook JSON existing on disk is not evidence of activation. AEK retains independent CI because local hooks can be bypassed.

Installation is repeatable and preserves unrelated configuration. Unmanaged or locally modified collisions fail before replacement. Review them; `--replace` permits backed-up replacement. The installation manifest and timestamped backups live alongside the runtime. Do not delete backups until satisfied with the update. `--home /temporary/home` is available for isolated installation experiments.

## Clone an already enrolled project

Committed `.aek/project.json` travels with the clone; Git configuration, approvals, graph indexes, and task state do not. The current CLI deliberately refuses `init --accept` when policy already exists. Install AEK first, then restore local guards using the core's enrollment helper:

```sh
cd /path/to/cloned-project
python3 -c 'import runpy; from pathlib import Path; runpy.run_path(str(Path.home()/".local/share/aek/scripts/aek.py")); from aek.install import enroll_hooks; from aek.common import root_at; print(enroll_hooks(root_at(".")))'
```

Use the installed interpreter and reported runtime path if your location differs. A clearer portable form, including Windows, is:

```python
# Save as a temporary setup script outside protected project files.
import runpy
runpy.run_path("/absolute/reported/runtime/scripts/aek.py")
from aek.common import root_at
from aek.install import enroll_hooks
print(enroll_hooks(root_at("/absolute/path/to/project")))
```

Run this with Python 3.11+. It wires local hooks and forwards previous hooks without changing committed policy; it does not establish approval. With restricted credentials, run `aek doctor --online` and import the current proposal with `aek harness freeze --proposal NUMBER` on the corresponding clean snapshot. If your clone is on the default branch, use `aek harness workspace` and the reviewed proposal workflow instead. Do not invent a local approval flag.

A dedicated public rebind subcommand is not currently provided; the explicit Python helper above is the supported implementation-level setup route for existing clones.

## Update and removal

```sh
aek update --source /path/to/fresh/source --agent both
```

This reads your supplied source, not an automatic remote download. Reload agents and review changed Codex definitions. Global updates do not update a project's protected `.aek/ci` copy: use a separately reviewed owner governance change.

Before uninstalling, run `aek init --disable` in every enrolled local repository. Then `aek uninstall` removes unchanged owned files/entries, restores backed-up originals, and preserves local modifications. Disablement only restores Git hooks; committed enrollment and remote checks remain. Full project de-enrollment needs owner review.

For the older global Harness Lock, explicitly add `--migrate-legacy` to install/update. It checks known ownership, records backups, restores that tool's saved global Git hooks path, and removes only its owned Antigravity entry. Unknown guards are not silently removed.
