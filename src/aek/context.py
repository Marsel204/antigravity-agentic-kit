from __future__ import annotations

from pathlib import Path
import re

from .common import Error, commit, digest, git, locked, read_json, state_dir, write_json
from . import policy


def task_path(root, name):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", name):
        raise Error(
            "Task names must use 1–80 letters, numbers, underscores or hyphens."
        )
    return state_dir(root) / "tasks" / (name + ".json")


def update_task(root, name, value, revision):
    policy.require_module(policy.load(root), "context")
    if not isinstance(value, dict) or any(
        k in value for k in ["revision", "worktree", "task"]
    ):
        raise Error("Task payload must be an object without reserved metadata fields.")
    path = task_path(root, name)
    with locked(path.with_suffix(".lock")):
        old = read_json(path) if path.exists() else {"revision": 0}
        if old["revision"] != revision:
            raise Error(
                f"Task revision conflict: expected {revision}, current {old['revision']}."
            )
        value = dict(value, revision=revision + 1, worktree=str(root), task=name)
        write_json(path, value)
    return value


def context(root, task=None, limit=12000):
    config = policy.load(root)
    policy.require_module(config, "context")
    if not 1000 <= limit <= 24000:
        raise Error("Context limit must be between 1000 and 24000 characters.")
    task_state = (
        read_json(task_path(root, task))
        if task and task_path(root, task).exists()
        else None
    )
    references = task_state.get("references", []) if task_state else []
    if not isinstance(references, list) or not all(
        isinstance(p, str) for p in references
    ):
        raise Error("Task references must be repository-relative document paths.")
    for name in references:
        policy.valid_path(name)
    if task_state:
        import json

        encoded = json.dumps(task_state)
        if len(encoded) > 4000:
            task_state = {
                "task": task,
                "revision": task_state["revision"],
                "preview": encoded[:3500],
                "truncated": True,
            }
    docs = []
    for name in policy.files(root):
        if policy.matches(name, config["architecture"]["documents"]):
            if task and name != ".aek/architecture.md" and name not in references:
                continue
            path = root / name
            if path.is_symlink():
                raise Error("Architecture documents must not be symlinks.")
            if path.is_file():
                docs.append({"path": name, "text": path.read_text(encoding="utf-8")})
    # Short architecture summary first, then detailed decision records.
    docs.sort(key=lambda x: (x["path"] != ".aek/architecture.md", x["path"]))
    remaining = max(0, limit - 2000 - (len(str(task_state)) if task_state else 0))
    selected = []
    for doc in docs:
        text = doc["text"][:remaining]
        selected.append(
            {
                "path": doc["path"],
                "text": text,
                "truncated": len(text) < len(doc["text"]),
            }
        )
        remaining -= len(text)
        if not remaining:
            break
    approval_path = state_dir(root) / "approval.json"
    approval = read_json(approval_path) if approval_path.exists() else None
    return {
        "commit": commit(root),
        "worktree": str(root),
        "architecture": selected,
        "task": task_state,
        "harness": {
            "proposal": approval["proposal"],
            "digest": digest(approval["snapshot"]),
            "status": "cached-reference-revalidate-before-verification",
        }
        if approval
        else None,
        "rules": [
            "Architecture boundary changes require human approval before implementation.",
            "Retrieve relevant source; inspect source references before trusting graph relationships.",
            "Launch parallel agents only when the user explicitly requests them.",
        ],
    }


def new_worktree(root, task, branch, ownership, authorized=False):
    policy.require_module(policy.load(root), "coordination")
    if not authorized:
        raise Error(
            "Parallel work requires explicit user authorization; pass --requested after that request."
        )
    if not ownership:
        raise Error("Declare interface/file ownership with --owns.")
    for item in ownership:
        policy.valid_path(item)
        scope = item[:-3] if item.endswith("/**") else item
        if any(c in scope for c in "*?["):
            raise Error("Ownership must be an exact path or a directory ending in /**.")
    common = Path(git(root, "rev-parse", "--git-common-dir").stdout.decode().strip())
    if not common.is_absolute():
        common = root / common
    registry = common.resolve() / "aek-coordination.json"
    with locked(registry.with_suffix(".lock")):
        tasks = read_json(registry) if registry.exists() else {}
        if task in tasks:
            raise Error("Task is already registered; resume its worktree instead.")
        for existing in tasks.values():
            for left in ownership:
                for right in existing["ownership"]:
                    a = left.removesuffix("/**").casefold().rstrip("/")
                    b = right.removesuffix("/**").casefold().rstrip("/")
                    if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                        raise Error(
                            f"Ownership overlaps another task: {left}. Resolve the interface explicitly."
                        )
        git(root, "check-ref-format", "--branch", branch)
        directory = state_dir(root) / "worktrees" / task
        task_path(root, task)  # validates task before using it as a directory name
        git(root, "worktree", "add", "-b", branch, str(directory), "HEAD")
        tasks[task] = {"path": str(directory), "branch": branch, "ownership": ownership}
        write_json(registry, tasks)
    update_task(directory, task, {"ownership": ownership, "status": "ready"}, 0)
    return tasks[task]
