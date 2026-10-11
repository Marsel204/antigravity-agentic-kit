from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from .common import Error, digest, git, read_json, root_at, state_dir, write_json
from . import policy
from .context import context


def blocked_paths(root, paths, config):
    blocked = []
    for name in paths:
        # Both lexical path and resolved target matter for symlink aliases.
        path = Path(name) if Path(name).is_absolute() else root / name
        for candidate in [Path(os.path.abspath(path)), path.resolve()]:
            try:
                relative = candidate.relative_to(root).as_posix()
            except ValueError:
                continue
            if policy.protected(relative, config):
                blocked.append(name)
                break
    return blocked


def patch_paths(patch):
    if not isinstance(patch, str):
        raise Error("Patch input must be a string.")
    result = []
    for line in patch.splitlines():
        match = re.match(
            r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", line
        )
        if match:
            result.append(match.group(1))
    if not result:
        raise Error("Cannot determine file targets from patch.")
    return result


def tool_paths(value):
    result = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() in [
                "targetfile",
                "target_file",
                "file_path",
                "filepath",
                "path",
                "destination",
                "source",
            ] and isinstance(item, str):
                result.append(item)
            elif isinstance(item, (dict, list)):
                result.extend(tool_paths(item))
    elif isinstance(value, list):
        for item in value:
            result.extend(tool_paths(item))
    return result


def patch_input(args):
    if isinstance(args, dict):
        return next(
            (
                args[k]
                for k in ["command", "input", "patch"]
                if isinstance(args.get(k), str)
            ),
            "",
        )
    return args


def target_roots(cwd, paths):
    roots = set()
    for name in paths:
        path = Path(name) if Path(name).is_absolute() else Path(cwd) / name
        for candidate in [Path(os.path.abspath(path)), path.resolve()]:
            parent = candidate.parent
            while not parent.exists() and parent != parent.parent:
                parent = parent.parent
            try:
                roots.add(root_at(parent))
            except Error:
                continue
    return roots


def adapter(name, payload):
    try:
        if not isinstance(payload, dict):
            raise Error("Hook input must be a JSON object.")
        cwd = (
            payload.get("cwd")
            or payload.get("workingDirectory")
            or (payload.get("workspacePaths") or [os.getcwd()])[0]
        )
        event = payload.get("hook_event_name", "PreToolUse")
        args = payload.get("tool_input", {})
        if (
            name == "codex"
            and event == "PostToolUse"
            and isinstance(args, dict)
            and args.get("workdir")
        ):
            cwd = args["workdir"]
        if name == "antigravity":
            targets = tool_paths(payload.get("toolCall", {}).get("args", {}))
            for workspace in payload.get("workspacePaths", []):
                if any(
                    Path(target).is_absolute()
                    and Path(target).is_relative_to(Path(workspace))
                    for target in targets
                ):
                    cwd = workspace
                    break
        try:
            root = root_at(cwd)
        except Error:
            root = None
        if root is None or not (root / policy.CONFIG).exists():
            paths = (
                tool_paths(args)
                if name == "codex"
                else tool_paths(payload.get("toolCall", {}).get("args", {}))
            )
            if name == "codex" and payload.get("tool_name") == "apply_patch":
                try:
                    paths = patch_paths(patch_input(args))
                except Error:
                    paths = []
            root = next(
                (r for r in target_roots(cwd, paths) if (r / policy.CONFIG).is_file()),
                None,
            )
            if root is None:
                if name == "antigravity" and "invocationNum" in payload:
                    return {"injectSteps": []}
                return {"decision": "allow"} if name == "antigravity" else {}
        config = policy.load(root)
        if name == "antigravity" and "invocationNum" in payload:
            if "context" not in config["modules"]:
                return {"injectSteps": []}
            return {
                "injectSteps": [
                    {"ephemeralMessage": json.dumps(context(root), ensure_ascii=True)}
                ]
            }
        if name == "codex" and event in [
            "SessionStart",
            "UserPromptSubmit",
            "PostToolUse",
        ]:
            if "context" not in config["modules"]:
                return {}
            value = context(root)
            fingerprint = digest(value)
            cache = state_dir(root) / "context-hook.json"
            previous = read_json(cache) if cache.exists() else {}
            if event == "PostToolUse" and previous.get("digest") == fingerprint:
                return {}
            write_json(cache, {"digest": fingerprint})
            return {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": json.dumps(value, ensure_ascii=True),
                }
            }
        if name == "codex":
            tool = payload.get("tool_name", "")
            args = payload.get("tool_input", {})
            if tool == "apply_patch":
                patch = patch_input(args)
                paths = patch_paths(patch)
            else:
                if not re.search(r"write|edit|replace|delete|move", tool, re.I):
                    return {}
                paths = tool_paths(args)
                # Unknown MCP tool schemas aren't a complete file-write boundary.
                if not paths:
                    raise Error(
                        "Cannot determine write targets for this MCP tool schema."
                    )
        else:
            call = payload.get("toolCall", {})
            tool = call.get("name", "")
            if tool not in [
                "write_to_file",
                "replace_file_content",
                "multi_replace_file_content",
            ]:
                return {"decision": "allow"}
            paths = tool_paths(call.get("args", {}))
            if not paths:
                raise Error("Cannot determine write target.")
        denied = []
        absolute_paths = [
            str(Path(p) if Path(p).is_absolute() else Path(cwd) / p) for p in paths
        ]
        for target in target_roots(cwd, paths):
            if not (target / policy.CONFIG).is_file():
                continue
            target_config = policy.load(target)
            authoring = (
                git(
                    target,
                    "config",
                    "--local",
                    "--get",
                    "aek.proposalWorkspace",
                    check=False,
                )
                .stdout.decode()
                .strip()
                == "true"
            )
            author_root = (
                git(
                    target,
                    "config",
                    "--local",
                    "--get",
                    "aek.proposalRoot",
                    check=False,
                )
                .stdout.decode()
                .strip()
            )
            authoring = (
                authoring
                and bool(author_root)
                and Path(author_root).resolve() == target.resolve()
            )
            # Authoring is scoped to its dedicated clone; it never authorizes CI.
            if not authoring:
                denied.extend(blocked_paths(target, absolute_paths, target_config))
        if not denied:
            return {"decision": "allow"} if name == "antigravity" else {}
        reason = (
            "Harness/architecture is locked. Propose changes in a separate test workspace and obtain human approval: "
            + ", ".join(denied)
        )
    except (Error, ValueError, TypeError) as exc:
        reason = f"AEK cannot validate this tool call: {exc}"
    if name == "antigravity":
        return {"decision": "deny", "reason": reason}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def git_hook(event, argv):
    try:
        root = root_at()
    except Error:
        # Non-commit events can run before Git repository discovery is ready.
        return 0
    config_path = root / policy.CONFIG

    def guard():
        if os.environ.get("ALLOW_TEST_EDITS") == "1" or not config_path.exists():
            return
        config = policy.load(root)
        paths = [
            os.fsdecode(x)
            for x in git(
                root, "diff", "--cached", "--name-only", "--no-renames", "-z"
            ).stdout.split(b"\0")
            if x
        ]
        denied = blocked_paths(root, paths, config)
        if denied:
            raise Error(
                "Harness/architecture is locked. Staged protected files: "
                + ", ".join(denied)
                + "\nUse a reviewed test proposal. Intentional local commits may use ALLOW_TEST_EDITS=1; CI approval is still required."
            )

    guarded = event in ["pre-commit", "pre-merge-commit", "pre-applypatch"]
    if guarded:
        guard()
    previous = (
        git(root, "config", "--local", "--get", "aek.previousHooksPath", check=False)
        .stdout.decode()
        .strip()
    )
    if previous:
        path = Path(previous) / event
        effective = (
            git(root, "config", "--get", "core.hooksPath").stdout.decode().strip()
        )
        if path.is_file() and path.parent.resolve() != Path(effective).resolve():
            # Native hooks may read stdin; don't capture it or hide their output.
            shell = shutil.which("sh")
            if not shell and os.name == "nt":
                git_binary = Path(shutil.which("git") or "")
                for parent in git_binary.parents:
                    candidate = parent / "bin/sh.exe"
                    if candidate.is_file():
                        shell = str(candidate)
                        break
            if not shell:
                raise Error(
                    "Cannot find the shell for an existing Git hook; install Git for Windows or a POSIX shell."
                )
            process = subprocess.run(
                [shell, "-c", 'exec "$0" "$@"', path.as_posix(), *argv]
            )
            if process.returncode:
                return process.returncode
    if guarded:
        guard()  # A forwarded hook could stage protected files.
    return 0
