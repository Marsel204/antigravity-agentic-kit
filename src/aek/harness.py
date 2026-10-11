from __future__ import annotations

import os
from pathlib import Path
import re

from .common import (
    Error,
    checkout,
    clean,
    commit,
    digest,
    git,
    state_dir,
    write_json,
    read_json,
    evidence_text,
)
from . import policy
from .github import GitHub, fetch, transport


def workspace(root, task, branch):
    from .context import task_path
    from .install import enroll_hooks

    task_path(root, task)
    config = policy.load(root)
    base_ref = fetch(root, config)
    git(root, "check-ref-format", "--branch", branch)
    destination = state_dir(root) / "test-proposals" / task
    if destination.exists():
        raise Error("Proposal workspace already exists; resume it instead.")
    from .common import run

    run(["git", "clone", "--quiet", "--no-hardlinks", str(root), str(destination)])
    git(
        destination,
        "remote",
        "set-url",
        "origin",
        git(root, "remote", "get-url", "origin").stdout.decode().strip(),
    )
    git(destination, "switch", "-c", branch, commit(root, base_ref))
    for key in ["user.name", "user.email"]:
        setting = git(root, "config", "--get", key, check=False).stdout.decode().strip()
        if setting:
            git(destination, "config", "--local", key, setting)
    git(destination, "config", "--local", "aek.proposalWorkspace", "true")
    git(
        destination, "config", "--local", "aek.proposalRoot", str(destination.resolve())
    )
    enroll_hooks(destination)
    baseline = commit(root, base_ref)
    record = ".aek/proposals/" + task + ".json"
    write_json(
        destination / record,
        {
            "schema_version": 1,
            "task": task,
            "baseline": baseline,
            "role": "test-proposal",
        },
    )
    git(destination, "add", "--", record)
    from .verify import execution_env

    run(
        [
            "git",
            "-C",
            destination,
            "commit",
            "--quiet",
            "-m",
            "test: record harness proposal baseline",
        ],
        env=dict(execution_env(), ALLOW_TEST_EDITS="1"),
    )
    return {
        "workspace": str(destination),
        "branch": branch,
        "role": "test-authoring",
        "authority": "none; local authoring permission is not human approval",
    }


def snapshot(root, sha, config):
    return {
        "commit": sha,
        "policy_digest": digest(config),
        "files": policy.tree(root, sha, config),
    }


def validate_change(trusted, proposed):
    if not set(proposed.get("ignored_artifacts", [])) <= set(
        trusted.get("ignored_artifacts", [])
    ):
        raise Error(
            "Widening ignored artifact exclusions requires administrator-managed policy enrollment."
        )
    for key in [
        "repository",
        "human_ids",
        "agent_login",
        "check_app_id",
        "base_branch",
    ]:
        if proposed["github"].get(key) != trusted["github"].get(key):
            raise Error(
                "Security identity/protection settings require administrator-managed governance, not a test proposal."
            )
    if not set(trusted["protected_paths"]) <= set(proposed["protected_paths"]):
        raise Error(
            "A test proposal may extend protection, but must not remove existing protected patterns."
        )
    if not set(trusted["architecture"]["documents"]) <= set(
        proposed["architecture"]["documents"]
    ):
        raise Error("A proposal must retain existing architecture document protection.")


def marker(root, sha, base, config):
    harness = snapshot(root, sha, config)
    return f"AEK-HARNESS {digest(harness)} base={base} candidate={sha}"


def audit(root, base, sha, config):
    # Audit is evidence for a human reviewer, never authorization.
    diff = git(
        root, "diff", "--no-ext-diff", "--no-renames", "--unified=3", base, sha
    ).stdout.decode(errors="replace")
    flags = []
    for line in diff.splitlines():
        if (
            line.startswith("-")
            and not line.startswith("---")
            and re.search(r"assert|expect\(|check\(|require\(", line)
        ):
            flags.append({"kind": "removed-assertion", "line": line[:300]})
        if line.startswith("+") and re.search(
            r"skip|xfail|\.only\(|\.only\b|ignore|exclude|pass\b", line
        ):
            flags.append({"kind": "possible-weakening", "line": line[:300]})
    return {
        "flags": flags,
        "changed_paths": [
            os.fsdecode(x)
            for x in git(
                root, "diff", "--name-only", "--no-renames", "-z", base, sha
            ).stdout.split(b"\0")
            if x
        ],
        "requires_human_review": True,
    }


def approved(root, config, proposal, base_sha, github=None):
    github = github or GitHub()
    repo = config["github"]["repository"]
    pr = github.api(f"repos/{repo}/pulls/{int(proposal)}")
    if pr.get("state") != "open" or pr.get("merged"):
        raise Error(
            "Harness proposal must remain open and unmerged until the feature is merged."
        )
    if pr["base"]["repo"]["full_name"].casefold() != repo.casefold():
        raise Error("Proposal targets a different repository.")
    if pr["base"]["ref"] != (
        config["github"].get("base_branch")
        or github.repository(config)["default_branch"]
    ):
        raise Error("Proposal targets a different base branch.")
    sha = commit(root, pr["head"]["sha"])
    ancestor = git(root, "merge-base", base_sha, sha).stdout.decode().strip()
    # Branch may precede source-only base changes; protected changes must be reconciled.
    if policy.tree(root, ancestor, config) != policy.tree(root, base_sha, config):
        raise Error(
            "Target-branch harness changed since the proposal. Reconcile and reapprove."
        )
    proposal_config = policy.load(root, sha)
    validate_change(config, proposal_config)
    changed = [
        os.fsdecode(x)
        for x in git(
            root, "diff", "--name-only", "--no-renames", "-z", ancestor, sha
        ).stdout.split(b"\0")
        if x
    ]
    if any(not policy.protected(name, proposal_config) for name in changed):
        raise Error(
            "Harness proposal contains implementation files; use a test-only proposal."
        )
    expected = marker(root, sha, ancestor, proposal_config)
    reviews = github.pages(f"repos/{repo}/pulls/{int(proposal)}/reviews")
    # A later non-approval from the same person supersedes an earlier approval.
    latest = {}
    for review in reviews:
        if review.get("state") != "COMMENTED":
            latest[review["user"]["id"]] = review
    for ident, review in latest.items():
        if (
            ident in config["github"]["human_ids"]
            and review.get("state") == "CHANGES_REQUESTED"
        ):
            raise Error("A configured human reviewer requested changes.")
    valid = [
        r
        for ident, r in latest.items()
        if ident in config["github"]["human_ids"]
        and r["user"].get("type") == "User"
        and r["state"] == "APPROVED"
        and r.get("commit_id") == sha
        and expected in r.get("body", "").splitlines()
    ]
    if not valid:
        raise Error(
            "No current human review approves the exact harness marker and proposal commit."
        )
    return {
        "schema_version": 1,
        "repository": repo,
        "proposal": int(proposal),
        "base": ancestor,
        "snapshot": snapshot(root, sha, proposal_config),
        "config": proposal_config,
        "base_policy_digest": digest(config),
        "review_id": valid[-1]["id"],
        "reviewer_id": valid[-1]["user"]["id"],
        "marker": expected,
    }


def propose(root, branch, expected, *, publish=False):
    from .verify import execute

    config = policy.load(root)
    clean(root)
    base_ref = fetch(root, config)
    head, base = commit(root), commit(root, base_ref)
    validate_change(policy.load(root, base_ref), config)
    ancestor = git(root, "merge-base", head, base).stdout.decode().strip()
    if policy.tree(root, ancestor, config) != policy.tree(root, base, config):
        raise Error("Reconcile the target-branch harness before proposing tests.")
    changed = audit(root, ancestor, head, config)
    if any(not policy.protected(p, config) for p in changed["changed_paths"]):
        raise Error(
            "Commit only protected test/architecture files on the proposal branch."
        )
    test_names = {c["name"] for c in config["checks"] if c.get("kind") == "test"}
    if not set(expected) <= test_names:
        raise Error("--expect-failure must name configured test checks.")
    with checkout(root, head) as target:
        # Test-only diff means candidate sources already are pre-feature code.
        results = execute(
            target, [c for c in config["checks"] if c.get("kind") == "test"]
        )
        if policy.working_tree(target, config) != policy.tree(root, head, config):
            raise Error("Test execution changed the proposed harness.")
    for result in results:
        if result["name"] in expected:
            if result["status"] != "failed" or result.get("returncode") is None:
                raise Error(
                    f"Expected a test failure, not a runner error: {result['name']}"
                )
            output = result.get("output", "")
            requirement_compile_failure = bool(
                re.search(r"error\[E(?:0425|0599|0609)\]", output)
            )
            if requirement_compile_failure:
                changed["flags"].append(
                    {
                        "kind": "planned-api-compile-failure-needs-human-review",
                        "check": result["name"],
                    }
                )
            if (
                re.search(
                    r"No module named|command not found|not recognized|no tests (ran|collected)|usage: pytest|could not compile",
                    output,
                    re.I,
                )
                and not requirement_compile_failure
            ):
                raise Error(
                    f"Probable setup/collection failure in {result['name']}; inspect it before approval."
                )
        elif result["status"] != "passed":
            raise Error(f"Unexpected failure in {result['name']}.")
    value = {
        "snapshot": snapshot(root, head, config),
        "base": ancestor,
        "approval_marker": marker(root, head, ancestor, config),
        "audit": changed,
        "checks": results,
        "expected_failures": sorted(set(expected)),
        "runner_configuration": config["checks"],
    }
    write_json(state_dir(root) / "proposal.json", value)
    if publish:
        GitHub().identity(config)
        if not branch:
            raise Error("--branch is required when publishing a proposal.")
        git(root, "check-ref-format", "--branch", branch)
        transport(root, config, "push", f"{head}:refs/heads/{branch}")
        import tempfile

        body = (
            "Test-only proposal. Review assertions, fixtures and expected failures.\n\n"
            "To approve this harness, include this exact line in an APPROVE review:\n\n"
            f"{value['approval_marker']}\n\nAudit and test evidence:\n```json\n"
            + evidence_text(
                {
                    "snapshot_commit": head,
                    "baseline": ancestor,
                    "protected_file_count": len(value["snapshot"]["files"]),
                    "snapshot_digest": digest(value["snapshot"]),
                    "expected_failures": value["expected_failures"],
                    "runner_configuration": config["checks"],
                    "audit": changed,
                    "checks": results,
                }
            )
            + f"\n```\n\nComplete snapshot: https://github.com/{config['github']['repository']}/tree/{head}\n"
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "body.md"
            path.write_text(body, encoding="utf-8")
            from .common import run

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
                        config["github"].get("base_branch")
                        or GitHub().repository(config)["default_branch"],
                        "--title",
                        "test: propose approved feature harness",
                        "--body-file",
                        str(path),
                    ]
                )
                .stdout.decode()
                .strip()
            )
            value["url"] = url
    return value


def freeze(root, proposal, feature_branch=None):
    config = policy.load(root)
    clean(root)
    base_ref = fetch(root, config, proposal)
    # Trusted policy comes from the destination, not the candidate branch.
    trusted = policy.load(root, base_ref)
    value = approved(root, trusted, proposal, commit(root, base_ref))
    if digest(config) != digest(value["config"]):
        raise Error("Local policy differs from the human-approved proposal policy.")
    if feature_branch:
        git(root, "check-ref-format", "--branch", feature_branch)
        git(root, "switch", "-c", feature_branch, value["snapshot"]["commit"])
    git(root, "config", "--local", "--unset-all", "aek.proposalWorkspace", check=False)
    git(root, "config", "--local", "--unset-all", "aek.proposalRoot", check=False)
    write_json(state_dir(root) / "approval.json", value)
    return value


def resolve(root, *, offline=False, proposal=None):
    local = policy.load(root)
    cached = state_dir(root) / "approval.json"
    if offline:
        value = read_json(cached)
        if value.get("repository") != local["github"]["repository"]:
            raise Error("Cached snapshot belongs to another repository.")
        snap = snapshot(root, value["snapshot"]["commit"], local)
        if snap != value["snapshot"]:
            raise Error("Cached snapshot or current policy changed.")
        return local, value, "cached-untrusted"
    if proposal is None:
        proposal = (
            read_json(cached)["proposal"]
            if cached.exists()
            else local["github"].get("test_proposal")
        )
    if not proposal:
        raise Error("Freeze an approved test proposal first, or specify --proposal.")
    base_ref = fetch(root, local, proposal)
    trusted = policy.load(root, base_ref)
    value = approved(root, trusted, proposal, commit(root, base_ref))
    if digest(local) != digest(value["config"]):
        raise Error("Local project policy differs from human-approved policy.")
    write_json(cached, value)
    return value["config"], value, "github-verified"
