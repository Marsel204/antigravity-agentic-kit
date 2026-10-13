---
name: spec
description: Inspect a project and clarify requirements, architecture constraints, edge cases, and measurable acceptance criteria before planning or implementation.
---

# Specification

Inspect the existing code and configuration first. Load `aek context` when the project is enrolled. Identify affected behavior, interfaces, modules, existing harness coverage, and approved architecture invariants. Reuse project scaffolding, architecture, and initial baseline prepared by `init`; detailed feature requirements belong here.

Clarify material ambiguities with focused questions that change scope or behavior. Discover repository facts through inspection instead of asking the user. Include concrete expected outcomes, failure modes, performance/hardware constraints when relevant, and acceptance criteria.

Present the specification for review before implementation. In enrolled projects, protected harness or architecture changes need a concrete proposal and the exact human GitHub approval. A specification or implementation request cannot substitute for that approval. Specifications should support the requested work without imposing unrelated integrations, approval gates, or external actions on unenrolled projects.
