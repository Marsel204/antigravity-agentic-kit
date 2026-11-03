"""Archive the retired skill layout without touching unrelated skill collections."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import shutil

from .common import Error, is_link, write_json

RETIRED = (
    "engineering-lifecycle", "spec", "plan", "agentic-plan", "test", "build",
    "review", "init", "verify", "ship", "systematic-debugging",
)
SOURCE_REPOSITORY = "https://github.com/Marsel204/antigravity-agentic-kit"
LAYOUT = "composable-v1"
# Known pre-migration AEK entry points identify copies predating the installer.
KNOWN_LEGACY_DIGESTS = frozenset({
    "31f05b56dadfab9dba33ecb66c9cec972a97dfdf5334f97d947131f63d071c2a",
    "4a2273d195fbba7203e1adcccef41bf2c2f9b46e8a15b70163bbe584f1ed3607",
    "6bd41052185934074c306665a2e206a94ea3b6d1e57221b2b35c52af799e21df",
    "6f7d56dda14ddcc09d812f4993f6d626d3edc6510991cd0d3f444df4ba3278a8",
    "7cd45ca4503923910c5e6ebf466c9036ca9b914d961fae549713ba9108a73b25",
    "92b97dbdc0365717418bf9cc528c460f026709b4e9e503c507467f2cc7a532a5",
    "9c95caa587c5c8a9fc006b749528c0f9e6a71114c6fdccead7b217a7a76af71a",
    "a077eedff0dca647e85de285ea282ab016427e3bd77d7c4381aa4d344358fcbe",
    "b928d8a974d4b35d308a2ab3656fd4614a35e70928bf074f4afe65b94d930f8b",
    "de335ec12ee6f77250ea268db95b113263c8e118fee8c3fdf03d8136fbbe388b",
    "f382bdf64f989b4f3e3af997c7bd5628b665e57bb6506af4d2ecd9a12980dbe4",
    "febc1d22fe52102a3997c96f9c0dbc09761ea7ac89aedd2451a4f250a86f26e5",
})


@dataclass
class Migration:
    roots: list[tuple[str, Path]]
    retired: list[tuple[str, Path]] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    replaceable: set[Path] = field(default_factory=set)


def linked(path):
    return is_link(path) or any(is_link(parent) for parent in path.parents)


def owns(directory, manifest):
    return any(
        Path(name).is_relative_to(directory) for name in manifest.get("files", {})
    )


def known_legacy(directory):
    entry = directory / "SKILL.md"
    if not entry.is_file() or linked(entry):
        return False
    content = entry.read_bytes()
    normalized = content.replace(b"\r\n", b"\n")
    parts = normalized.split(b"---", 2)
    header = (
        parts[1].splitlines()
        if normalized.startswith(b"---\n") and len(parts) == 3 else []
    )
    return (
        hashlib.sha256(normalized).hexdigest() in KNOWN_LEGACY_DIGESTS
        or f"  source-repository: {SOURCE_REPOSITORY}".encode() in header
    )


def plan(home, runtime, adapters, manifest, enabled=False):
    roots = [("runtime", runtime / "skills")]
    if "codex" in adapters:
        roots.extend([("codex", home / ".agents/skills"),
                      ("codex-legacy", home / ".codex/skills")])
    if "antigravity" in adapters:
        roots.append(("antigravity", home / ".gemini/config/skills"))
    migration = Migration(roots)
    for label, root in roots:
        names = RETIRED + (("pr",) if label == "codex-legacy" else ())
        for name in names:
            directory = root / name
            if not directory.exists() and not is_link(directory):
                continue
            if linked(directory) or not directory.is_dir():
                migration.preserved.append(str(directory))
            elif owns(directory, manifest) or known_legacy(directory):
                migration.retired.append((label, directory))
            else:
                migration.preserved.append(str(directory))
        # `pr` keeps its name but changes from an AEK publisher to a body writer.
        # Only the first migration may replace an owned, locally adapted old PR.
        pr = root / "pr"
        old_layout = manifest.get("skill_layouts", {}).get(str(root)) != LAYOUT
        if enabled and not linked(pr) and (
            known_legacy(pr) or (old_layout and owns(pr, manifest))
        ):
            migration.replaceable.add(pr)
    if migration.retired and not enabled:
        raise Error(
            "Retired AEK skills are still installed. Run the new checkout's "
            "scripts/aek.py update with --migrate-skills to archive them first."
        )
    return migration


def archive(migration, backup, manifest):
    entries = [
        {"path": str(path), "backup": str(backup / "retired-skills" / label / path.name)}
        for label, path in migration.retired
    ]
    if entries:
        # Keep a recovery map even if a later filesystem write fails.
        write_json(backup / "skill-migration.json", entries)
        write_json(backup / "installation-before.json", manifest)
    for entry in entries:
        path, destination = Path(entry["path"]), Path(entry["backup"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))
        for name in list(manifest["files"]):
            if Path(name).is_relative_to(path):
                del manifest["files"][name]
    manifest.setdefault("skill_migrations", []).extend(entries)
    for _, root in migration.roots:
        manifest.setdefault("skill_layouts", {})[str(root)] = LAYOUT
    return {"retired": entries, "preserved": migration.preserved}
