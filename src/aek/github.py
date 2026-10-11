from __future__ import annotations

import json
import os
import re

from .common import Error, git, run


class GitHub:
    """GitHub CLI credential transport. No credentials are saved by AEK."""

    def api(self, endpoint, method="GET", body=None):
        argv = ["gh", "api", "--hostname", "github.com", endpoint, "--method", method]
        payload = None
        if body is not None:
            argv += ["--input", "-"]
            payload = json.dumps(body).encode()
        result = run(argv, input=payload)
        try:
            return json.loads(result.stdout) if result.stdout.strip() else None
        except ValueError as exc:
            raise Error("GitHub returned invalid JSON.") from exc

    def pages(self, endpoint):
        result = []
        for page in range(1, 101):
            items = self.api(
                f"{endpoint}{'&' if '?' in endpoint else '?'}per_page=100&page={page}"
            )
            if not isinstance(items, list):
                raise Error("Unexpected GitHub pagination response.")
            result += items
            if len(items) < 100:
                return result
        raise Error("GitHub pagination exceeded its safety limit.")

    def repository(self, config):
        return self.api("repos/" + config["github"]["repository"])

    def token(self):
        # Capture privately; never print or persist the token or authenticated URL.
        return (
            os.environ.get("GH_TOKEN")
            or os.environ.get("GITHUB_TOKEN")
            or run(["gh", "auth", "token", "--hostname", "github.com"])
            .stdout.decode()
            .strip()
        )

    def identity(self, config):
        user = self.api("user")
        if user["id"] in config["github"]["human_ids"]:
            raise Error(
                "Publishing credentials belong to a harness approver. Use a separate agent identity."
            )
        if (
            not config["github"]["agent_login"]
            or user["login"].casefold() != config["github"]["agent_login"].casefold()
        ):
            raise Error(
                "Authenticated GitHub identity does not match configured github.agent_login."
            )
        repository = self.repository(config)
        if repository.get("permissions", {}).get("admin", True):
            raise Error(
                "Agent identity must not have repository administrator permissions."
            )
        return user


def repo_from_remote(root):
    remote = (
        git(root, "remote", "get-url", "origin", check=False).stdout.decode().strip()
    )
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([\w.-]+/[\w.-]+?)(?:\.git)?/?",
        remote,
    )
    if not match:
        raise Error(
            "Configure a GitHub origin, or provide --repository owner/repository."
        )
    return match.group(1)


def fetch(root, config, proposal=None):
    if repo_from_remote(root).casefold() != config["github"]["repository"].casefold():
        raise Error("Git origin does not match the enrolled GitHub repository.")
    branch = (
        config["github"].get("base_branch")
        or GitHub().repository(config)["default_branch"]
    )
    if (
        not re.fullmatch(r"[A-Za-z0-9_./-]+", branch)
        or branch.startswith("-")
        or ".." in branch
    ):
        raise Error("Invalid base branch.")
    transport(
        root,
        config,
        "fetch",
        "--no-tags",
        f"+refs/heads/{branch}:refs/remotes/origin/{branch}",
    )
    if proposal:
        transport(
            root,
            config,
            "fetch",
            "--no-tags",
            f"+refs/pull/{int(proposal)}/head:refs/aek/proposals/{int(proposal)}",
        )
    return "refs/remotes/origin/" + branch


def transport(root, config, operation, *args):
    import base64

    token = GitHub().token()
    if not token:
        raise Error("No GitHub transport credential available.")
    auth = base64.b64encode(("x-access-token:" + token).encode()).decode()
    url = "https://github.com/" + config["github"]["repository"] + ".git"
    # Bind both API and Git publishing to the same token; do not fall back to a human SSH key.
    flags = [
        "-c",
        "credential.helper=",
        "-c",
        "http.https://github.com/.extraheader=AUTHORIZATION: basic " + auth,
    ]
    if operation == "fetch":
        return git(
            root,
            *flags,
            "fetch",
            "--no-tags",
            url,
            *[x for x in args if x != "--no-tags"],
        )
    if operation == "push":
        return git(root, *flags, "push", url, *args)
    raise Error("Unsupported authenticated Git transport operation.")


def protection(config, github=None):
    github = github or GitHub()
    repository = github.repository(config)
    branch = config["github"].get("base_branch") or repository["default_branch"]
    from urllib.parse import quote

    policy = github.api(
        f"repos/{config['github']['repository']}/branches/{quote(branch, safe='')}/protection"
    )
    checks = policy.get("required_status_checks") or {}
    app = config["github"].get("check_app_id", 0)
    expected = {"context": "aek/verification", "app_id": app}
    if not app or expected not in checks.get("checks", []) or not checks.get("strict"):
        raise Error(
            "Require aek/verification from the configured App, with branches up to date."
        )
    if not (policy.get("enforce_admins") or {}).get("enabled"):
        raise Error("Repository protection must apply to administrators too.")
    environment = f"repos/{config['github']['repository']}/environments/aek-authority"
    authority = github.api(environment)
    restriction = authority.get("deployment_branch_policy") or {}
    if (
        restriction.get("custom_branch_policies") is not True
        or restriction.get("protected_branches") is not False
    ):
        raise Error(
            "Restrict the aek-authority environment to only the default branch using a custom branch rule."
        )
    allowed = github.api(environment + "/deployment-branch-policies?per_page=100")
    entries = allowed.get("branch_policies", [])
    if (
        allowed.get("total_count") != 1
        or len(entries) != 1
        or entries[0].get("name") != repository["default_branch"]
        or entries[0].get("type", "branch") != "branch"
    ):
        raise Error(
            "The aek-authority environment must allow exactly the default branch, with no tag or wildcard rules."
        )
    if any(c in repository["default_branch"] for c in "*?["):
        raise Error(
            "The default branch contains pattern metacharacters; an exact environment branch rule cannot be guaranteed."
        )
    return {
        "base_branch": branch,
        "app_id": app,
        "required_check": "aek/verification",
        "authority_environment": "aek-authority",
    }
