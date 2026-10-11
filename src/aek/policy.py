from __future__ import annotations

import fnmatch
import os
from pathlib import PurePosixPath
import re
import sys

from .common import Error, git, read_json, is_link

CONFIG = ".aek/project.json"
DEFAULT_PATTERNS = [
    "**/tests/**",
    "**/test/**",
    "**/fixtures/**",
    "**/__snapshots__/**",
    "**/*.spec.*",
    "**/*.test.*",
    "**/test_*.py",
    "**/*_test.py",
    "**/*_test.go",
]
GOVERNANCE = [
    "**/.gitattributes",
    CONFIG,
    ".aek/architecture.md",
    ".aek/decisions/**",
    ".aek/ci/**",
    ".aek/proposals/**",
    ".github/workflows/aek-controller.yml",
    ".github/workflows/aek-request.yml",
]


def valid_path(path):
    path = str(path).replace("\\", "/")
    parts = PurePosixPath(path).parts
    if (
        not path
        or path.startswith("/")
        or re.match(r"^[A-Za-z]:", path)
        or ".." in parts
        or ".git" in parts
    ):
        raise Error(f"Expected a repository-relative path: {path}")
    return path.removeprefix("./")


def matches(path, patterns):
    # '**/' also matches the root, unlike fnmatch's literal prefix.
    path = valid_path(path).casefold()
    for pattern in patterns:
        pattern = valid_path(pattern).casefold()
        if fnmatch.fnmatchcase(path, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]):
            return True
        if pattern.endswith("/**") and path == pattern[:-3]:
            return True
        if pattern.startswith("**/") and pattern.endswith("/**"):
            segment = pattern[3:-3]
            if segment in path.split("/"):
                return True
    return False


def protected(path, config):
    return matches(
        path,
        config["protected_paths"] + GOVERNANCE + config["architecture"]["documents"],
    )


def validate(config):
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise Error("Unsupported project configuration; expected schema_version 1.")
    for key in [
        "protected_paths",
        "checks",
        "github",
        "architecture",
        "graphify",
        "modules",
    ]:
        if key not in config:
            raise Error(f"Missing project setting: {key}")
    modules = config["modules"]
    if (
        not isinstance(modules, list)
        or "harness" not in modules
        or not all(
            isinstance(m, str)
            and m in {"harness", "context", "coordination", "release"}
            for m in modules
        )
    ):
        raise Error(
            "Modules must include harness and may include context, coordination, and release."
        )
    if "coordination" in modules and "context" not in modules:
        raise Error("The coordination module requires context for isolated task state.")
    for key in ["github", "architecture", "graphify"]:
        if not isinstance(config[key], dict):
            raise Error(f"{key} must be a configuration object.")
    if not isinstance(config["architecture"].get("documents"), list) or not isinstance(
        config["architecture"].get("rules"), list
    ):
        raise Error("Architecture documents and rules must be lists.")
    if not isinstance(config["protected_paths"], list) or not config["protected_paths"]:
        raise Error("At least one protected path is required.")
    artifacts = config.get("ignored_artifacts", [])
    if not isinstance(artifacts, list) or not all(
        isinstance(p, str) for p in artifacts
    ):
        raise Error(
            "ignored_artifacts must be a list of reviewed repository-relative patterns."
        )
    for p in artifacts:
        valid_path(p)
    for pattern in config["protected_paths"] + config["architecture"]["documents"]:
        if not isinstance(pattern, str):
            raise Error("Protected and architecture path patterns must be strings.")
        valid_path(pattern)
    checks = config["checks"]
    if (
        not isinstance(checks, list)
        or not checks
        or not all(isinstance(c, dict) for c in checks)
        or not any(c.get("kind") == "test" for c in checks)
    ):
        raise Error("Declare at least one required test check.")
    names = set()
    for item in checks:
        if not isinstance(item, dict) or not re.fullmatch(
            r"[a-zA-Z0-9_-]+", item.get("name", "")
        ):
            raise Error("Every check needs a unique alphanumeric name.")
        if item["name"] in names:
            raise Error("Duplicate check name.")
        names.add(item["name"])
        if item.get("required") is not True:
            raise Error(
                "Configured checks must be required; omit optional checks instead."
            )
        if (
            not isinstance(item.get("timeout", 300), int)
            or not 1 <= item.get("timeout", 300) <= 7200
        ):
            raise Error("Check timeouts must be between 1 and 7200 seconds.")
        commands = item.get("argv")
        values = commands.values() if isinstance(commands, dict) else [commands]
        for argv in values:
            if (
                not isinstance(argv, list)
                or not argv
                or not all(isinstance(x, str) and x for x in argv)
            ):
                raise Error(
                    "Check commands must be nonempty argument arrays, not shell strings."
                )
        valid_path(item.get("cwd", ".")) if item.get("cwd", ".") != "." else None
    gh = config["github"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", gh.get("repository", "")):
        raise Error("Configure github.repository as owner/repository.")
    ids = gh.get("human_ids", [])
    if not isinstance(ids, list) or not all(type(x) is int and x > 0 for x in ids):
        raise Error("github.human_ids must contain numeric GitHub account IDs.")
    for rule in config["architecture"]["rules"]:
        if not isinstance(rule, dict) or not rule.get("description"):
            raise Error(
                "Architecture rules need a description and optional check name."
            )
        if rule.get("check") and rule["check"] not in names:
            raise Error(
                "An executable architecture rule must reference a configured required check."
            )
    if config["graphify"].get("semantic") not in [False, True]:
        raise Error("graphify.semantic must be a boolean.")
    if type(config["graphify"].get("enabled")) is not bool:
        raise Error("graphify.enabled must be a boolean.")
    return config


def require_module(config, name):
    if name not in config["modules"]:
        raise Error(
            f"The {name} module is disabled in the reviewed project configuration."
        )


def load(root, ref=None):
    if ref:
        import json

        try:
            value = json.loads(git(root, "show", f"{ref}:{CONFIG}").stdout)
        except ValueError as exc:
            raise Error("Invalid committed project configuration.") from exc
    else:
        value = read_json(root / CONFIG)
    return validate(value)


def tree(root, ref, config):
    result = {}
    for record in git(root, "ls-tree", "-r", "-z", ref).stdout.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        name = os.fsdecode(raw_path)
        if protected(name, config):
            if mode not in ["100644", "100755"] or kind != "blob":
                raise Error(f"Protected symlinks/submodules are unsupported: {name}")
            result[name] = {
                "mode": mode,
                "sha256": __import__("hashlib")
                .sha256(git(root, "cat-file", "blob", blob).stdout)
                .hexdigest(),
            }
    return result


def files(root):
    return sorted(
        set(
            os.fsdecode(x)
            for x in git(
                root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"
            ).stdout.split(b"\0")
            if x
        )
    )


def index_tree(root, config):
    import hashlib

    result = {}
    for record in git(root, "ls-files", "--stage", "-z").stdout.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, blob, stage = meta.decode().split()
        name = os.fsdecode(raw_path)
        if not protected(name, config):
            continue
        if stage != "0" or mode not in ["100644", "100755"]:
            raise Error(f"Unmerged or unsafe protected index entry: {name}")
        result[name] = {
            "mode": mode,
            "sha256": hashlib.sha256(
                git(root, "cat-file", "blob", blob).stdout
            ).hexdigest(),
        }
    return result


def working_tree(root, config):
    import hashlib

    result = {}
    autocrlf = (
        git(root, "config", "--get", "core.autocrlf", check=False)
        .stdout.decode()
        .strip()
        .casefold()
    )
    text_eol = set()
    for record in git(root, "ls-files", "--eol", "-z").stdout.split(b"\0"):
        if not record:
            continue
        meta, name = record.split(b"\t", 1)
        info = meta.decode()
        if (
            info.startswith("i/lf ")
            and "w/crlf " in info
            and "attr/-text" not in info
            and (
                autocrlf == "true"
                or "attr/text" in info
                or "eol=crlf" in info
                or "eol=lf" in info
            )
        ):
            text_eol.add(os.fsdecode(name))
    candidates = files(root)
    # Include ignored files inside protected directories; dependencies elsewhere are excluded.
    for item in git(
        root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard"
    ).stdout.split(b"\0"):
        if (
            item
            and protected(os.fsdecode(item), config)
            and not matches(os.fsdecode(item), config.get("ignored_artifacts", []))
        ):
            candidates.append(os.fsdecode(item))
    for name in sorted(set(candidates)):
        if not protected(name, config):
            continue
        path = root / name
        if not path.exists() and not path.is_symlink():
            continue
        if is_link(path) or any(
            is_link(p) for p in path.parents if p != root and root in p.parents
        ):
            raise Error(f"Protected symlink/junction path: {name}")
        if not path.is_file():
            raise Error(f"Protected path is not a regular file: {name}")
        mode = "100755" if os.name != "nt" and path.stat().st_mode & 0o111 else "100644"
        if os.name == "nt":
            stage = git(root, "ls-files", "--stage", "--", name).stdout.decode()
            mode = stage.split(" ", 1)[0] if stage else "100644"
        content = path.read_bytes()
        if name in text_eol:
            # Git's declared text checkout conversion is portable; do not run clean filters.
            content = content.replace(b"\r\n", b"\n")
        result[name] = {
            "mode": mode,
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    return result


def command(check):
    argv = check["argv"]
    if isinstance(argv, dict):
        argv = argv.get(sys.platform, argv.get("default"))
        if not argv:
            raise Error(f"Check {check['name']} has no command for {sys.platform}.")
    return [sys.executable if x == "{python}" else x for x in argv]


def discover(root, repository, human_ids=None):
    checks, runner_paths, profiles = [], [], []

    def add(name, argv, kind="test"):
        checks.append(
            {"name": name, "kind": kind, "argv": argv, "timeout": 300, "required": True}
        )

    python_tests = (
        list(root.glob("test*.py"))
        + list((root / "tests").glob("**/*.py"))
        + list((root / "test").glob("**/*.py"))
    )
    if (
        (root / "pyproject.toml").exists()
        or (root / "pytest.ini").exists()
        or python_tests
    ):
        profiles.append("python")
        add("python-tests", ["{python}", "-m", "pytest"])
        runner_paths += [
            "pyproject.toml",
            "pytest.ini",
            "conftest.py",
            "**/conftest.py",
            "setup.cfg",
            "tox.ini",
        ]
    if (root / "package.json").exists():
        package = read_json(root / "package.json")
        scripts = package.get("scripts", {})
        profiles.append("javascript")
        runner_paths += [
            "package.json",
            "*lock*",
            "**/*vitest*",
            "**/*jest*",
            "**/*playwright*",
            "tsconfig*.json",
        ]
        runner = (
            "pnpm"
            if (root / "pnpm-lock.yaml").exists()
            else "yarn"
            if (root / "yarn.lock").exists()
            else "npm"
        )
        if "test" in scripts:
            add("js-tests", [runner, "test"])
        for name, kind in [
            ("build", "build"),
            ("typecheck", "typecheck"),
            ("test:e2e", "e2e"),
        ]:
            if name in scripts:
                add(name.replace(":", "-"), [runner, "run", name], kind)
    if (root / "go.mod").exists():
        profiles.append("go")
        add("go-tests", ["go", "test", "./..."])
        add("go-build", ["go", "build", "./..."], "build")
        runner_paths += ["go.mod", "go.sum", "**/testdata/**"]
    if (root / "Cargo.toml").exists():
        profiles.append("rust")
        add("rust-tests", ["cargo", "test", "--locked"])
        add("rust-build", ["cargo", "check", "--locked"], "build")
        runner_paths += ["**/Cargo.toml", "Cargo.lock", ".cargo/**", "rust-toolchain*"]
        # Inline Rust test modules share files with implementation. Propose whole-file
        # protection; the owner can move them to integration files before enrollment.
        for path in root.glob("**/*.rs"):
            if any(
                part in {"target", ".git", "vendor"}
                for part in path.relative_to(root).parts
            ):
                continue
            if (
                path.is_file()
                and not path.is_symlink()
                and re.search(
                    r"#\s*\[\s*(?:test\s*\]|cfg\s*\(\s*test\s*\))",
                    path.read_text(encoding="utf-8", errors="replace"),
                )
            ):
                runner_paths.append(path.relative_to(root).as_posix())
    return {
        "schema_version": 1,
        "profiles": profiles or ["custom"],
        "modules": ["harness", "context", "coordination", "release"],
        "protected_paths": DEFAULT_PATTERNS + runner_paths,
        "ignored_artifacts": [
            "**/node_modules/**",
            "**/.venv/**",
            "**/venv/**",
            "target/**",
            "dist/**",
            "build/**",
            "**/__pycache__/**",
            "**/.pytest_cache/**",
        ],
        "checks": checks,
        "github": {
            "repository": repository,
            "human_ids": human_ids or [],
            "agent_login": "",
            "check_app_id": 0,
            "base_branch": "",
            "test_proposal": 0,
            "verification_image": "",
        },
        "architecture": {
            "documents": [".aek/architecture.md", ".aek/decisions/**"],
            "rules": [],
        },
        "graphify": {"enabled": False, "semantic": False, "backend": ""},
    }
