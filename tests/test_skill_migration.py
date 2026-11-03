from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aek.common import Error, read_json, run
from aek.install import SOURCE, install, uninstall


class SkillMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aek-skill-migration-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.old = self.source("old", ["spec", "build", "pr"])
        self.new = self.source("new", ["implement", "tdd", "pr", "aek-workflow"])

    def install_old(self, adapters):
        install(adapters, self.home, source=self.old)
        path = self.home / ".local/share/aek-installation.json"
        manifest = read_json(path)
        manifest.pop("skill_layouts", None)
        path.write_text(json.dumps(manifest))

    def source(self, name, skills):
        source = self.root / name
        for folder in ["src", "scripts", "templates"]:
            shutil.copytree(SOURCE / folder, source / folder,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for skill in skills:
            path = source / "skills" / skill / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(f"---\nname: {skill}\ndescription: {name} fixture\n---\n{name}\n")
        return source

    def test_upgrade_archives_modified_owned_skills_and_is_repeatable(self):
        self.install_old(["codex", "antigravity"])
        legacy = self.home / ".agents/skills/spec"
        (legacy / "SKILL.md").write_text("locally adapted AEK specification")
        (legacy / "notes.txt").write_text("local additions")
        pr = self.home / ".agents/skills/pr/SKILL.md"
        pr.write_text("locally adapted AEK PR skill")
        specialist = self.home / ".agents/skills/embedded-micro/SKILL.md"
        specialist.parent.mkdir()
        specialist.write_text("keep my firmware skill")
        result = install(["codex", "antigravity"], self.home,
                         source=self.new, migrate_skills=True)
        self.assertFalse(legacy.exists())
        archives = {entry["path"]: Path(entry["backup"])
                    for entry in result["skill_migration"]["retired"]}
        self.assertEqual((archives[str(legacy)] / "notes.txt").read_text(), "local additions")
        self.assertEqual((archives[str(legacy)] / "SKILL.md").read_text(),
                         "locally adapted AEK specification")
        self.assertEqual(pr.read_bytes(), (self.new / "skills/pr/SKILL.md").read_bytes())
        saved_files = read_json(Path(result["backup"]) / "file-backups.json")
        self.assertEqual(Path(saved_files[str(pr)]).read_text(), "locally adapted AEK PR skill")
        self.assertEqual(specialist.read_text(), "keep my firmware skill")
        for directory in [".agents/skills", ".gemini/config/skills", ".local/share/aek/skills"]:
            self.assertFalse((self.home / directory / "build").exists())
            self.assertTrue((self.home / directory / "implement/SKILL.md").is_file())
        manifest = read_json(self.home / ".local/share/aek-installation.json")
        self.assertFalse(any("/skills/spec/" in p for p in manifest["files"]))
        repeated = install(["codex", "antigravity"], self.home,
                           source=self.new, migrate_skills=True)
        self.assertEqual(repeated["skill_migration"]["retired"], [])
        uninstall(self.home)
        self.assertEqual(specialist.read_text(), "keep my firmware skill")
        self.assertTrue(archives[str(legacy)].exists())

    def test_old_layout_requires_explicit_migration_before_any_changes(self):
        self.install_old(["codex"])
        manifest = self.home / ".local/share/aek-installation.json"
        previous = manifest.read_bytes()
        with self.assertRaisesRegex(Error, "migrate-skills"):
            install(["codex"], self.home, source=self.new)
        self.assertEqual(manifest.read_bytes(), previous)
        self.assertTrue((self.home / ".agents/skills/spec/SKILL.md").is_file())
        self.assertFalse((self.home / ".agents/skills/tdd").exists())

    def test_unmanaged_alias_is_retired_only_with_aek_provenance(self):
        alias = self.home / ".codex/skills/agentic-plan/SKILL.md"
        alias.parent.mkdir(parents=True)
        alias.write_text("---\nname: agentic-plan\nmetadata:\n"
                         "  source-repository: https://github.com/Marsel204/antigravity-agentic-kit\n"
                         "---\nmy adaptation\n")
        foreign = self.home / ".agents/skills/plan/SKILL.md"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("my unrelated planning skill")
        result = install(["codex"], self.home, source=self.new, migrate_skills=True)
        self.assertFalse(alias.exists())
        self.assertEqual(foreign.read_text(), "my unrelated planning skill")
        self.assertIn(str(foreign.parent), result["skill_migration"]["preserved"])

    def test_collision_is_detected_before_retiring_any_skill(self):
        self.install_old(["codex"])
        foreign = self.home / ".agents/skills/tdd/SKILL.md"
        foreign.parent.mkdir()
        foreign.write_text("custom TDD")
        with self.assertRaisesRegex(Error, "modified/unmanaged"):
            install(["codex"], self.home, source=self.new, migrate_skills=True)
        self.assertEqual(foreign.read_text(), "custom TDD")
        self.assertTrue((self.home / ".agents/skills/spec/SKILL.md").is_file())

    def test_source_cli_exposes_repeatable_migration_command(self):
        self.install_old(["codex"])
        result = run([sys.executable, SOURCE / "scripts/aek.py", "--json", "update",
                      "--home", self.home, "--source", self.new,
                      "--agent", "codex", "--migrate-skills"])
        self.assertTrue(json.loads(result.stdout)["skill_migration"]["retired"])
        self.assertFalse((self.home / ".agents/skills/spec").exists())

    def test_aek_repository_mentioned_only_in_body_does_not_claim_ownership(self):
        foreign = self.home / ".codex/skills/agentic-plan/SKILL.md"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("---\nname: agentic-plan\ndescription: custom\n---\n"
                           "  source-repository: https://github.com/Marsel204/antigravity-agentic-kit\n")
        result = install(["codex"], self.home, source=self.new, migrate_skills=True)
        self.assertTrue(foreign.exists())
        self.assertIn(str(foreign.parent), result["skill_migration"]["preserved"])

    def test_unmanifested_legacy_pr_copy_is_archived_from_old_codex_root(self):
        legacy = self.home / ".codex/skills/pr/SKILL.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("---\nname: pr\nmetadata:\n"
                          "  source-repository: https://github.com/Marsel204/antigravity-agentic-kit\n"
                          "---\nlegacy PR publisher\n")
        result = install(["codex"], self.home, source=self.new, migrate_skills=True)
        self.assertFalse(legacy.exists())
        archived = {entry["path"]: entry["backup"]
                    for entry in result["skill_migration"]["retired"]}
        self.assertEqual((Path(archived[str(legacy.parent)]) / "SKILL.md").read_text(),
                         "---\nname: pr\nmetadata:\n"
                         "  source-repository: https://github.com/Marsel204/antigravity-agentic-kit\n"
                         "---\nlegacy PR publisher\n")

    def test_actual_bundle_installs_supporting_resources_and_aek_controls(self):
        install(["codex", "antigravity"], self.home)
        for base in [".agents/skills", ".gemini/config/skills", ".local/share/aek/skills"]:
            directory = self.home / base
            for name in ["grill-with-docs", "grilling", "domain-modeling", "codebase-design",
                         "to-spec", "to-tickets", "tdd", "implement", "code-review", "pr",
                         "setup-matt-pocock-skills"]:
                self.assertTrue((directory / name / "SKILL.md").is_file())
                self.assertTrue((directory / name / "LICENSE").is_file())
                self.assertTrue((directory / name / "UPSTREAM.md").is_file())
            for name in ["aek-init", "aek-workflow", "aek-harness", "aek-verify", "aek-ship"]:
                self.assertTrue((directory / name / "SKILL.md").is_file())
            self.assertTrue((directory / "tdd/mocking.md").is_file())
            self.assertTrue((directory / "aek-init/references/aek-setup.md").is_file())
            self.assertFalse((directory / "engineering-lifecycle").exists())
            self.assertFalse((directory / "build").exists())

    def test_selected_adapter_leaves_other_adapter_skills_untouched(self):
        self.install_old(["codex", "antigravity"])
        other = self.home / ".gemini/config/skills/spec/SKILL.md"
        install(["codex"], self.home, source=self.new, migrate_skills=True)
        self.assertTrue(other.exists())
        install(["antigravity"], self.home, source=self.new, migrate_skills=True)
        self.assertFalse(other.exists())

    def test_migration_does_not_overwrite_later_edits_to_replacement_pr(self):
        install(["codex"], self.home, source=self.new, migrate_skills=True)
        pr = self.home / ".agents/skills/pr/SKILL.md"
        pr.write_text("my changes to the replacement PR skill")
        with self.assertRaisesRegex(Error, "modified/unmanaged"):
            install(["codex"], self.home, source=self.new, migrate_skills=True)
        self.assertEqual(pr.read_text(), "my changes to the replacement PR skill")

    def test_retirement_preserves_symlinked_skill_directories(self):
        target = self.root / "external"
        target.mkdir()
        (target / "SKILL.md").write_text("external planning skill")
        alias = self.home / ".agents/skills/plan"
        alias.parent.mkdir(parents=True)
        try:
            alias.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation unavailable")
        result = install(["codex"], self.home, source=self.new, migrate_skills=True)
        self.assertTrue(alias.is_symlink())
        self.assertIn(str(alias), result["skill_migration"]["preserved"])
        self.assertEqual((target / "SKILL.md").read_text(), "external planning skill")


class BundlePruningTests(unittest.TestCase):
    def test_sync_removes_orphaned_alias_without_deleting_its_target(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "scripts/sync_bundle.py"
            script.parent.mkdir()
            shutil.copy2(SOURCE / "scripts/sync_bundle.py", script)
            target = root / "plugin/skills/debug"
            target.mkdir(parents=True)
            (target / "SKILL.md").write_text("keep debug")
            source = root / "skills/debug/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("keep debug")
            alias = target.parent / "systematic-debugging"
            try:
                alias.symlink_to("debug", target_is_directory=True)
            except OSError:
                self.skipTest("Symlink creation unavailable")
            self.assertNotEqual(run([sys.executable, script, "--check"], check=False).returncode, 0)
            run([sys.executable, script])
            self.assertFalse(alias.exists())
            self.assertEqual((target / "SKILL.md").read_text(), "keep debug")

    def test_check_detects_and_sync_removes_retired_generated_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "scripts/sync_bundle.py"
            script.parent.mkdir()
            shutil.copy2(SOURCE / "scripts/sync_bundle.py", script)
            current = root / "skills/implement/SKILL.md"
            current.parent.mkdir(parents=True)
            current.write_text("current")
            stale = root / "plugin/skills/build/SKILL.md"
            stale.parent.mkdir(parents=True)
            stale.write_text("retired")
            run([sys.executable, script])
            stale.parent.mkdir(parents=True, exist_ok=True)
            stale.write_text("retired")
            result = run([sys.executable, script, "--check"], check=False)
            self.assertNotEqual(result.returncode, 0)
            run([sys.executable, script])
            self.assertFalse(stale.exists())
            self.assertEqual((root / "plugin/skills/implement/SKILL.md").read_text(), "current")
            self.assertEqual(run([sys.executable, script, "--check"]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
