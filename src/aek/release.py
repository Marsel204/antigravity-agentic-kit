from __future__ import annotations

import json
from pathlib import Path
import tempfile

from .common import Error, clean, commit, git, run, state_dir, write_json, evidence_text
from .github import GitHub, protection, transport
from . import policy
from .verify import verify


def installation_status():
    import sys
    import shutil
    from .install import data_home
    from .common import read_json

    runtime = data_home()
    record = runtime.parent / "aek-installation.json"
    manifest = read_json(record) if record.exists() else {}
    return {
        "runtime": str(runtime),
        "installed": bool(manifest),
        "entry_exists": (runtime / "scripts/aek.py").is_file(),
        "python": sys.version.split()[0],
        "git": shutil.which("git"),
        "configured_adapters": manifest.get("adapters", []),
        "activation": "Codex definitions require /hooks trust; Antigravity requires reload and live validation.",
    }


def doctor(root, online=False):
    installation = installation_status()
    if root is None or not (root / policy.CONFIG).is_file():
        return {
            "installation": installation,
            "enforcement_complete": False,
            "issues": [
                "No explicitly enrolled project at this path. Run aek init to propose enrollment."
            ],
        }
    config = policy.load(root)
    issues = []
    hooks = (
        git(root, "config", "--show-origin", "--get", "core.hooksPath", check=False)
        .stdout.decode()
        .strip()
    )
    effective = (
        git(root, "config", "--get", "core.hooksPath", check=False)
        .stdout.decode()
        .strip()
    )
    hooks_path = Path(effective)
    if not hooks_path.is_absolute():
        hooks_path = root / hooks_path
    script = hooks_path / "pre-commit"
    if not script.is_file() or "git-hook" not in script.read_text(errors="replace"):
        issues.append("AEK pre-commit hook is missing or overridden.")
    if not config["github"]["human_ids"]:
        issues.append("No human account IDs configured.")
    if not config["github"]["agent_login"]:
        issues.append("No restricted publishing identity configured.")
    if not config["github"]["check_app_id"]:
        issues.append("No dedicated verification App configured.")
    if not config["github"].get("verification_image"):
        issues.append("No digest-pinned CI toolchain image configured.")
    if not online:
        issues.append(
            "Remote identity and repository protection have not been checked."
        )
    else:
        try:
            GitHub().identity(config)
            protection(config)
        except Error as exc:
            issues.append(str(exc))
    return {
        "installation": installation,
        "enforcement_complete": not issues,
        "issues": issues,
        "effective_hooks": hooks,
        "adapter_activation": "Configured hooks need trust/reload and a live edit-denial check in the agent.",
        "credential_boundary": "Human and App credentials must be inaccessible to coding agents; token limits require administrator inspection.",
    }


def review(root, summary, independent=False, requested=False):
    policy.require_module(policy.load(root), "release")
    if independent and not requested:
        raise Error("Independent review requires explicitly requested agent work.")
    clean(root)
    value = {
        "commit": commit(root),
        "mode": "independent" if independent else "self-review",
        "summary": summary,
        "independent_requested": requested,
        "source": "local-review-record-not-an-approval",
    }
    write_json(state_dir(root) / "review.json", value)
    return value


def ship(root, title, review_summary=None):
    config = policy.load(root)
    policy.require_module(config, "release")
    clean(root)
    GitHub().identity(config)
    protection(config)
    branch = git(root, "branch", "--show-current").stdout.decode().strip()
    base = (
        config["github"].get("base_branch")
        or GitHub().repository(config)["default_branch"]
    )
    if not branch or branch == base:
        raise Error(
            "Ship from a feature branch, not a detached checkout or the default branch."
        )
    report = verify(root)  # Always rerun; local report files are never authorization.
    if not report["passed"] or report["authority"] != "github-verified":
        raise Error(
            "Current, independently approved local verification must pass before publishing."
        )
    if commit(root) != report["commit"]:
        raise Error("Commit changed during verification.")
    clean(root)
    if not review_summary:
        from .common import read_json

        record = read_json(state_dir(root) / "review.json")
        if record["commit"] != report["commit"] or not record.get("summary"):
            raise Error("Record a review for this exact commit before shipping.")
    else:
        record = review(root, review_summary)
    transport(root, config, "push", f"{report['commit']}:refs/heads/{branch}")
    body = (
        f"AEK-PROPOSAL: {report['proposal']}\n\nApproved test proposal: #{report['proposal']}\n\n"
        f"Review mode: {record['mode']}\n\n{record['summary']}\n\n"
        "Verification evidence (CI must independently validate the integration result):\n```json\n"
        + evidence_text(report)
        + "\n```\n"
    )
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "body.md"
        path.write_text(body, encoding="utf-8")
        existing = run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                config["github"]["repository"],
                "--head",
                branch,
                "--state",
                "open",
                "--json",
                "url,isDraft",
            ],
            check=True,
        )
        prs = json.loads(existing.stdout)
        if prs:
            if not prs[0]["isDraft"]:
                raise Error(
                    "Existing implementation PR is ready for review; do not change its state automatically."
                )
            url = prs[0]["url"]
            run(["gh", "pr", "edit", url, "--title", title, "--body-file", str(path)])
        else:
            url = (
                run(
                    [
                        "gh",
                        "pr",
                        "create",
                        "--repo",
                        config["github"]["repository"],
                        "--draft",
                        "--head",
                        branch,
                        "--base",
                        base,
                        "--title",
                        title,
                        "--body-file",
                        str(path),
                    ]
                )
                .stdout.decode()
                .strip()
            )
    return {
        "url": url,
        "commit": report["commit"],
        "ci_status": "awaiting-independent-verification",
        "draft": True,
        "merged": False,
        "deployed": False,
    }
