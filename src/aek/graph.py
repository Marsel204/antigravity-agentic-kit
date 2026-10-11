from __future__ import annotations

import hashlib
import os
from pathlib import Path
import venv

from .common import (
    Error,
    commit,
    digest,
    git,
    locked,
    read_json,
    run,
    state_dir,
    write_json,
)
from . import policy
from .install import data_home

VERSION = "0.9.85"


def executable(home=None):
    directory = data_home(home) / "graphify-env"
    return directory / ("Scripts/graphify.exe" if os.name == "nt" else "bin/graphify")


def install_graph(home=None):
    directory = executable(home).parents[1]
    venv.EnvBuilder(with_pip=True).create(directory)
    python = directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(
        [
            python,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            f"graphifyy=={VERSION}",
        ],
        timeout=600,
    )
    return {
        "graphify_version": VERSION,
        "executable": str(executable(home)),
        "semantic_enabled": False,
    }


def provenance(root):
    items = []
    names = set(policy.files(root))
    ignored = {
        os.fsdecode(p)
        for p in git(
            root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard"
        ).stdout.split(b"\0")
        if p
    }
    overrides = [
        root / name for name in names | ignored if name.endswith(".graphifyignore")
    ]
    names.update(name for name in ignored if name.endswith(".graphifyignore"))
    if any(
        any(
            line.lstrip().startswith("!")
            for line in p.read_text(encoding="utf-8").splitlines()
        )
        for p in overrides
        if p.is_file()
    ):
        # Explicit ignore overrides can include otherwise ignored source. Be conservative
        # rather than labeling an index current after those inputs change.
        names.update(ignored)
    exclude = Path(
        os.fsdecode(git(root, "rev-parse", "--git-path", "info/exclude").stdout).strip()
    )
    if not exclude.is_absolute():
        exclude = root / exclude
    items.append(
        (
            ".git/info/exclude",
            hashlib.sha256(exclude.read_bytes()).hexdigest()
            if exclude.is_file()
            else None,
        )
    )
    for name in sorted(names):
        path = root / name
        if path.is_symlink():
            target = path.resolve()
            target_hash = (
                hashlib.sha256(target.read_bytes()).hexdigest()
                if target.is_relative_to(root) and target.is_file()
                else None
            )
            items.append((name, "symlink", os.readlink(path), target_hash))
            continue
        if path.is_file():
            items.append((name, hashlib.sha256(path.read_bytes()).hexdigest()))
    return {
        "repository": policy.load(root)["github"]["repository"],
        "commit": commit(root),
        "worktree": str(root),
        "fingerprint": digest(items),
        "version": VERSION,
    }


def check_version(binary):
    if not binary.exists():
        raise Error("Graphify is optional and not installed. Run aek graph install.")
    text = run([binary, "--version"]).stdout.decode().strip()
    if VERSION not in text.split():
        raise Error(f"Expected Graphify {VERSION}, found {text}.")


def refresh(root, semantic=False):
    config = policy.load(root)
    if not config["graphify"]["enabled"]:
        raise Error("Enable Graphify in the reviewed project configuration first.")
    if semantic and not config["graphify"]["semantic"]:
        raise Error("External semantic extraction needs explicit project opt-in.")
    if semantic:
        from .harness import resolve

        config, _, authority = resolve(root)
        if authority != "github-verified" or not config["graphify"]["semantic"]:
            raise Error(
                "Semantic extraction requires a live human-approved project opt-in."
            )
    binary = executable()
    check_version(binary)
    folder = state_dir(root) / "graph"
    with locked(folder.with_suffix(".lock"), timeout=1):
        before = provenance(root)
        argv = [
            binary,
            "extract",
            str(root),
            "--out",
            str(folder),
            "--max-workers",
            "1",
        ]
        env = dict(os.environ)
        if semantic:
            backend = config["graphify"]["backend"]
            if not backend:
                raise Error(
                    "Select an explicit semantic backend; do not infer it from available API keys."
                )
            argv += ["--backend", backend]
        else:
            argv += ["--code-only"]
            for name in list(env):
                if name.endswith("_API_KEY") or name in [
                    "GOOGLE_API_KEY",
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                ]:
                    env.pop(name)
        result = run(argv, cwd=root, env=env, timeout=600)
        if before != provenance(root):
            raise Error("Source changed during extraction; refresh again.")
        graph = folder / "graphify-out" / "graph.json"
        if not graph.exists():
            raise Error("Graphify did not produce graph.json.")
        parsed = read_json(graph)
        if not parsed.get("nodes"):
            raise Error(
                "Graphify produced no code nodes; inspect supported inputs and extraction failures."
            )
        metadata = dict(
            before,
            semantic=semantic,
            graph_sha256=hashlib.sha256(graph.read_bytes()).hexdigest(),
        )
        write_json(folder / "provenance.json", metadata)
    return {
        "provenance": metadata,
        "summary": result.stdout.decode(errors="replace")[-4000:],
    }


def query(root, question, budget=2000):
    folder = state_dir(root) / "graph"
    metadata = read_json(folder / "provenance.json")
    if any(metadata.get(k) != v for k, v in provenance(root).items()):
        raise Error("Graph index is stale for this worktree; run aek graph refresh.")
    graph = folder / "graphify-out" / "graph.json"
    if metadata.get("graph_sha256") != hashlib.sha256(graph.read_bytes()).hexdigest():
        raise Error("Graph index changed without extraction provenance.")
    binary = executable()
    check_version(binary)
    result = run(
        [binary, "query", question, "--budget", str(budget), "--graph", str(graph)],
        cwd=root,
    )
    if any(metadata.get(k) != v for k, v in provenance(root).items()):
        raise Error(
            "Source changed during the graph query; refresh before relying on its evidence."
        )
    return {
        "evidence": result.stdout.decode(errors="replace"),
        "provenance": metadata,
        "instruction": "Inspect cited source before relying on these relationships.",
    }
