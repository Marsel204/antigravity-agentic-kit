# Impeccable source and attribution

- Author: Paul Bakaus.
- Repository: https://github.com/pbakaus/impeccable
- Revision: `2f98774f86bc05563876643db37e6c37c322850f`.
- Skill version: `4.5.2`.
- Pinned engine version: `0.1.14` (see `scripts/VERSION`).
- Distribution copied: `.agent/skills/impeccable/` (Antigravity).
- License: Apache-2.0, reproduced in [LICENSE](LICENSE).
- Upstream third-party attribution: [NOTICE.md](NOTICE.md).

The upstream skill, references, and launcher are copied without content changes. This kit adds this provenance file and preserves the upstream LICENSE and NOTICE.md. Plugin copies are generated from the canonical folder with `python scripts/sync_bundle.py`.

The launcher resolves references through its actual skill directory, so the global installation does not depend on a project-local `.agent/` folder. The engine is downloaded and checksum-verified on first use; binaries are not vendored. To update, review the upstream revision and replace the entire skill distribution, LICENSE, and NOTICE.md together, then update this record and synchronize the plugin bundle.
