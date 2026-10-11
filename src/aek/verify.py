from __future__ import annotations

import os
import signal
import shutil
import subprocess
import tempfile
import time

from .common import (
    Error,
    checkout,
    commit,
    digest,
    git,
    state_dir,
    write_json,
    environment,
    is_link,
)
from . import policy
from .harness import resolve


def execution_env():
    env = dict(os.environ)
    for name in list(env):
        if any(
            word in name.upper()
            for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "PRIVATE_KEY")
        ) or name.startswith("GIT_"):
            env.pop(name)
    env.update(
        CI="true",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        GIT_TERMINAL_PROMPT="0",
    )
    env.pop("PYTHONPATH", None)
    env.pop("NODE_OPTIONS", None)
    return env


def execute(root, checks):
    results = []
    for item in checks:
        start = time.monotonic()
        result = {
            "name": item["name"],
            "kind": item.get("kind", "custom"),
            "status": "error",
        }
        try:
            argv = policy.command(item)
            if os.name == "nt":
                argv[0] = shutil.which(argv[0]) or argv[0]
            cwd = (root / item.get("cwd", ".")).resolve()
            if cwd != root.resolve() and root.resolve() not in cwd.parents:
                raise Error("Check working directory escapes the disposable checkout.")
            result["argv"] = argv
            with tempfile.TemporaryFile() as log:
                env = execution_env()
                env["PYTHONPATH"] = os.pathsep.join([str(root / "src"), str(root)])
                process = subprocess.Popen(
                    argv,
                    cwd=cwd,
                    env=env,
                    stdout=log,
                    stderr=log,
                    start_new_session=os.name != "nt",
                )
                try:
                    code = process.wait(timeout=item.get("timeout", 300))
                    result.update(
                        status="passed" if code == 0 else "failed", returncode=code
                    )
                except subprocess.TimeoutExpired:
                    if os.name == "nt":
                        subprocess.run(
                            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                            capture_output=True,
                        )
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.kill()
                    process.wait()
                    result["status"] = "timeout"
                log.seek(0, 2)
                size = log.tell()
                log.seek(max(0, size - 12000))
                result["output"] = log.read().decode(errors="replace")
        except (OSError, Error) as exc:
            result["output"] = str(exc)
        result["seconds"] = round(time.monotonic() - start, 3)
        results.append(result)
    return results


def restore(root, source, config):
    wanted = policy.tree(root, source, config)
    existing = [p for p in policy.files(root) if policy.protected(p, config)]
    paths = sorted(set(existing) | set(wanted))
    for name in paths:
        path = root / name
        if is_link(path) or any(
            is_link(p) for p in path.parents if p != root and root in p.parents
        ):
            raise Error(f"Refusing unsafe harness restore: {name}")
        if name not in wanted:
            if path.exists():
                if not path.is_file():
                    raise Error(f"Cannot remove protected non-file: {name}")
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(git(root, "show", f"{source}:{name}").stdout)
        if os.name != "nt":
            path.chmod(0o755 if wanted[name]["mode"] == "100755" else 0o644)
    if paths:
        payload = b"".join(os.fsencode(":(literal)" + p) + b"\0" for p in paths)
        git(
            root,
            "add",
            "--all",
            "--force",
            "--pathspec-from-file=-",
            "--pathspec-file-nul",
            input=payload,
        )
        if os.name == "nt":
            for name, meta in wanted.items():
                git(
                    root,
                    "update-index",
                    "--chmod=" + ("+x" if meta["mode"] == "100755" else "-x"),
                    "--",
                    name,
                )


def verify(
    root,
    *,
    offline=False,
    proposal=None,
    approval=None,
    config=None,
    sha=None,
    authority=None,
    save=True,
):
    if approval is None:
        config, approval, authority = resolve(root, offline=offline, proposal=proposal)
    sha = sha or commit(root)
    expected = approval["snapshot"]["files"]
    actual = policy.tree(root, sha, config)
    changes = sorted(
        p for p in set(expected) | set(actual) if expected.get(p) != actual.get(p)
    )
    # Compare local bytes/index too, even though execution uses committed source.
    dirty = []
    if sha == commit(root):
        work = policy.working_tree(root, config)
        dirty = sorted(
            p for p in set(expected) | set(work) if expected.get(p) != work.get(p)
        )
        index = policy.index_tree(root, config)
        dirty += sorted(
            p for p in set(expected) | set(index) if expected.get(p) != index.get(p)
        )
    with checkout(root, sha) as target:
        restore(target, approval["snapshot"]["commit"], config)
        before = policy.working_tree(target, config)
        if before != expected:
            raise Error("Disposable checkout did not reproduce the approved harness.")
        results = execute(target, config["checks"])
        try:
            after = policy.working_tree(target, config)
            post_tampering = (
                after != expected or policy.index_tree(target, config) != expected
            )
        except Error:
            post_tampering = True
    required_names = {c["name"] for c in config["checks"]}
    completed = {c["name"] for c in results if c["status"] == "passed"}
    report = {
        "environment": environment(),
        "schema_version": 1,
        "commit": sha,
        "repository": config["github"]["repository"],
        "authority": authority,
        "proposal": approval["proposal"],
        "review_id": approval["review_id"],
        "harness_digest": digest(approval["snapshot"]),
        "policy_digest": digest(config),
        "tampered_paths": sorted(set(changes + dirty)),
        "post_execution_tampering": post_tampering,
        "checks": results,
        "architecture_review": [
            {
                "description": r["description"],
                "status": "executed" if r.get("check") else "requires-human-review",
            }
            for r in config["architecture"]["rules"]
        ],
        "passed": not changes
        and not dirty
        and not post_tampering
        and completed == required_names,
    }
    if save:
        write_json(state_dir(root) / "verification.json", report)
    return report
