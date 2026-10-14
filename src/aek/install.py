from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import sys
import time

from .common import Error, atomic_write, git, read_json, write_json, is_link

SOURCE = Path(__file__).resolve().parents[2]
if not (SOURCE / "templates").is_dir():
    SOURCE = Path(__file__).resolve().parent / "bundle"
EVENTS = [
    "pre-commit",
    "pre-merge-commit",
    "pre-applypatch",
    "post-checkout",
    "post-merge",
    "pre-push",
    "commit-msg",
    "prepare-commit-msg",
    "applypatch-msg",
    "post-applypatch",
    "post-commit",
    "pre-rebase",
    "post-rewrite",
    "post-update",
    "pre-auto-gc",
    "reference-transaction",
    "push-to-checkout",
    "pre-receive",
    "update",
    "post-receive",
    "proc-receive",
    "post-index-change",
    "sendemail-validate",
    "fsmonitor-watchman",
]


def data_home(home=None):
    if home:
        return Path(home) / ".local" / "share" / "aek"
    if os.name == "nt":
        return (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            / "AEK"
        )
    return (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "aek"
    )


def hook_definitions(runtime, adapter):
    entry = runtime / "scripts" / "aek.py"
    command = shlex.join(
        [sys.executable.replace("\\", "/"), entry.as_posix(), "adapter", adapter]
    )
    windows = __import__("subprocess").list2cmdline(
        [sys.executable, str(entry), "adapter", adapter]
    )
    if adapter == "codex":

        def event(matcher=None):
            value = {
                "hooks": [
                    {
                        "type": "command",
                        "command": command,
                        "commandWindows": windows,
                        "timeout": 30,
                        "statusMessage": "AEK: harness and context",
                    }
                ]
            }
            if matcher:
                value["matcher"] = matcher
            return value

        return {
            "PreToolUse": [
                event(
                    "apply_patch|Edit|Write|mcp__.*(?:write|edit|replace|delete|move).*"
                )
            ],
            "SessionStart": [event("startup|resume|clear|compact")],
            "UserPromptSubmit": [event()],
            "PostToolUse": [event("Bash")],
        }
    return {
        "enabled": True,
        "PreToolUse": [
            {
                "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
                "hooks": [
                    {
                        "type": "command",
                        "command": windows if os.name == "nt" else command,
                    }
                ],
            }
        ],
        "PreInvocation": [
            {"type": "command", "command": windows if os.name == "nt" else command}
        ],
    }


def validate_hooks(data, adapter):
    if not isinstance(data, dict):
        raise Error("Hook configuration must be an object.")
    if adapter == "codex":
        groups = data.get("hooks", {})
        if not isinstance(groups, dict):
            raise Error("Codex hooks must be an event map.")
        for values in groups.values():
            if not isinstance(values, list) or any(
                not isinstance(v, dict)
                or not isinstance(v.get("hooks"), list)
                or any(not isinstance(h, dict) for h in v["hooks"])
                for v in values
            ):
                raise Error(
                    "Codex hook events must contain hook groups with handler lists."
                )


def without_owned_codex(data):
    result = json.loads(json.dumps(data))
    for event, groups in result.get("hooks", {}).items():
        kept = []
        for group in groups:
            hooks = [
                h
                for h in group.get("hooks", [])
                if not h.get("statusMessage", "").startswith("AEK:")
            ]
            if hooks:
                kept.append(dict(group, hooks=hooks))
        result["hooks"][event] = kept
    return result


def configure_hooks(path, runtime, adapter, remove=False):
    data = read_json(path) if path.exists() else {}
    validate_hooks(data, adapter)
    original = json.dumps(data, indent=2) + "\n"
    if adapter == "codex":
        data = without_owned_codex(data)
        if not remove:
            for event, groups in hook_definitions(runtime, adapter).items():
                data.setdefault("hooks", {}).setdefault(event, []).extend(groups)
    else:
        if not remove:
            data["aek"] = hook_definitions(runtime, adapter)
        else:
            data.pop("aek", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not path.with_suffix(".json.aek-backup").exists():
        atomic_write(path.with_suffix(".json.aek-backup"), original)
    write_json(path, data)


def install(adapters, home=None, replace=False, source=None):
    # Normalize OS-level parent aliases (macOS /var -> /private/var) before
    # rejecting symlinks inside the selected installation destinations.
    home = (Path(home) if home else Path.home()).resolve()
    runtime = data_home(home if home != Path.home().resolve() else None)
    manifest_path = runtime.parent / "aek-installation.json"
    manifest = (
        read_json(manifest_path)
        if manifest_path.exists()
        else {"files": {}, "adapters": []}
    )
    source = Path(source).resolve() if source else SOURCE
    if not all(
        (source / item).exists()
        for item in ["src/aek/cli.py", "scripts/aek.py", "skills", "templates"]
    ):
        raise Error("Installation source must be a complete kit checkout or bundle.")
    if source == runtime:
        raise Error(
            "Run update --source PATH with a freshly checked-out kit, or use its source launcher."
        )
    targets = {}
    shared = []
    instruction_updates = {}
    for folder in ["src", "scripts", "templates", "skills"]:
        for path in (source / folder).rglob("*"):
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix != ".pyc"
            ):
                targets[runtime / path.relative_to(source)] = path.read_bytes()
    bin_dir = home / ".local" / "bin" if os.name != "nt" else runtime / "bin"
    launcher = (
        "#!/bin/sh\nexec "
        + shlex.join([sys.executable, str(runtime / "scripts" / "aek.py")])
        + ' "$@"\n'
    )
    targets[bin_dir / "aek"] = launcher.encode()
    targets[bin_dir / "aek.cmd"] = (
        '@echo off\r\n"'
        + sys.executable
        + '" "'
        + str(runtime / "scripts" / "aek.py")
        + '" %*\r\n'
    ).encode()
    skill_dirs = []
    if "codex" in adapters:
        skill_dirs.append(home / ".agents" / "skills")
    if "antigravity" in adapters:
        skill_dirs.append(home / ".gemini" / "config" / "skills")
    for directory in skill_dirs:
        for path in (source / "skills").rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                targets[directory / path.relative_to(source / "skills")] = (
                    path.read_bytes()
                )
    # Validate all collisions before changing anything.
    for adapter in adapters:
        path = (
            home / ".codex/hooks.json"
            if adapter == "codex"
            else home / ".gemini/config/hooks.json"
        )
        if path.exists():
            data = read_json(path)
            validate_hooks(data, adapter)
            if (
                adapter == "antigravity"
                and "aek" in data
                and (runtime / "scripts/aek.py").as_posix()
                not in json.dumps(data["aek"]).replace(chr(92), "/").replace("//", "/")
            ):
                raise Error(
                    "An unrelated Antigravity hook owns the name aek; preserve it and rename it before installation."
                )
        instructions = (
            home / ".codex/AGENTS.md"
            if adapter == "codex"
            else home / ".gemini/config/GEMINI.md"
        )
        if instructions.exists():
            text = instructions.read_text(encoding="utf-8")
            if (
                text.count(START) != text.count(END)
                or text.count(START) > 1
                or (START in text and text.find(END) < text.find(START))
            ):
                raise Error(f"Malformed instruction markers in {instructions}.")
            if START in text and managed_block(text) != manifest.get(
                "instruction_blocks", {}
            ).get(str(instructions), managed_block_text()):
                if not replace:
                    raise Error(
                        f"Preserving modified AEK instructions in {instructions}; use --replace to back them up."
                    )
                instruction_updates[instructions] = text
    for path, content in targets.items():
        if is_link(path) or any(is_link(parent) for parent in path.parents):
            if path.is_file() and path.read_bytes() == content:
                shared.append(path)
                continue
            raise Error(f"Installation destination uses a symlink: {path}")
        if path.exists() and path.read_bytes() != content:
            old_digest = manifest["files"].get(str(path), {}).get("digest")
            current = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            if old_digest != current and not replace:
                raise Error(
                    f"Preserving modified/unmanaged file: {path}. Use --replace to back it up and replace."
                )
    backup = runtime.parent / ("aek-backups-" + str(time.time_ns()))
    for path, content in instruction_updates.items():
        backup.mkdir(parents=True, exist_ok=True)
        atomic_write(
            backup / (__import__("hashlib").sha256(str(path).encode()).hexdigest()),
            content,
        )
    for path, content in targets.items():
        if path in shared:
            continue
        if path.exists() and (
            path.read_bytes() != content or str(path) not in manifest["files"]
        ):
            relative = __import__("hashlib").sha256(str(path).encode()).hexdigest()
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup / relative)
            if str(path) not in manifest["files"]:
                manifest.setdefault("backups", {}).setdefault(
                    str(path), str(backup / relative)
                )
        atomic_write(path, content)
        if (
            path.name in ["aek", "aek.py"]
            or path.suffix == ".sh"
            or content.startswith(b"#!")
        ):
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        manifest["files"][str(path)] = {
            "digest": __import__("hashlib").sha256(content).hexdigest()
        }
    for adapter in adapters:
        path = (
            home / ".codex" / "hooks.json"
            if adapter == "codex"
            else home / ".gemini" / "config" / "hooks.json"
        )
        configure_hooks(path, runtime, adapter)
        instructions = (
            home / ".codex/AGENTS.md"
            if adapter == "codex"
            else home / ".gemini/config/GEMINI.md"
        )
        update_instructions(instructions, remove=False)
        manifest.setdefault("instruction_blocks", {})[str(instructions)] = (
            managed_block_text()
        )
    manifest["adapters"] = sorted(set(manifest["adapters"]) | set(adapters))
    manifest["runtime"] = str(runtime)
    manifest["home"] = str(home)
    write_json(manifest_path, manifest)
    return {
        "runtime": str(runtime),
        "bin": str(bin_dir),
        "adapters": adapters,
        "projects_enrolled": 0,
        "codex_hooks": "configured; review and trust using /hooks",
        "antigravity_hooks": "configured; reload and validate in Antigravity",
        "path_setup": f"Add {bin_dir} to PATH if it is not already present.",
    }


START, END = "<!-- AEK:BEGIN -->", "<!-- AEK:END -->"
INSTRUCTIONS = """For repositories enrolled with .aek/project.json, load `aek context` at task start,
resume, compaction, and worktree switches. Author harness/architecture proposals in a
dedicated `aek harness workspace`; implement against the human-approved frozen snapshot.
Local flags and state files cannot grant approval. Architecture boundary changes need
human approval before implementation. Launch parallel agents only on explicit request.
Run declared checks with `aek verify`; use the restricted publishing identity and `aek ship`
for draft PR delivery. Merging/deployment remain separate requests. Unenrolled projects
retain their existing workflow and do not have AEK enforcement.\n"""


def managed_block_text():
    return START + "\n" + INSTRUCTIONS + END


def managed_block(content):
    return START + content.split(START, 1)[1].split(END, 1)[0] + END


def update_instructions(path, remove=False):
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    if (
        (START in content) != (END in content)
        or content.count(START) > 1
        or content.count(END) > 1
        or (START in content and content.find(END) < content.find(START))
    ):
        raise Error(
            f"Malformed AEK instruction markers in {path}; preserve and repair them manually."
        )
    if START in content:
        before, rest = content.split(START, 1)
        _, after = rest.split(END, 1)
        content = before.rstrip("\n") + after
    if not remove:
        content = (
            content.rstrip("\n") + "\n\n" + START + "\n" + INSTRUCTIONS + END + "\n"
        )
    atomic_write(path, content)


def migrate_legacy(home=None):
    """Explicit migration of the previous standalone tool, not arbitrary global hooks."""
    from .common import run

    home = Path(home) if home else Path.home()
    legacy = home / ".local/share/harness-lock"
    expected = str(legacy / ".githooks")
    current = (
        run(["git", "config", "--global", "--get", "core.hooksPath"], check=False)
        .stdout.decode()
        .strip()
    )
    result = {"git_changed": False, "antigravity_changed": False}
    if current == expected:
        hook = legacy / ".githooks/pre-commit"
        if not hook.exists() or "ALLOW_TEST_EDITS" not in hook.read_text():
            raise Error(
                "Legacy hook ownership cannot be confirmed; refusing migration."
            )
        previous = (
            run(
                ["git", "config", "--global", "--get", "harnessLock.previousHooksPath"],
                check=False,
            )
            .stdout.decode()
            .strip()
        )
        write_json(
            data_home(home).parent / "aek-legacy-migration.json",
            {"core.hooksPath": current, "previous": previous},
        )
        if previous and previous != current:
            run(["git", "config", "--global", "core.hooksPath", previous])
        else:
            run(["git", "config", "--global", "--unset-all", "core.hooksPath"])
        result["git_changed"] = True
    path = home / ".gemini/config/hooks.json"
    if path.exists():
        data = read_json(path)
        named = data.get("harness-lock")
        if named and str(legacy) in json.dumps(named):
            atomic_write(path.with_suffix(".json.legacy-backup"), path.read_bytes())
            del data["harness-lock"]
            write_json(path, data)
            result["antigravity_changed"] = True
    return result


def uninstall(home=None):
    home = (Path(home) if home else Path.home()).resolve()
    runtime = data_home(home if home != Path.home().resolve() else None)
    manifest_path = runtime.parent / "aek-installation.json"
    manifest = read_json(manifest_path)
    preserved = []
    for name, metadata in manifest["files"].items():
        path = Path(name)
        if not path.exists():
            continue
        if (
            path.is_symlink()
            or __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            != metadata["digest"]
        ):
            preserved.append(name)
            continue
        backup = manifest.get("backups", {}).get(name)
        if backup and Path(backup).exists():
            shutil.copy2(backup, path)
        else:
            path.unlink()
    for adapter in manifest["adapters"]:
        path = (
            home / ".codex" / "hooks.json"
            if adapter == "codex"
            else home / ".gemini" / "config" / "hooks.json"
        )
        if path.exists():
            configure_hooks(path, runtime, adapter, remove=True)
        instructions = (
            home / ".codex/AGENTS.md"
            if adapter == "codex"
            else home / ".gemini/config/GEMINI.md"
        )
        if instructions.exists():
            text = instructions.read_text(encoding="utf-8")
            if START in text and (
                END not in text
                or managed_block(text)
                != manifest.get("instruction_blocks", {}).get(
                    str(instructions), managed_block_text()
                )
            ):
                preserved.append(str(instructions))
            else:
                update_instructions(instructions, remove=True)
    manifest_path.unlink()
    return {
        "preserved_modified_files": preserved,
        "project_hooks": "remain enrolled; use aek init --disable before uninstalling",
    }


def enroll_hooks(root, runtime=None):
    runtime = Path(runtime) if runtime else SOURCE
    previous = (
        git(root, "config", "--get", "core.hooksPath", check=False)
        .stdout.decode()
        .strip()
    )
    common = Path(git(root, "rev-parse", "--git-common-dir").stdout.decode().strip())
    if not common.is_absolute():
        common = (root / common).resolve()
    hooks = common / "aek-hooks"
    if previous and Path(previous).resolve() == hooks.resolve():
        previous = (
            git(
                root, "config", "--local", "--get", "aek.previousHooksPath", check=False
            )
            .stdout.decode()
            .strip()
        )
    elif not previous:
        previous = str(common / "hooks")
    elif not Path(previous).is_absolute():
        previous = str((root / previous).resolve())
    git(root, "config", "--local", "aek.previousHooksPath", previous)
    hooks.mkdir(parents=True, exist_ok=True)
    entry = runtime / "scripts" / "aek.py"
    for event in EVENTS:
        script = (
            "#!/bin/sh\nexec "
            + shlex.join(
                [sys.executable.replace("\\", "/"), entry.as_posix(), "git-hook", event]
            )
            + ' "$@"\n'
        )
        atomic_write(hooks / event, script)
        (hooks / event).chmod(0o755)
    git(root, "config", "--local", "core.hooksPath", str(hooks))
    # Worktree-local settings may shadow repository config; do not silently replace them.
    effective = git(root, "config", "--get", "core.hooksPath").stdout.decode().strip()
    if effective != str(hooks):
        raise Error(
            "A worktree-local hooksPath overrides enrollment. Remove the override after reviewing it."
        )
    return str(hooks)


def disable_hooks(root):
    previous = (
        git(root, "config", "--local", "--get", "aek.previousHooksPath", check=False)
        .stdout.decode()
        .strip()
    )
    if not previous:
        raise Error("No AEK enrollment hook record found.")
    git(root, "config", "--local", "core.hooksPath", previous)
    return {"hooks_restored": previous, "configuration_preserved": True}
