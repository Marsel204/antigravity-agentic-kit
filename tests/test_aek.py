from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aek.common import Error, commit, digest, git, read_json, run, state_dir, write_json
from aek import policy
from aek.harness import approved, marker, snapshot
from aek.verify import verify, execute
from aek.adapters import adapter, blocked_paths
from aek.context import update_task, new_worktree, task_path
from aek.install import install, uninstall, enroll_hooks
from aek.github import protection
from aek.ci import publish


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aek-tests-")
        self.root = Path(self.temp.name) / "project space"
        self.root.mkdir()
        run(["git", "init", "--quiet", "--initial-branch=trunk", self.root])
        git(
            self.root,
            "config",
            "core.hooksPath",
            str(Path(self.temp.name) / "empty-hooks"),
        )
        git(self.root, "config", "core.autocrlf", "false")
        git(self.root, "config", "user.name", "Fixture")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        self.config = policy.discover(self.root, "owner/project", [123])
        self.config["github"].update(
            agent_login="agent-bot",
            check_app_id=456,
            base_branch="trunk",
            verification_image="example/image@sha256:" + "a" * 64,
        )
        self.config["checks"] = [
            {
                "name": "tests",
                "kind": "test",
                "required": True,
                "argv": ["{python}", "tests/check.py"],
                "timeout": 15,
            }
        ]
        self.write(".aek/project.json", json.dumps(self.config))
        self.write(".aek/architecture.md", "Only services write to the database.\n")
        self.write("tests/check.py", "assert 2 + 2 == 4\n")
        self.write("source.py", "value = 4\n")
        self.write(".gitignore", "__pycache__/\n.pytest_cache/\n")
        self.base = self.save()
        self.approval = {
            "proposal": 7,
            "review_id": 99,
            "reviewer_id": 123,
            "snapshot": snapshot(self.root, self.base, self.config),
            "base": self.base,
            "repository": "owner/project",
            "marker": marker(self.root, self.base, self.base, self.config),
        }

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def save(self):
        git(self.root, "add", "--all")
        git(
            self.root,
            "-c",
            "core.hooksPath=" + str(Path(self.temp.name) / "empty-hooks"),
            "commit",
            "--quiet",
            "-m",
            "fixture",
        )
        return commit(self.root)

    def verify(self):
        return verify(
            self.root,
            config=self.config,
            approval=self.approval,
            authority="github-verified",
        )

    def github(self, sha=None, reviews=None):
        sha = sha or self.base
        review = {
            "id": 99,
            "user": {"id": 123, "type": "User"},
            "state": "APPROVED",
            "commit_id": sha,
            "body": marker(self.root, sha, self.base, self.config),
        }

        class Fake:
            def api(inner, endpoint, method="GET", body=None):
                if "/check-runs?" in endpoint:
                    return {"check_runs": []}
                if endpoint.endswith("/check-runs"):
                    return dict(body, id=321)
                if "/check-runs/" in endpoint:
                    return body
                if "/branches/" in endpoint:
                    return {"commit": {"sha": self.base}}
                if endpoint.endswith("/pulls/7"):
                    return {
                        "state": "open",
                        "body": "AEK-PROPOSAL: 7",
                        "merged": False,
                        "head": {"sha": sha},
                        "base": {
                            "ref": "trunk",
                            "repo": {"full_name": "owner/project"},
                        },
                    }
                raise AssertionError(endpoint)

            def pages(inner, endpoint):
                return reviews if reviews is not None else [review]

            def repository(inner, config):
                return {"default_branch": "trunk"}

        return Fake()


class HarnessTests(RepoCase):
    def test_windows_style_custom_protected_paths_match_repository_paths(self):
        self.config["protected_paths"].append("support\\assertions\\**")
        policy.validate(self.config)
        self.assertTrue(policy.protected("support/assertions/helper.py", self.config))
        self.assertTrue(policy.protected("support\\assertions\\helper.py", self.config))

    @unittest.skipUnless(os.name == "nt", "Native Windows junction acceptance")
    def test_junction_harness_alias_rejected_without_symlink_privileges(self):
        outside = Path(self.temp.name) / "external-tests"
        shutil.copytree(self.root / "tests", outside)
        shutil.rmtree(self.root / "tests")
        run(["cmd", "/c", "mklink", "/J", self.root / "tests", outside])
        with self.assertRaisesRegex(Error, "junction"):
            self.verify()

    def test_disposable_checkout_does_not_execute_global_smudge_filter(self):
        from aek.common import checkout
        import shlex

        self.write(".gitattributes", "*.py filter=witness\n")
        sha = self.save()
        home = Path(self.temp.name) / "filter-home"
        home.mkdir()
        witness = home / "executed"
        command = shlex.join(
            [sys.executable, "-c", f"open({str(witness)!r}, 'w').write('executed')"]
        )
        run(
            [
                "git",
                "config",
                "--file",
                home / ".gitconfig",
                "filter.witness.smudge",
                command,
            ]
        )
        with patch.dict(os.environ, {"HOME": str(home)}):
            with checkout(self.root, sha) as target:
                self.assertEqual((target / "source.py").read_text(), "value = 4\n")
        self.assertFalse(witness.exists())

    def test_timeout_error_does_not_expose_transport_credentials(self):
        import subprocess

        argv = ["git", "-c", "http.extraheader=AUTHORIZATION: secret-fixture"]
        with patch(
            "aek.common.subprocess.run", side_effect=subprocess.TimeoutExpired(argv, 1)
        ):
            with self.assertRaises(Error) as result:
                run(argv, timeout=1)
        self.assertNotIn("secret-fixture", str(result.exception))

    def test_candidate_verifier_change_fails_against_approved_core(self):
        self.write(".aek/ci/aek/ci.py", "trusted = True\n")
        self.base = self.save()
        self.approval["snapshot"] = snapshot(self.root, self.base, self.config)
        self.write(".aek/ci/aek/ci.py", "trusted = False\n")
        self.save()
        result = self.verify()
        self.assertFalse(result["passed"])
        self.assertIn(".aek/ci/aek/ci.py", result["tampered_paths"])
        self.assertEqual(result["checks"][0]["status"], "passed")

    def test_git_text_crlf_conversion_preserves_approved_harness(self):
        git(self.root, "config", "core.autocrlf", "true")
        path = self.root / "tests/check.py"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertTrue(self.verify()["passed"])
        path.write_bytes(b"assert 2 + 2 == 0\r\n")
        self.assertFalse(self.verify()["passed"])

    def test_attribute_change_is_protected(self):
        self.assertTrue(policy.protected(".gitattributes", self.config))
        self.assertTrue(policy.protected("tests/.gitattributes", self.config))

    def test_approved_tests_pass_without_touching_worktree(self):
        before = git(self.root, "status", "--porcelain").stdout
        report = self.verify()
        self.assertTrue(report["passed"])
        self.assertEqual(report["checks"][0]["status"], "passed")
        self.assertEqual(before, git(self.root, "status", "--porcelain").stdout)

    def test_approved_new_feature_test_is_preserved(self):
        self.write("tests/new.test.py", "assert True\n")
        sha = self.save()
        self.approval["snapshot"] = snapshot(self.root, sha, self.config)
        self.assertTrue(self.verify()["passed"])
        self.assertTrue((self.root / "tests/new.test.py").exists())

    def test_working_edit_fails_even_restored_tests_pass(self):
        original = (self.root / "tests/check.py").read_text()
        self.write("tests/check.py", "pass\n")
        report = self.verify()
        self.assertFalse(report["passed"])
        self.assertEqual(report["checks"][0]["status"], "passed")
        self.assertEqual((self.root / "tests/check.py").read_text(), "pass\n")
        self.assertNotEqual(original, "pass\n")

    def test_committed_edit_fails_even_restored_tests_pass(self):
        self.write("tests/check.py", "pass\n")
        self.save()
        self.assertFalse(self.verify()["passed"])

    def test_new_untracked_test_fails(self):
        self.write("tests/extra.py", "pass\n")
        self.assertFalse(self.verify()["passed"])

    def test_staged_tampering_hidden_by_restored_working_bytes_fails(self):
        original = (self.root / "tests/check.py").read_text()
        self.write("tests/check.py", "pass\n")
        git(self.root, "add", "tests/check.py")
        self.write("tests/check.py", original)
        self.assertFalse(self.verify()["passed"])

    def test_ignored_protected_addition_fails(self):
        self.write("tests/.gitignore", "hidden.py\n")
        self.write("tests/hidden.py", "pass\n")
        self.assertFalse(self.verify()["passed"])

    def test_reviewed_ignored_dependency_tests_are_excluded_but_tracked_tests_are_not(
        self,
    ):
        self.write(".gitignore", "node_modules/\n")
        self.base = self.save()
        self.approval["snapshot"] = snapshot(self.root, self.base, self.config)
        self.write("node_modules/dependency/tests/check.py", "pass\n")
        self.assertTrue(self.verify()["passed"])
        git(self.root, "add", "--force", "node_modules/dependency/tests/check.py")
        self.assertFalse(self.verify()["passed"])

    def test_deleted_test_fails(self):
        (self.root / "tests/check.py").unlink()
        self.assertFalse(self.verify()["passed"])

    def test_renamed_test_fails(self):
        git(self.root, "mv", "tests/check.py", "source_check.py")
        self.save()
        self.assertFalse(self.verify()["passed"])

    def test_fixture_and_runner_change_fails(self):
        self.write("fixtures/input.json", "{}")
        self.assertFalse(self.verify()["passed"])
        self.config["checks"][0]["argv"] = ["{python}", "-c", "pass"]
        self.write(".aek/project.json", json.dumps(self.config))
        self.save()
        self.assertFalse(self.verify()["passed"])

    def test_source_edits_dont_count_as_harness_tampering(self):
        self.write("source.py", "value = 5\n")
        self.save()
        self.assertTrue(self.verify()["passed"])

    def test_test_failure_fails(self):
        self.write("tests/check.py", "assert False\n")
        sha = self.save()
        self.approval["snapshot"] = snapshot(self.root, sha, self.config)
        self.assertFalse(self.verify()["passed"])

    def test_postexecution_tampering_fails(self):
        self.write(
            "tests/check.py",
            "from pathlib import Path\nPath('tests/check.py').write_text('pass\\n')\n",
        )
        sha = self.save()
        self.approval["snapshot"] = snapshot(self.root, sha, self.config)
        self.assertTrue(self.verify()["post_execution_tampering"])

    def test_missing_runner_fails(self):
        check = dict(self.config["checks"][0], argv=["aek-no-such-executable-12345"])
        self.assertEqual(execute(self.root, [check])[0]["status"], "error")

    def test_timeout_fails(self):
        check = dict(
            self.config["checks"][0],
            timeout=1,
            argv=["{python}", "-c", "import time; time.sleep(10)"],
        )
        self.assertEqual(execute(self.root, [check])[0]["status"], "timeout")

    def test_symlink_alias_denied(self):
        alias = self.root / "alias.py"
        try:
            alias.symlink_to(self.root / "tests/check.py")
        except OSError:
            self.skipTest("Symlink creation unavailable")
        self.assertEqual(
            blocked_paths(self.root, ["alias.py"], self.config), ["alias.py"]
        )

    def test_protected_symlinks_rejected(self):
        path = self.root / "tests/link.py"
        try:
            path.symlink_to(self.root / "source.py")
        except OSError:
            self.skipTest("Symlink creation unavailable")
        self.save()
        with self.assertRaises(Error):
            policy.tree(self.root, "HEAD", self.config)

    def test_filename_with_newline_is_fingerprinted(self):
        if os.name == "nt":
            self.skipTest("Windows forbids newline filenames")
        self.write("tests/odd\nname.py", "pass\n")
        self.assertIn("tests/odd\nname.py", self.verify()["tampered_paths"])


class ApprovalTests(RepoCase):
    def test_workspace_records_reviewable_initial_baseline_and_keeps_guards(self):
        from aek.harness import workspace

        git(
            self.root, "remote", "add", "origin", "https://github.com/owner/project.git"
        )
        with patch("aek.harness.fetch", return_value=self.base):
            result = workspace(self.root, "baseline", "codex/test-baseline")
        target = Path(result["workspace"])
        record = read_json(target / ".aek/proposals/baseline.json")
        self.assertEqual(record["baseline"], self.base)
        self.assertTrue(policy.protected(".aek/proposals/baseline.json", self.config))
        self.assertNotEqual(commit(target), self.base)
        self.assertEqual(git(target, "status", "--porcelain").stdout, b"")
        self.assertIn(
            "aek-hooks",
            git(target, "config", "--get", "core.hooksPath").stdout.decode(),
        )

    def test_real_approved_marker_accepted(self):
        result = approved(self.root, self.config, 7, self.base, self.github())
        self.assertEqual(result["reviewer_id"], 123)

    def test_untrusted_reviewer_rejected(self):
        fake = self.github()
        records = fake.pages("")
        records[0]["user"]["id"] = 999
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, self.base, self.github(reviews=records))

    def test_bot_reviewer_rejected(self):
        fake = self.github()
        records = fake.pages("")
        records[0]["user"]["type"] = "Bot"
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, self.base, self.github(reviews=records))

    def test_dismissed_review_rejected(self):
        records = self.github().pages("")
        records[0]["state"] = "DISMISSED"
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, self.base, self.github(reviews=records))

    def test_real_rust_proposal_flags_planned_api_failure_for_human_review(self):
        from aek.harness import propose

        if not shutil.which("cargo"):
            if os.environ.get("AEK_REQUIRE_PROFILES") == "1":
                self.fail("cargo required for acceptance")
            self.skipTest("cargo unavailable")
        self.write(
            "Cargo.toml", '[package]\nname="fixture"\nversion="0.1.0"\nedition="2021"\n'
        )
        self.write(
            "Cargo.lock", 'version = 3\n[[package]]\nname="fixture"\nversion="0.1.0"\n'
        )
        self.write("src/lib.rs", "pub fn existing() -> i32 { 1 }\n")
        self.write(".gitignore", "target/\n")
        self.config["checks"] = [
            {
                "name": "rust-tests",
                "kind": "test",
                "required": True,
                "argv": ["cargo", "test", "--locked"],
                "timeout": 120,
            }
        ]
        self.write(".aek/project.json", json.dumps(self.config))
        baseline = self.save()
        git(self.root, "switch", "-c", "codex/new-api-tests")
        self.write(
            "tests/new_api.rs",
            "#[test]\nfn proposed() { assert_eq!(fixture::added(), 2); }\n",
        )
        self.save()
        with patch("aek.harness.fetch", return_value=baseline):
            result = propose(self.root, None, ["rust-tests"])
        self.assertEqual(result["checks"][0]["status"], "failed")
        self.assertTrue(
            any(
                flag["kind"] == "planned-api-compile-failure-needs-human-review"
                for flag in result["audit"]["flags"]
            )
        )

    def test_proposal_cannot_widen_artifact_exclusions(self):
        from aek.harness import validate_change

        proposed = json.loads(json.dumps(self.config))
        proposed["ignored_artifacts"].append("tests/**")
        with self.assertRaisesRegex(Error, "Widening ignored artifact"):
            validate_change(self.config, proposed)

    def test_changed_proposal_rejected(self):
        records = self.github().pages("")
        self.write("tests/new.py", "pass\n")
        sha = self.save()
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, self.base, self.github(sha, records))

    def test_implementation_in_proposal_rejected(self):
        self.write("source.py", "new = 6\n")
        sha = self.save()
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, self.base, self.github(sha))

    def test_changed_policy_rejected(self):
        altered = dict(self.config)
        altered["checks"] = [
            dict(self.config["checks"][0], argv=["{python}", "-c", "pass"])
        ]
        self.write(".aek/project.json", json.dumps(altered))
        sha = self.save()
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, self.base, self.github(sha))

    def test_exact_human_approval_can_change_runner(self):
        altered = json.loads(json.dumps(self.config))
        altered["checks"][0]["argv"] = ["{python}", "-c", "assert 2+2 == 4"]
        self.write(".aek/project.json", json.dumps(altered))
        sha = self.save()
        records = self.github(sha).pages("")
        records[0]["body"] = marker(self.root, sha, self.base, altered)
        result = approved(
            self.root, self.config, 7, self.base, self.github(sha, records)
        )
        self.assertEqual(
            result["config"]["checks"][0]["argv"], altered["checks"][0]["argv"]
        )

    def test_policy_cannot_add_agent_as_reviewer(self):
        altered = json.loads(json.dumps(self.config))
        altered["github"]["human_ids"].append(999)
        self.write(".aek/project.json", json.dumps(altered))
        sha = self.save()
        records = self.github(sha).pages("")
        records[0]["body"] = marker(self.root, sha, self.base, altered)
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, self.base, self.github(sha, records))

    def test_target_harness_change_requires_reapproval(self):
        proposal = self.base
        self.write("tests/new.py", "pass\n")
        new_base = self.save()
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, new_base, self.github(proposal))

    def test_forged_cached_approval_never_authorizes_online(self):
        from aek.harness import resolve

        write_json(state_dir(self.root) / "approval.json", self.approval)
        with (
            patch("aek.harness.fetch", return_value=self.base),
            patch("aek.harness.GitHub", return_value=self.github(reviews=[])),
        ):
            with self.assertRaises(Error):
                resolve(self.root)

    def test_only_offline_mode_uses_cache(self):
        from aek.harness import resolve

        write_json(state_dir(self.root) / "approval.json", self.approval)
        _, _, authority = resolve(self.root, offline=True)
        self.assertEqual(authority, "cached-untrusted")

    def test_later_changes_requested_supersedes_approval(self):
        records = self.github().pages("")
        records.append(dict(records[0], id=100, state="CHANGES_REQUESTED"))
        with self.assertRaises(Error):
            approved(self.root, self.config, 7, self.base, self.github(reviews=records))


class HookTests(RepoCase):
    def test_absolute_write_from_unenrolled_cwd_checks_target_repository(self):
        outside = Path(self.temp.name) / "unenrolled"
        outside.mkdir()
        payload = {
            "cwd": str(outside),
            "tool_name": "apply_patch",
            "tool_input": {
                "input": f"*** Begin Patch\n*** Update File: {self.root / 'tests/check.py'}\n*** End Patch"
            },
        }
        value = adapter("codex", payload)
        self.assertEqual(value["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_proposal_role_cannot_unlock_other_worktree(self):
        other = Path(
            new_worktree(self.root, "worker", "codex/worker", ["source.py"], True)[
                "path"
            ]
        )
        git(self.root, "config", "aek.proposalWorkspace", "true")
        git(self.root, "config", "aek.proposalRoot", str(self.root))
        value = adapter(
            "codex",
            {
                "cwd": str(self.root),
                "tool_name": "Write",
                "tool_input": {"file_path": str(other / "tests/check.py")},
            },
        )
        self.assertEqual(value["hookSpecificOutput"]["permissionDecision"], "deny")

    def setUp(self):
        super().setUp()
        enroll_hooks(self.root)

    def attempt(self, value=None):
        env = dict(os.environ)
        env.pop("ALLOW_TEST_EDITS", None)
        if value is not None:
            env["ALLOW_TEST_EDITS"] = value
        return run(
            ["git", "-C", self.root, "commit", "-m", "attempt"], check=False, env=env
        )

    def test_block_staged_test(self):
        self.write("tests/check.py", "pass\n")
        git(self.root, "add", "--all")
        self.assertNotEqual(self.attempt().returncode, 0)

    def test_only_exact_one_bypasses(self):
        self.write("tests/check.py", "pass\n")
        git(self.root, "add", "--all")
        self.assertNotEqual(self.attempt("true").returncode, 0)
        self.assertEqual(self.attempt("1").returncode, 0)

    def test_source_commit_allowed(self):
        self.write("source.py", "value = 9\n")
        git(self.root, "add", "--all")
        self.assertEqual(self.attempt().returncode, 0)

    def test_rename_to_source_still_blocked(self):
        git(self.root, "mv", "tests/check.py", "safe.py")
        self.assertNotEqual(self.attempt().returncode, 0)

    def test_forwarded_hook_cannot_stage_test(self):
        previous = Path(self.temp.name) / "native"
        previous.mkdir()
        hook = previous / "pre-commit"
        hook.write_text(
            '#!/bin/sh\nprintf "pass\\n" > tests/check.py\ngit add tests/check.py\n'
        )
        hook.chmod(0o755)
        git(self.root, "config", "aek.previousHooksPath", str(previous))
        self.write("source.py", "value = 7\n")
        git(self.root, "add", "--all")
        self.assertNotEqual(self.attempt().returncode, 0)

    def test_codex_patch_and_move_denied(self):
        payload = {
            "cwd": str(self.root),
            "tool_name": "apply_patch",
            "tool_input": {
                "command": "*** Begin Patch\n*** Update File: source.py\n*** Move to: tests/renamed.py\n*** End Patch"
            },
        }
        self.assertEqual(
            adapter("codex", payload)["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )

    def test_reading_harness_is_allowed(self):
        payload = {
            "cwd": str(self.root),
            "tool_name": "mcp__filesystem__read_file",
            "tool_input": {"path": str(self.root / "tests/check.py")},
        }
        self.assertEqual(adapter("codex", payload), {})

    def test_unknown_write_schema_denied(self):
        payload = {
            "cwd": str(self.root),
            "tool_name": "mcp__filesystem__write_file",
            "tool_input": {"unknown": "x"},
        }
        self.assertEqual(
            adapter("codex", payload)["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )

    def test_malformed_payload_denied(self):
        self.assertEqual(adapter("antigravity", 42)["decision"], "deny")

    def test_antigravity_write_denied(self):
        payload = {
            "workspacePaths": [str(self.root)],
            "toolCall": {
                "name": "multi_replace_file_content",
                "args": {"TargetFile": str(self.root / "tests/check.py")},
            },
        }
        self.assertEqual(adapter("antigravity", payload)["decision"], "deny")

    def test_antigravity_source_allowed(self):
        payload = {
            "workspacePaths": [str(self.root)],
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.root / "source.py")},
            },
        }
        self.assertEqual(adapter("antigravity", payload)["decision"], "allow")

    def test_proposal_workspace_can_author_without_granting_approval(self):
        git(self.root, "config", "aek.proposalWorkspace", "true")
        git(self.root, "config", "aek.proposalRoot", str(self.root))
        payload = {
            "workspacePaths": [str(self.root)],
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.root / "tests/check.py")},
            },
        }
        self.assertEqual(adapter("antigravity", payload)["decision"], "allow")
        self.write("tests/check.py", "pass\n")
        git(self.root, "add", "--all")
        self.assertNotEqual(self.attempt().returncode, 0)

    def test_compaction_context_has_architecture(self):
        output = adapter(
            "codex",
            {
                "cwd": str(self.root),
                "hook_event_name": "SessionStart",
                "source": "compact",
            },
        )
        self.assertIn(
            "Only services", output["hookSpecificOutput"]["additionalContext"]
        )

    def test_antigravity_invocation_injects_context(self):
        output = adapter(
            "antigravity", {"workspacePaths": [str(self.root)], "invocationNum": 10}
        )
        self.assertIn("Only services", output["injectSteps"][0]["ephemeralMessage"])


class StateTests(RepoCase):
    def test_graph_fingerprint_covers_rescued_ignored_source(self):
        from aek.graph import provenance

        self.write(".gitignore", "ignored/\n")
        self.write(".graphifyignore", "!ignored/**\n")
        source = self.write("ignored/source.py", "value = 1\n")
        before = provenance(self.root)
        source.write_text("value = 2\n")
        self.assertNotEqual(before, provenance(self.root))

    def test_ship_cannot_accept_report_for_different_commit(self):
        from aek.release import ship

        git(self.root, "switch", "-c", "codex/feature")
        github = self.github()
        github.identity = lambda config: {"login": "agent-bot"}
        report = {"passed": True, "authority": "github-verified", "commit": "f" * 40}
        with (
            patch("aek.release.GitHub", return_value=github),
            patch("aek.release.protection"),
            patch("aek.release.verify", return_value=report) as verifier,
            patch("aek.release.transport") as publisher,
        ):
            with self.assertRaisesRegex(Error, "Commit changed"):
                ship(self.root, "feature", "self-reviewed")
            verifier.assert_called_once()
            publisher.assert_not_called()

    def test_disabled_context_does_not_inject_or_enable_module(self):
        self.config["modules"] = ["harness"]
        self.write(".aek/project.json", json.dumps(self.config))
        value = adapter(
            "codex", {"cwd": str(self.root), "hook_event_name": "SessionStart"}
        )
        self.assertEqual(value, {})
        with self.assertRaisesRegex(Error, "disabled"):
            update_task(self.root, "one", {}, 0)

    def test_directory_ownership_conflict_and_ambiguous_globs(self):
        new_worktree(self.root, "one", "codex/one", ["src/service/**"], True)
        with self.assertRaisesRegex(Error, "overlaps"):
            new_worktree(
                self.root, "two", "codex/two", ["src/service/handler.py"], True
            )
        with self.assertRaisesRegex(Error, "exact path"):
            new_worktree(self.root, "three", "codex/three", ["src/*/handler.py"], True)

    def test_atomic_revision_conflict(self):
        self.assertEqual(
            update_task(self.root, "one", {"status": "ready"}, 0)["revision"], 1
        )
        with self.assertRaises(Error):
            update_task(self.root, "one", {"status": "stale"}, 0)
        self.assertEqual(read_json(task_path(self.root, "one"))["status"], "ready")

    def test_concurrent_updates_have_one_winner(self):
        results = []

        def put():
            try:
                update_task(self.root, "one", {"status": "ready"}, 0)
                results.append("success")
            except Error:
                results.append("conflict")

        threads = [threading.Thread(target=put) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(results), ["conflict", "success"])

    def test_parallel_requires_request(self):
        with self.assertRaises(Error):
            new_worktree(self.root, "one", "codex/one", ["source.py"])

    def test_worktrees_have_separate_state_and_ownership(self):
        task = new_worktree(self.root, "one", "codex/one", ["source.py"], True)
        root2 = Path(task["path"])
        update_task(self.root, "one", {"status": "parent"}, 0)
        self.assertEqual(read_json(task_path(root2, "one"))["status"], "ready")
        with self.assertRaises(Error):
            new_worktree(self.root, "two", "codex/two", ["source.py"], True)

    def test_task_path_traversal_rejected(self):
        with self.assertRaises(Error):
            update_task(self.root, "../escape", {}, 0)

    def test_stale_graph_rejected(self):
        from aek.graph import provenance, query

        folder = state_dir(self.root) / "graph"
        folder.mkdir()
        (folder / "graph.json").write_text("{}")
        write_json(folder / "provenance.json", provenance(self.root))
        self.write("source.py", "value = 8\n")
        with self.assertRaisesRegex(Error, "stale"):
            query(self.root, "value")


class InstallationTests(unittest.TestCase):
    def test_malformed_nested_hooks_fail_before_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            write_json(home / ".codex/hooks.json", {"hooks": {"PreToolUse": {}}})
            with self.assertRaisesRegex(Error, "hook events"):
                install(["codex"], home)
            self.assertFalse((home / ".local/share/aek").exists())

    def test_installed_launcher_can_upgrade_from_explicit_source(self):
        from aek.install import SOURCE

        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            install(["codex"], home)
            entry = home / ".local/share/aek/scripts/aek.py"
            result = run(
                [
                    sys.executable,
                    entry,
                    "--json",
                    "update",
                    "--home",
                    home,
                    "--source",
                    SOURCE,
                    "--agent",
                    "codex",
                ]
            )
            self.assertEqual(json.loads(result.stdout)["adapters"], ["codex"])

    def test_modified_managed_instructions_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            install(["codex"], home)
            path = home / ".codex/AGENTS.md"
            path.write_text(
                path.read_text().replace(
                    "human approval", "my extra policy and human approval"
                )
            )
            with self.assertRaisesRegex(Error, "modified AEK instructions"):
                install(["codex"], home)
            result = uninstall(home)
            self.assertIn(str(path), result["preserved_modified_files"])
            self.assertIn("my extra policy", path.read_text())

    def test_enrollment_collision_does_not_partially_write_policy(self):
        from aek.cli import initialize, parser

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "pytest.ini").write_text("[pytest]\n")
            write_json(
                root / "proposal.json", policy.discover(root, "owner/project", [123])
            )
            existing = root / ".github/workflows/aek-controller.yml"
            existing.parent.mkdir(parents=True)
            existing.write_text("custom controller")
            args = parser().parse_args(
                ["init", "--accept", str(root / "proposal.json"), "--ci"]
            )
            with self.assertRaisesRegex(Error, "overwrite"):
                initialize(args, root)
            self.assertFalse((root / ".aek/project.json").exists())
            self.assertEqual(existing.read_text(), "custom controller")

    def test_install_repeat_preserves_unrelated_hooks_and_uninstall(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            hooks = home / ".codex/hooks.json"
            original = {
                "custom": True,
                "hooks": {
                    "PreToolUse": [
                        {"matcher": "Bash", "hooks": [{"command": "echo custom"}]}
                    ]
                },
            }
            write_json(hooks, original)
            install(["codex", "antigravity"], home)
            install(["codex", "antigravity"], home)
            current = read_json(hooks)
            self.assertEqual(
                current["hooks"]["PreToolUse"][0]["hooks"][0]["command"], "echo custom"
            )
            self.assertEqual(len(current["hooks"]["PreToolUse"]), 2)
            self.assertTrue((home / ".local/share/aek/scripts/aek.py").exists())
            uninstall(home)
            self.assertTrue(read_json(hooks)["custom"])
            self.assertEqual(len(read_json(hooks)["hooks"]["PreToolUse"]), 1)

    def test_unmanaged_skill_preserved_until_explicit_replace(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            skill = home / ".agents/skills/build/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("custom skill")
            with self.assertRaises(Error):
                install(["codex"], home)
            self.assertEqual(skill.read_text(), "custom skill")
            install(["codex"], home, replace=True)
            uninstall(home)
            self.assertEqual(skill.read_text(), "custom skill")

    def test_modified_installed_file_survives_uninstall(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            install(["codex"], home)
            skill = home / ".agents/skills/build/SKILL.md"
            skill.write_text("local edit")
            result = uninstall(home)
            self.assertEqual(skill.read_text(), "local edit")
            self.assertIn(str(skill), result["preserved_modified_files"])

    def test_existing_identical_file_is_restored_on_uninstall(self):
        from aek.install import SOURCE

        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            skill = home / ".agents/skills/build/SKILL.md"
            skill.parent.mkdir(parents=True)
            original = (SOURCE / "skills/build/SKILL.md").read_bytes()
            skill.write_bytes(original)
            install(["codex"], home)
            uninstall(home)
            self.assertEqual(skill.read_bytes(), original)

    def test_existing_instructions_remain_after_uninstall(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            file = home / ".codex/AGENTS.md"
            file.parent.mkdir()
            file.write_text("My project instructions.\n")
            install(["codex"], home)
            install(["codex"], home)
            self.assertEqual(file.read_text().count("AEK:BEGIN"), 1)
            uninstall(home)
            self.assertIn("My project instructions.", file.read_text())
            self.assertNotIn("AEK:BEGIN", file.read_text())

    def test_invalid_hook_config_fails_before_runtime_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            hooks = home / ".codex/hooks.json"
            hooks.parent.mkdir()
            hooks.write_text("invalid JSON")
            with self.assertRaises(Error):
                install(["codex"], home)
            self.assertFalse((home / ".local/share/aek").exists())

    def test_legacy_migration_changes_only_owned_global_hooks(self):
        from aek.install import migrate_legacy

        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            hook = home / ".local/share/harness-lock/.githooks/pre-commit"
            hook.parent.mkdir(parents=True)
            hook.write_text("ALLOW_TEST_EDITS=1")
            config = home / "gitconfig"
            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": str(config), "GIT_CONFIG_NOSYSTEM": "1"},
            ):
                run(["git", "config", "--global", "core.hooksPath", str(hook.parent)])
                self.assertTrue(migrate_legacy(home)["git_changed"])
                run(["git", "config", "--global", "core.hooksPath", "/unrelated/hooks"])
                self.assertFalse(migrate_legacy(home)["git_changed"])
                self.assertEqual(
                    run(["git", "config", "--global", "--get", "core.hooksPath"])
                    .stdout.decode()
                    .strip(),
                    "/unrelated/hooks",
                )


class ControllerTests(RepoCase):
    def lifecycle_api(self, followers=(), marker_body=""):
        calls = []
        base = self.base

        class Fake:
            def pages(inner, endpoint):
                return list(followers)

            def api(inner, endpoint, method="GET", body=None):
                calls.append((endpoint, method, body))
                if "/check-runs?" in endpoint:
                    return {
                        "check_runs": [
                            {"id": 22, "name": "aek/verification", "app": {"id": 999}},
                            {"id": 23, "name": "aek/verification", "app": {"id": 456}},
                        ]
                    }
                if "/check-runs/" in endpoint:
                    return body
                if "/pulls/" in endpoint:
                    return {
                        "number": 7,
                        "state": "open",
                        "body": marker_body,
                        "head": {"sha": base},
                        "base": {
                            "ref": "trunk",
                            "repo": {"full_name": "owner/project"},
                        },
                    }
                raise AssertionError(endpoint)

        return Fake(), calls

    def test_failed_preparation_revokes_previous_success_only_for_designated_app(self):
        from aek.ci import prepare

        api, calls = self.lifecycle_api()
        with patch("aek.ci.GitHub", return_value=api), patch("aek.ci.protection"):
            with self.assertRaisesRegex(Error, "reference an approved proposal"):
                prepare(
                    self.root,
                    {"repository": {"full_name": "owner/project"}},
                    candidate_pr=7,
                )
        updates = [(url, body) for url, method, body in calls if method == "PATCH"]
        self.assertEqual(len(updates), 1)
        self.assertTrue(updates[0][0].endswith("/23"))
        self.assertEqual(updates[0][1]["conclusion"], "failure")
        self.assertTrue(updates[0][1]["external_id"])

    def test_proposal_review_event_invalidates_dependent_implementation(self):
        from aek.ci import prepare

        follower_sha = "b" * 40
        api, calls = self.lifecycle_api(
            [{"number": 9, "body": "AEK-PROPOSAL: 7", "head": {"sha": follower_sha}}]
        )
        event = {
            "repository": {"full_name": "owner/project"},
            "workflow_run": {
                "name": "AEK request",
                "event": "pull_request_review",
                "pull_requests": [{"number": 7}],
            },
        }
        with patch("aek.ci.GitHub", return_value=api), patch("aek.ci.protection"):
            with self.assertRaisesRegex(
                Error, "Dependent implementation checks invalidated"
            ):
                prepare(self.root, event)
        self.assertTrue(any(follower_sha in url for url, method, body in calls))
        self.assertEqual(sum(method == "PATCH" for url, method, body in calls), 2)

    def test_superseded_worker_cannot_overwrite_newer_check(self):
        plan, report = self.plan_report()
        plan.update(check_run_id=321, verification_request="older")
        api = self.github()
        original = api.api

        def query(endpoint, method="GET", body=None):
            if endpoint.endswith("/check-runs/321"):
                self.assertEqual(method, "GET")
                return {"external_id": "newer"}
            return original(endpoint, method, body)

        api.api = query
        with patch("aek.ci.GitHub", return_value=api):
            with self.assertRaisesRegex(Error, "superseded"):
                publish(plan, report, "success")

    def test_removed_proposal_reference_prevents_success(self):
        plan, report = self.plan_report()
        api = self.github()
        original = api.api

        def query(endpoint, method="GET", body=None):
            result = original(endpoint, method, body)
            if "/pulls/" in endpoint:
                result["body"] = ""
            return result

        api.api = query
        with patch("aek.ci.GitHub", return_value=api):
            self.assertEqual(publish(plan, report, "success")["conclusion"], "failure")

    def test_edited_live_approval_marker_cannot_pass(self):
        plan, report = self.plan_report()
        records = self.github().pages("")
        records[0]["body"] = "No longer approving the frozen snapshot"
        with patch("aek.ci.GitHub", return_value=self.github(reviews=records)):
            self.assertEqual(publish(plan, report, "success")["conclusion"], "failure")

    def test_candidate_container_has_readonly_harness_and_no_authority_mount(self):
        from aek.ci import container_checks
        from types import SimpleNamespace

        captured = []

        def docker(argv, **kwargs):
            captured.append(argv)
            return SimpleNamespace(returncode=0, stdout=b"passed", stderr=b"")

        with (
            patch("aek.ci.run", side_effect=docker),
            patch.object(os, "getuid", return_value=1000, create=True),
            patch.object(os, "getgid", return_value=1000, create=True),
        ):
            result = container_checks(
                self.root,
                self.config["checks"],
                self.config["github"]["verification_image"],
                self.config,
            )
        self.assertEqual(result[0]["status"], "passed")
        command = captured[0]
        mounts = [
            command[i + 1] for i, value in enumerate(command) if value == "--mount"
        ]
        self.assertTrue(any("dst=/work/.git,readonly" in m for m in mounts))
        self.assertTrue(any("dst=/work/tests,readonly" in m for m in mounts))
        self.assertTrue(any("dst=/work/.aek,readonly" in m for m in mounts))
        self.assertTrue(
            all("/var/run/docker.sock" not in m and ".codex" not in m for m in mounts)
        )
        self.assertIn("--network=none", command)
        self.assertIn("PYTHONPATH=/work/src:/work", command)
        self.assertEqual(command[command.index("--user") + 1], "1000:1000")

    def plan_report(self):
        plan = {
            "repository": "owner/project",
            "candidate_pr": 7,
            "candidate": self.base,
            "integration": self.base,
            "base": self.base,
            "config": self.config,
            "approval": self.approval,
        }
        report = {
            "passed": True,
            "candidate": self.base,
            "integration": self.base,
            "base": self.base,
            "harness_digest": digest(self.approval["snapshot"]),
            "checks": [{"name": "tests", "status": "passed"}],
        }
        return plan, report

    def test_aggregate_success_requires_all_checks(self):
        plan, report = self.plan_report()
        with patch("aek.ci.GitHub", return_value=self.github()):
            self.assertEqual(publish(plan, report, "success")["conclusion"], "success")
            for status in ["skipped", "timeout", "failed", "cancelled"]:
                report["checks"][0]["status"] = status
                self.assertEqual(
                    publish(plan, report, "success")["conclusion"], "failure"
                )

    def test_missing_report_or_failed_job_cannot_pass(self):
        plan, report = self.plan_report()
        with patch("aek.ci.GitHub", return_value=self.github()):
            self.assertEqual(publish(plan, {}, "success")["conclusion"], "failure")
            self.assertEqual(publish(plan, report, "failure")["conclusion"], "failure")

    def test_stale_commit_report_cannot_pass(self):
        plan, report = self.plan_report()
        report["candidate"] = "f" * 40
        with patch("aek.ci.GitHub", return_value=self.github()):
            self.assertEqual(publish(plan, report, "success")["conclusion"], "failure")

    def test_review_revocation_cannot_pass(self):
        plan, report = self.plan_report()
        records = self.github().pages("")
        records[0]["state"] = "DISMISSED"
        with patch("aek.ci.GitHub", return_value=self.github(reviews=records)):
            self.assertEqual(publish(plan, report, "success")["conclusion"], "failure")

    def test_later_change_request_cannot_pass(self):
        plan, report = self.plan_report()
        records = self.github().pages("")
        records.append(dict(records[0], id=100, state="CHANGES_REQUESTED"))
        with patch("aek.ci.GitHub", return_value=self.github(reviews=records)):
            self.assertEqual(publish(plan, report, "success")["conclusion"], "failure")

    def test_trusted_controller_assembles_real_integration_commit(self):
        from aek.ci import prepare

        git(self.root, "switch", "-c", "codex/proposal")
        git(self.root, "commit", "--quiet", "--allow-empty", "-m", "baseline proposal")
        proposal_sha = commit(self.root)
        git(self.root, "switch", "-c", "codex/feature")
        self.write("source.py", "value = 5\n")
        feature_sha = self.save()
        git(self.root, "switch", "trunk")
        self.write("other.py", "other = True\n")
        base_sha = self.save()
        review = {
            "id": 99,
            "user": {"id": 123, "type": "User"},
            "state": "APPROVED",
            "commit_id": proposal_sha,
            "body": marker(self.root, proposal_sha, self.base, self.config),
        }

        class Fake:
            def repository(inner, config):
                return {"default_branch": "trunk"}

            def pages(inner, endpoint):
                return [review]

            def api(inner, endpoint, method="GET", body=None):
                if "/check-runs?" in endpoint:
                    return {"check_runs": []}
                if endpoint.endswith("/check-runs"):
                    return {"id": 321}
                if endpoint.endswith("/protection"):
                    return {
                        "required_status_checks": {
                            "strict": True,
                            "checks": [{"context": "aek/verification", "app_id": 456}],
                        },
                        "enforce_admins": {"enabled": True},
                    }
                if endpoint.endswith("/environments/aek-authority"):
                    return {
                        "deployment_branch_policy": {
                            "custom_branch_policies": True,
                            "protected_branches": False,
                        }
                    }
                if "/deployment-branch-policies" in endpoint:
                    return {
                        "total_count": 1,
                        "branch_policies": [{"name": "trunk", "type": "branch"}],
                    }
                number = int(endpoint.rsplit("/", 1)[1])
                return {
                    "state": "open",
                    "merged": False,
                    "body": "AEK-PROPOSAL: 7",
                    "head": {"sha": proposal_sha if number == 7 else feature_sha},
                    "base": {"ref": "trunk", "repo": {"full_name": "owner/project"}},
                }

        def intercepted(root, config, operation, *args):
            return git(root, "update-ref", "refs/aek/candidate", feature_sha)

        event = {
            "repository": {"full_name": "owner/project"},
            "inputs": {"candidate_pr": "9", "proposal_pr": "7"},
        }
        with (
            patch("aek.ci.GitHub", return_value=Fake()),
            patch("aek.ci.fetch", return_value=base_sha),
            patch("aek.ci.transport", side_effect=intercepted),
        ):
            plan = prepare(self.root, event)
        self.assertNotEqual(plan["integration"], feature_sha)
        self.assertEqual(
            policy.tree(self.root, plan["integration"], self.config),
            plan["approval"]["snapshot"]["files"],
        )
        self.assertEqual(
            git(self.root, "show", plan["integration"] + ":source.py").stdout,
            b"value = 5\n",
        )
        self.assertEqual(
            git(self.root, "show", plan["integration"] + ":other.py").stdout,
            b"other = True\n",
        )

    def test_spoofed_app_cannot_satisfy_protection(self):
        class Fake:
            def repository(inner, config):
                return {"default_branch": "trunk"}

            def api(inner, endpoint):
                return {
                    "required_status_checks": {
                        "strict": True,
                        "checks": [{"context": "aek/verification", "app_id": 999}],
                    },
                    "enforce_admins": {"enabled": True},
                }

        with self.assertRaises(Error):
            protection(self.config, Fake())

    def test_unrestricted_authority_environment_cannot_satisfy_protection(self):
        class Fake:
            def repository(inner, config):
                return {"default_branch": "trunk"}

            def api(inner, endpoint):
                if endpoint.endswith("/protection"):
                    return {
                        "required_status_checks": {
                            "strict": True,
                            "checks": [{"context": "aek/verification", "app_id": 456}],
                        },
                        "enforce_admins": {"enabled": True},
                    }
                return {"deployment_branch_policy": None}

        with self.assertRaisesRegex(Error, "aek-authority"):
            protection(self.config, Fake())


class RunnerProfiles(unittest.TestCase):
    def fixture(self, ecosystem, files):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, contents in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents)
            config = policy.discover(root, "owner/project", [123])
            self.assertIn(ecosystem, config["profiles"])
            policy.validate(config)
            results = execute(root, config["checks"])
            self.assertTrue(all(r["status"] == "passed" for r in results), results)

    def require(self, executable):
        if not shutil.which(executable):
            if os.environ.get("AEK_REQUIRE_PROFILES") == "1":
                self.fail(f"Missing required CI profile runtime: {executable}")
            self.skipTest(f"{executable} unavailable locally; CI requires it")

    def test_python(self):
        self.require("pytest")
        self.fixture(
            "python",
            {
                "pyproject.toml": "[tool.pytest.ini_options]\n",
                "tests/test_sum.py": "def test_sum():\n assert sum([1,2]) == 3\n",
            },
        )

    def test_javascript(self):
        self.require("npm")
        self.fixture(
            "javascript",
            {
                "package.json": '{"scripts":{"test":"node --test"}}',
                "math.test.js": "const {test} = require('node:test'); const assert = require('node:assert'); test('sum', () => assert.equal(1+2,3));",
            },
        )

    def test_go(self):
        self.require("go")
        self.fixture(
            "go",
            {
                "go.mod": "module fixture\n\ngo 1.22\n",
                "sum.go": "package fixture\nfunc Sum(a,b int) int { return a+b }\n",
                "sum_test.go": 'package fixture\nimport "testing"\nfunc TestSum(t *testing.T) { if Sum(1,2)!=3 { t.Fatal("wrong") } }\n',
            },
        )

    def test_rust(self):
        self.require("cargo")
        self.fixture(
            "rust",
            {
                "Cargo.toml": '[package]\nname="fixture"\nversion="0.1.0"\nedition="2021"\n',
                "Cargo.lock": '# fixture\nversion = 3\n[[package]]\nname="fixture"\nversion="0.1.0"\n',
                "src/lib.rs": "#[test]\nfn sum() { assert_eq!(1+2,3); }\n",
            },
        )


if __name__ == "__main__":
    unittest.main()
