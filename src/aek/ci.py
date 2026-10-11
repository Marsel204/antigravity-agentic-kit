"""Trusted CI controller. Invoke only from the protected default-branch runtime.

prepare/publish inspect data. execute runs candidate commands only in Docker,
with no Docker socket, host credentials, or controller runtime mounted.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import re
import time
import uuid
from urllib.parse import quote

from .common import (
    Error,
    checkout,
    commit,
    digest,
    git,
    read_json,
    run,
    write_json,
    environment,
)
from .github import GitHub, fetch, protection, transport
from .harness import approved
from . import policy
from .verify import restore


def proposal_number(pr):
    found = re.search(r"^AEK-PROPOSAL: ([1-9][0-9]*)$", pr.get("body") or "", re.M)
    return int(found.group(1)) if found else None


def invalidate(github, config, sha, reason):
    """Replace this App's previous success before doing fallible preparation."""
    repo = config["github"]["repository"]
    runs = github.api(
        f"repos/{repo}/commits/{sha}/check-runs?check_name=aek%2Fverification&filter=latest&per_page=100"
    )
    owned = [
        r
        for r in runs.get("check_runs", [])
        if r["name"] == "aek/verification"
        and r["app"]["id"] == config["github"]["check_app_id"]
    ]
    body = {
        "name": "aek/verification",
        "status": "completed",
        "conclusion": "failure",
        "external_id": uuid.uuid4().hex,
        "output": {"title": "Verification requires revalidation", "summary": reason},
    }
    if owned:
        ident = owned[-1]["id"]
        github.api(f"repos/{repo}/check-runs/{ident}", "PATCH", body)
        return {"id": ident, "epoch": body["external_id"]}
    body["head_sha"] = sha
    return {
        "id": github.api(f"repos/{repo}/check-runs", "POST", body)["id"],
        "epoch": body["external_id"],
    }


def prepare(root, event, candidate_pr=None, proposal=None):
    config = policy.load(root)
    github = GitHub()
    protection(config, github)
    repo = config["github"]["repository"]
    if event.get("repository", {}).get("full_name", "").casefold() != repo.casefold():
        raise Error("Request repository differs from trusted controller repository.")
    workflow = event.get("workflow_run")
    if workflow:
        if workflow.get("name") != "AEK request" or workflow.get("event") not in [
            "pull_request",
            "pull_request_review",
        ]:
            raise Error("Unexpected originating workflow.")
        matches = workflow.get("pull_requests", [])
        if not matches:
            matches = github.pages(f"repos/{repo}/commits/{workflow['head_sha']}/pulls")
        if len(matches) > 1 and workflow.get("head_branch"):
            matches = [
                p
                for p in matches
                if p.get("head", {}).get("ref") == workflow["head_branch"]
            ]
        if len(matches) != 1:
            raise Error("Cannot identify one candidate PR from the request.")
        candidate_pr = matches[0]["number"]
    candidate_pr = int(candidate_pr or event.get("inputs", {}).get("candidate_pr", 0))
    if not candidate_pr:
        raise Error("A candidate pull request is required.")
    pr = github.api(f"repos/{repo}/pulls/{candidate_pr}")
    if pr["base"]["repo"]["full_name"].casefold() != repo.casefold():
        raise Error("Request targets a different repository.")
    check_id = invalidate(
        github,
        config,
        pr["head"]["sha"],
        "New verification request. No prior success remains valid while preparation or execution is incomplete.",
    )
    # Review/branch changes on a test proposal invalidate every dependent open PR.
    # No candidate code runs for these events; push the feature or dispatch again.
    followers = [
        p
        for p in github.pages(f"repos/{repo}/pulls?state=open")
        if p.get("number") != candidate_pr and proposal_number(p) == candidate_pr
    ]
    if followers:
        for follower in followers:
            invalidate(
                github,
                config,
                follower["head"]["sha"],
                "Referenced proposal or review changed. Request fresh verification of this implementation PR.",
            )
        raise Error(
            "Dependent implementation checks invalidated; request fresh verification on each feature PR."
        )
    if (
        workflow
        and workflow["event"] == "pull_request_review"
        and not proposal_number(pr)
    ):
        raise Error(
            "No implementation PR references this proposal; approval is checked when an implementation requests verification."
        )
    if (
        pr["state"] != "open"
        or pr["base"]["repo"]["full_name"].casefold() != repo.casefold()
    ):
        raise Error("Candidate PR is not open against the configured repository.")
    # The event is only a request: always independently resolve the current head.
    proposal = int(proposal or event.get("inputs", {}).get("proposal_pr", 0) or 0)
    if not proposal:
        proposal = proposal_number(pr)
        if not proposal:
            raise Error(
                "Candidate PR must reference an approved proposal with AEK-PROPOSAL: NUMBER."
            )
    base_ref = fetch(root, config, proposal)
    if digest(policy.load(root, base_ref)) != digest(config):
        raise Error(
            "Controller policy is stale; rerun with current trusted default-branch code."
        )
    expected_branch = (
        config["github"].get("base_branch")
        or github.repository(config)["default_branch"]
    )
    if pr["base"]["ref"] != expected_branch:
        raise Error("Candidate targets a different base branch.")
    approval = approved(root, config, proposal, commit(root, base_ref), github)
    config = approval["config"]
    transport(
        root, config, "fetch", f"+refs/pull/{candidate_pr}/head:refs/aek/candidate"
    )
    head = commit(root, "refs/aek/candidate")
    if head != pr["head"]["sha"]:
        raise Error("Candidate changed while fetching.")
    baseline = commit(root, base_ref)
    image = config["github"].get("verification_image", "")
    if not re.fullmatch(r"[A-Za-z0-9./:_-]+@sha256:[a-f0-9]{64}", image):
        raise Error(
            "Configure a reviewed, digest-pinned Linux verification_image containing project toolchains and dependencies."
        )
    # Synthetic integration commit is assembled by trusted Git; conflict means failure.
    with checkout(root, head) as target:
        # Clone copied the base object. Disable repository hooks while assembling.
        git(
            target,
            "-c",
            "user.name=AEK verifier",
            "-c",
            "user.email=aek@localhost",
            "merge",
            "--no-edit",
            "--no-ff",
            baseline,
            isolated=True,
        )
        merged = commit(target)
        actual = policy.tree(target, merged, config)
        changed = sorted(
            p
            for p in set(actual) | set(approval["snapshot"]["files"])
            if actual.get(p) != approval["snapshot"]["files"].get(p)
        )
        # Export integration object to the trusted controller clone.
        git(target, "push", "--quiet", str(root), f"{merged}:refs/aek/integration")
    return {
        "schema_version": 1,
        "check_run_id": check_id["id"],
        "verification_request": check_id["epoch"],
        "repository": repo,
        "candidate_pr": candidate_pr,
        "candidate": head,
        "base": baseline,
        "integration": merged,
        "config": config,
        "approval": approval,
        "tampered_paths": changed,
        "image": image,
    }


def mount_spec(source, destination, readonly=False):
    fields = ["type=bind", "src=" + str(source), "dst=" + destination]
    if readonly:
        fields.append("readonly")
    output = io.StringIO()
    csv.writer(output, lineterminator="").writerow(fields)
    return output.getvalue()


def readonly_harness(target, config):
    # Freeze the top-level parent too, preventing directory rename/recreation attacks.
    names = set()
    for name in policy.files(target):
        if policy.protected(name, config):
            names.add(name.split("/", 1)[0] if "/" in name else name)
    return sorted(names)


def container_checks(target, checks, image, config):
    results = []
    # A fresh container for every command. Install dependencies in the reviewed image,
    # not by giving a candidate job access to private registry credentials.
    target.chmod(0o755)
    for item in checks:
        argv = policy.command(item)
        if argv[0] == __import__("sys").executable:
            argv[0] = "python3"
        started = time.monotonic()
        value = {
            "name": item["name"],
            "kind": item.get("kind", "custom"),
            "status": "error",
            "argv": argv,
        }
        name = "aek-" + uuid.uuid4().hex
        mounts = [
            "--mount",
            mount_spec(target, "/work"),
            "--mount",
            mount_spec(target / ".git", "/work/.git", True),
        ]
        for protected_name in readonly_harness(target, config):
            mounts += [
                "--mount",
                mount_spec(target / protected_name, "/work/" + protected_name, True),
            ]
        command = [
            "docker",
            "run",
            "--name",
            name,
            "--rm",
            "--network=none",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=256",
            "--memory=4g",
            "--cpus=2",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--env",
            "CI=true",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "--env",
            "PYTHONPATH=/work/src:/work",
            "--env",
            "HOME=/tmp",
            *mounts,
            "--workdir",
            "/work/" + item.get("cwd", "."),
            image,
            *argv,
        ]
        try:
            result = run(command, check=False, timeout=item.get("timeout", 300))
            value.update(
                status="passed" if result.returncode == 0 else "failed",
                returncode=result.returncode,
                output=(result.stdout + result.stderr).decode(errors="replace")[
                    -12000:
                ],
            )
        except Error as exc:
            value["output"] = str(exc)
        finally:
            # Killing a timed-out Docker client does not necessarily stop its container.
            run(["docker", "rm", "--force", name], check=False, timeout=30)
        value["seconds"] = round(time.monotonic() - started, 3)
        results.append(value)
    return results


def execute(root, plan):
    if os.name == "nt":
        raise Error("The independent controller executes on Linux with Docker.")
    if commit(root, "refs/aek/integration") != plan["integration"]:
        raise Error("Integration object does not match trusted plan.")
    expected = plan["approval"]["snapshot"]["files"]
    with checkout(root, plan["integration"]) as target:
        restore(target, plan["approval"]["snapshot"]["commit"], plan["config"])
        if policy.working_tree(target, plan["config"]) != expected:
            raise Error("Approved harness could not be reproduced.")
        results = container_checks(
            target, plan["config"]["checks"], plan["image"], plan["config"]
        )
        try:
            tampered = policy.working_tree(target, plan["config"]) != expected
        except Error:
            tampered = True
    return {
        "candidate": plan["candidate"],
        "environment": {
            "controller": environment(),
            "image": plan["image"],
            "network": "none",
        },
        "integration": plan["integration"],
        "base": plan["base"],
        "harness_digest": digest(plan["approval"]["snapshot"]),
        "tampered_paths": plan["tampered_paths"],
        "post_execution_tampering": tampered,
        "checks": results,
        "passed": not plan["tampered_paths"]
        and not tampered
        and len(results) == len(plan["config"]["checks"])
        and all(item["status"] == "passed" for item in results),
    }


def publish(plan, report, worker_result):
    github = GitHub()
    repo = plan["repository"]
    if plan.get("check_run_id"):
        current_check = github.api(
            f"repos/{repo}/check-runs/{int(plan['check_run_id'])}"
        )
        if current_check.get("external_id") != plan.get("verification_request"):
            raise Error(
                "This verification request was superseded; do not overwrite its newer check."
            )
    current = github.api(f"repos/{repo}/pulls/{plan['candidate_pr']}")
    base = github.api(
        f"repos/{repo}/branches/{quote(plan['config']['github'].get('base_branch') or github.repository(plan['config'])['default_branch'], safe='')}"
    )
    passed = (
        worker_result == "success"
        and report.get("passed") is True
        and report.get("candidate") == plan["candidate"]
        and report.get("integration") == plan["integration"]
        and report.get("base") == plan["base"]
        and report.get("harness_digest") == digest(plan["approval"]["snapshot"])
        and current["head"]["sha"] == plan["candidate"]
        and base["commit"]["sha"] == plan["base"]
        and current.get("state") == "open"
        and proposal_number(current) == plan["approval"]["proposal"]
        and current["base"]["ref"]
        == (
            plan["config"]["github"].get("base_branch")
            or github.repository(plan["config"])["default_branch"]
        )
        and current["base"]["repo"]["full_name"].casefold() == repo.casefold()
    )
    wanted = {c["name"] for c in plan["config"]["checks"]}
    checks = report.get("checks", [])
    if (
        len(checks) != len(wanted)
        or {c.get("name") for c in checks if c.get("status") == "passed"} != wanted
    ):
        passed = False
    # Revalidate the live review even if tests ran for a long time.
    reviews = github.pages(f"repos/{repo}/pulls/{plan['approval']['proposal']}/reviews")
    original = next(
        (r for r in reviews if r["id"] == plan["approval"]["review_id"]), None
    )
    if (
        not original
        or original["state"] != "APPROVED"
        or original["commit_id"] != plan["approval"]["snapshot"]["commit"]
        or original["user"]["id"] not in plan["config"]["github"]["human_ids"]
        or original["user"].get("type") != "User"
        or plan["approval"].get("marker")
        not in (original.get("body") or "").splitlines()
    ):
        passed = False
    latest = {}
    for record in reviews:
        if record.get("state") != "COMMENTED":
            latest[record["user"]["id"]] = record
    if original and latest.get(original["user"]["id"], {}).get("id") != original["id"]:
        passed = False
    if any(
        record["state"] == "CHANGES_REQUESTED"
        for ident, record in latest.items()
        if ident in plan["config"]["github"]["human_ids"]
    ):
        passed = False
    proposal = github.api(f"repos/{repo}/pulls/{plan['approval']['proposal']}")
    if (
        proposal["state"] != "open"
        or proposal["head"]["sha"] != plan["approval"]["snapshot"]["commit"]
    ):
        passed = False
    body = {
        "name": "aek/verification",
        "head_sha": plan["candidate"],
        "status": "completed",
        "conclusion": "success" if passed else "failure",
        "output": {
            "title": "Independent harness verification",
            "summary": json.dumps(report, indent=2)[:60000],
        },
    }
    if plan.get("check_run_id"):
        body.pop("head_sha")
        return github.api(
            f"repos/{repo}/check-runs/{int(plan['check_run_id'])}", "PATCH", body
        )
    return github.api(f"repos/{repo}/check-runs", "POST", body)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "execute", "publish"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--event", type=Path)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--worker-result", default="failure")
    args = parser.parse_args()
    try:
        root = Path(args.root).resolve()
        if args.action == "prepare":
            value = prepare(root, read_json(args.event))
            write_json(args.plan, value)
            # Bundle all needed objects; downstream jobs never trust candidate artifacts.
            git(
                root, "bundle", "create", str(args.plan.with_suffix(".bundle")), "--all"
            )
        elif args.action == "execute":
            value = execute(root, read_json(args.plan))
            write_json(args.report, value)
            if not value["passed"]:
                return 1
        else:
            value = publish(
                read_json(args.plan),
                read_json(args.report) if args.report and args.report.exists() else {},
                args.worker_result,
            )
        print(json.dumps(value))
        return 0
    except (Error, OSError, ValueError, KeyError) as exc:
        print(f"AEK CI: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
