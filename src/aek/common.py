from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import stat
import tempfile
import time


class Error(Exception):
    pass


def is_link(path):
    path = Path(path)
    if path.is_symlink():
        return True
    try:
        attrs = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except FileNotFoundError:
        return False


def run(argv, cwd=None, *, check=True, env=None, timeout=120, input=None):
    try:
        result = subprocess.run(
            [str(x) for x in argv],
            cwd=cwd,
            env=env,
            input=input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise Error(f"{argv[0]} timed out after {timeout} seconds.") from exc
    except OSError as exc:
        raise Error(f"Cannot run {argv[0]}: {exc}") from exc
    if check and result.returncode:
        # Do not echo command arguments: they might contain credentials.
        raise Error(
            f"{argv[0]} failed ({result.returncode}): "
            f"{result.stderr.decode(errors='replace')[-3000:]}"
        )
    return result


def git(root, *args, **kwargs):
    # Explicit repository prevents inherited hook/parent Git env selecting another checkout.
    env = dict(os.environ)
    isolated = kwargs.pop("isolated", False)
    for key in tuple(env):
        if key.startswith("GIT_") and key not in {
            "GIT_SSH",
            "GIT_SSH_COMMAND",
            "GIT_ASKPASS",
        }:
            env.pop(key)
        elif any(
            word in key.upper()
            for word in ["TOKEN", "SECRET", "PASSWORD", "API_KEY", "PRIVATE_KEY"]
        ):
            env.pop(key)
    if isolated:
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        env["GIT_CONFIG_NOSYSTEM"] = "1"
    return run(["git", "-C", root, *args], env=env, **kwargs)


def root_at(path="."):
    result = run(["git", "-C", path, "rev-parse", "--show-toplevel"], check=False)
    if result.returncode:
        raise Error("Run this command inside a Git working tree.")
    root = Path(os.fsdecode(result.stdout).strip()).resolve()
    if root == Path.home().resolve():
        raise Error(
            "Refusing to enroll or operate on your home directory as a project."
        )
    return root


def commit(root, ref="HEAD"):
    return (
        git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
        .stdout.decode()
        .strip()
    )


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def environment():
    import platform

    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "git": run(["git", "--version"]).stdout.decode().strip(),
    }


def evidence_text(value, limit=50000):
    rendered = json.dumps(value, indent=2)
    if len(rendered) > limit:
        return (
            rendered[:limit]
            + "\n[Evidence preview truncated; inspect the exact commits and complete local/CI report.]"
        )
    return rendered


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Error(f"Cannot read JSON at {path}: {exc}") from exc


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise Error(f"Refusing symlink destination: {path}")
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write(content if isinstance(content, bytes) else content.encode())
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def write_json(path, value):
    atomic_write(path, json.dumps(value, indent=2, ensure_ascii=True) + "\n")


def state_dir(root):
    # Worktree-local Git dir, not the shared common dir.
    path = git(root, "rev-parse", "--absolute-git-dir").stdout.decode().strip()
    result = Path(path) / "aek"
    result.mkdir(parents=True, exist_ok=True)
    return result


def clean(root):
    if git(root, "status", "--porcelain", "-z", "--untracked-files=all").stdout:
        raise Error("A clean committed working tree is required for this operation.")


@contextlib.contextmanager
def locked(path, timeout=10):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise Error(
                    f"Concurrent update or stale lock: {path}. Inspect before removing it."
                )
            time.sleep(0.05)
    try:
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


@contextlib.contextmanager
def checkout(root, sha):
    # Clone, rather than a linked worktree: candidate code cannot change the user's index/refs.
    with tempfile.TemporaryDirectory(prefix="aek-verify-") as folder:
        target = Path(folder) / "repo"
        env = dict(os.environ)
        for key in tuple(env):
            if key.startswith("GIT_") or any(
                word in key.upper()
                for word in ["TOKEN", "SECRET", "PASSWORD", "API_KEY", "PRIVATE_KEY"]
            ):
                env.pop(key)
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        run(
            [
                "git",
                "clone",
                "--quiet",
                "--no-hardlinks",
                "--no-checkout",
                str(root),
                str(target),
            ],
            env=env,
        )
        git(target, "config", "core.hooksPath", str(Path(folder) / "no-hooks"))
        git(
            target,
            "-c",
            "core.autocrlf=false",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "filter.lfs.process=",
            "-c",
            "filter.lfs.smudge=",
            "-c",
            "filter.lfs.required=false",
            "checkout",
            "--quiet",
            "--detach",
            sha,
            isolated=True,
        )
        yield target
