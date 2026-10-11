from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .common import Error, atomic_write, read_json, root_at, state_dir, write_json
from . import policy


def initialize(args, root):
    from .github import repo_from_remote
    from .install import enroll_hooks, disable_hooks, SOURCE

    if args.disable:
        return disable_hooks(root)
    if not args.accept:
        repository = args.repository or repo_from_remote(root)
        candidate = policy.discover(root, repository, args.human_id)
        path = state_dir(root) / "enrollment-proposal.json"
        write_json(path, candidate)
        return {
            "proposal": str(path),
            "configuration": candidate,
            "enrolled": False,
            "next": "Review commands, protected paths, human IDs, agent identity, App ID and CI image; then aek init --accept PATH.",
        }
    config = policy.validate(read_json(args.accept))
    if not config["github"]["human_ids"]:
        raise Error("Enrollment requires at least one configured human account ID.")
    config_path = root / policy.CONFIG
    if config_path.exists():
        raise Error(
            "Project is already enrolled. Policy changes require a human-reviewed governance PR."
        )
    destinations = [config_path, root / ".aek/architecture.md"]
    if args.ci:
        destinations += [
            root / ".aek/ci",
            root / ".github/workflows/aek-controller.yml",
            root / ".github/workflows/aek-request.yml",
        ]
        for path in destinations[2:]:
            if path.exists():
                raise Error(
                    f"Refusing to overwrite existing CI runtime/workflow: {path}"
                )
    for path in destinations:
        if path.is_symlink() or any(
            p.is_symlink() for p in path.parents if p != root and root in p.parents
        ):
            raise Error(f"Enrollment destination uses a symlink: {path}")
    write_json(config_path, config)
    architecture = root / ".aek/architecture.md"
    if not architecture.exists():
        atomic_write(
            architecture,
            "# Architecture\n\nRecord reviewed module responsibilities, dependency boundaries, interfaces, and invariants here before feature work.\n",
        )
    if args.ci:
        # Controller uses the protected default-branch copy, never the feature copy.
        import shutil

        destination = root / ".aek/ci"
        if destination.exists():
            raise Error("Refusing to overwrite existing CI controller runtime.")
        shutil.copytree(
            SOURCE / "src" / "aek",
            destination / "aek",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        for name in ["aek-controller.yml", "aek-request.yml"]:
            path = root / ".github/workflows" / name
            if path.exists():
                raise Error(f"Refusing to replace workflow: {path}")
            atomic_write(path, (SOURCE / "templates" / name).read_bytes())
    hooks = enroll_hooks(root)
    return {
        "enrolled": True,
        "hooks": hooks,
        "configuration": str(config_path),
        "ci": "Bootstrap configuration/controller on the protected default branch with human credentials. Configure App secrets and branch protection before feature work.",
        "enforcement_complete": False,
    }


def parser():
    p = argparse.ArgumentParser(
        prog="aek",
        description="Approved harnesses and architecture context for coding agents.",
    )
    p.add_argument("--json", action="store_true", help="Emit machine-readable output")
    p.add_argument("--path", default=".", help="Project working tree")
    sub = p.add_subparsers(dest="action", required=True)
    for action in ["install", "update"]:
        command = sub.add_parser(action)
        command.add_argument(
            "--agent", choices=["codex", "antigravity", "both"], default="both"
        )
        command.add_argument(
            "--home", type=Path, help="Alternative installation home for testing"
        )
        command.add_argument(
            "--source",
            type=Path,
            help="Fresh checkout/bundle used for installation or upgrade",
        )
        command.add_argument(
            "--replace",
            action="store_true",
            help="Back up and replace colliding unmanaged files",
        )
        command.add_argument(
            "--migrate-legacy",
            action="store_true",
            help="Explicitly replace the older standalone global Harness Lock with enrollment-only protection",
        )
    command = sub.add_parser("uninstall")
    command.add_argument("--home", type=Path)
    command = sub.add_parser("init")
    command.add_argument("--repository")
    command.add_argument("--human-id", action="append", type=int)
    command.add_argument("--accept", type=Path)
    command.add_argument("--ci", action="store_true")
    command.add_argument("--disable", action="store_true")
    command = sub.add_parser("doctor")
    command.add_argument("--online", action="store_true")
    command = sub.add_parser("harness")
    actions = command.add_subparsers(dest="operation", required=True)
    author = actions.add_parser("workspace")
    author.add_argument("--task", required=True)
    author.add_argument("--branch", required=True)
    propose = actions.add_parser("propose")
    propose.add_argument("--branch")
    propose.add_argument("--publish", action="store_true")
    propose.add_argument("--expect-failure", action="append", default=[])
    freeze = actions.add_parser("freeze")
    freeze.add_argument("--proposal", type=int, required=True)
    freeze.add_argument("--feature-branch")
    command = sub.add_parser("verify")
    command.add_argument("--offline", action="store_true")
    command.add_argument("--proposal", type=int)
    command = sub.add_parser("context")
    command.add_argument("--task")
    command.add_argument("--limit", type=int, default=12000)
    command = sub.add_parser("task")
    actions = command.add_subparsers(dest="operation", required=True)
    show = actions.add_parser("show")
    show.add_argument("name")
    put = actions.add_parser("put")
    put.add_argument("name")
    put.add_argument("--input", type=Path, required=True)
    put.add_argument("--revision", type=int, required=True)
    command = sub.add_parser("coordinate")
    command.add_argument("--task", required=True)
    command.add_argument("--branch", required=True)
    command.add_argument("--owns", action="append", required=True)
    command.add_argument("--requested", action="store_true")
    command = sub.add_parser("graph")
    actions = command.add_subparsers(dest="operation", required=True)
    actions.add_parser("install")
    graph = actions.add_parser("refresh")
    graph.add_argument("--semantic", action="store_true")
    query = actions.add_parser("query")
    query.add_argument("question")
    query.add_argument("--budget", type=int, default=2000)
    command = sub.add_parser("review")
    command.add_argument("--summary", required=True)
    command.add_argument("--independent", action="store_true")
    command.add_argument("--requested", action="store_true")
    command = sub.add_parser("ship")
    command.add_argument("--title", required=True)
    command.add_argument("--review-summary")
    command = sub.add_parser("adapter", help=argparse.SUPPRESS)
    command.add_argument("name", choices=["codex", "antigravity"])
    command = sub.add_parser("git-hook", help=argparse.SUPPRESS)
    command.add_argument("event")
    command.add_argument("arguments", nargs=argparse.REMAINDER)
    return p


def dispatch(args):
    if args.action in ["install", "update", "uninstall"]:
        from .install import install, uninstall, migrate_legacy

        if args.action == "uninstall":
            return uninstall(args.home)
        adapters = ["codex", "antigravity"] if args.agent == "both" else [args.agent]
        result = install(adapters, args.home, args.replace, args.source)
        if args.migrate_legacy:
            result["legacy_migration"] = migrate_legacy(args.home)
        return result
    if args.action == "graph" and args.operation == "install":
        from .graph import install_graph

        return install_graph()
    if args.action == "doctor":
        from .release import doctor

        try:
            root = root_at(args.path)
        except Error:
            root = None
        return doctor(root, args.online)
    root = root_at(args.path)
    if args.action == "init":
        return initialize(args, root)
    if args.action == "harness":
        from .harness import propose, freeze, workspace

        if args.operation == "workspace":
            return workspace(root, args.task, args.branch)
        if args.operation == "propose":
            return propose(root, args.branch, args.expect_failure, publish=args.publish)
        return freeze(root, args.proposal, args.feature_branch)
    if args.action == "verify":
        from .verify import verify

        return verify(root, offline=args.offline, proposal=args.proposal)
    if args.action == "context":
        from .context import context

        return context(root, args.task, args.limit)
    if args.action == "task":
        from .context import task_path, update_task

        if args.operation == "show":
            return read_json(task_path(root, args.name))
        return update_task(root, args.name, read_json(args.input), args.revision)
    if args.action == "coordinate":
        from .context import new_worktree

        return new_worktree(root, args.task, args.branch, args.owns, args.requested)
    if args.action == "graph":
        from .graph import refresh, query

        if args.operation == "refresh":
            return refresh(root, args.semantic)
        return query(root, args.question, args.budget)
    if args.action in ["ship", "review"]:
        from .release import ship, review

        if args.action == "ship":
            return ship(root, args.title, args.review_summary)
        return review(root, args.summary, args.independent, args.requested)
    raise Error("Unknown command.")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.action == "adapter":
            from .adapters import adapter

            try:
                payload = json.load(sys.stdin)
            except ValueError:
                payload = {
                    "toolCall": {"name": "write_to_file", "args": {}},
                    "tool_name": "apply_patch",
                    "tool_input": {},
                }
            print(json.dumps(adapter(args.name, payload)))
            return 0
        if args.action == "git-hook":
            from .adapters import git_hook

            return git_hook(args.event, args.arguments)
        result = dispatch(args)
        if args.json:
            print(json.dumps(result, ensure_ascii=True))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        if result.get("passed") is False or result.get("enforcement_complete") is False:
            return 1
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        if args.json:
            print(json.dumps({"error": str(exc), "passed": False}))
        else:
            print(f"AEK: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
