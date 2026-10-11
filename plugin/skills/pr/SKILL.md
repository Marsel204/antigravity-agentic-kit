---
name: pr
description: Create a reviewable pull request using the project's publishing policy and include current verification evidence.
---

# Pull request

In an AEK-enrolled project, publish through `aek ship` after an exact-commit review and independently approved harness verification. Use a separate test-proposal PR for harness authoring. Publishing uses the configured restricted agent identity and opens a draft; do not bypass its checks by calling GitHub directly with human credentials.

In unenrolled projects, follow their existing checks and publishing conventions. Inspect the final diff, include relevant validation and limitations, and create a PR only when publishing is authorized. Keep multiline bodies in a temporary file and pass `--body-file` to `gh`.

Return the created PR link. Do not merge or deploy unless separately requested.
