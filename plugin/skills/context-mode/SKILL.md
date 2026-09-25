---
name: context-mode
description: Reduce context window bloat by sandboxing tool outputs, file inspections, and command runs into a local FTS5 index. Use when exploring large codebases, reading large files, or running heavy searches.
---

# context-mode: Context & Token Optimizer for Large Codebases

Use context-mode MCP tools (`context-mode/<tool>`) to prevent context rot:

## Available Tools
* `context-mode/ctx_execute`: Run code/command in sandbox. Print only final answer.
* `context-mode/ctx_execute_file`: Read file into sandbox and extract needed lines/counts.
* `context-mode/ctx_batch_execute`: Run multiple repo commands, index output, answer follow-up queries.
* `context-mode/ctx_index`: Index a file/directory into the local FTS5 store.
* `context-mode/ctx_search`: Search indexed codebase knowledge across sessions.
* `context-mode/ctx_stats`: View context token savings and session metrics.

## Guidelines
- Never dump raw 1,000+ line logs or full files into the conversation.
- Use `ctx_execute_file` or `ctx_search` for large file analyses.
