---
name: context-mode
description: Use when the context-mode MCP server is available and a task needs large outputs, logs, or many files kept out of context.
---

# Context-mode

Use the available context-mode MCP tools for large outputs, logs, or many-file analysis. Hosts may expose tools as `context-mode/ctx_execute` or `mcp__context-mode__ctx_execute`; discover the actual names and schemas before calling them.

## Available tools

- `ctx_execute`: Run supplied code in a sandboxed subprocess and return only what it prints. With `intent`, large output is indexed and returned as searchable previews. Commands can have side effects; keep them within the authorized scope.
- `ctx_execute_file`: Load a named file into `FILE_CONTENT` and execute code over it, returning only printed results. Use direct bounded reads when editing or needing a known small range.
- `ctx_batch_execute`: Run labeled commands, index their output, and return matches for supplied queries in one call. Keep concurrency at 1 for CPU-bound or shared-state commands.
- `ctx_index`: Store supplied content or a file in a searchable BM25/FTS5 knowledge base, preserving raw chunks for retrieval. It does not recursively index a directory.
- `ctx_search`: Retrieve ranked sections from indexed content and session memory. Relevance mode searches the current session; timeline mode spans current/prior sessions and persistent auto-memory. Capture unindexed data first.
- `ctx_stats`: Report current-session context consumption, tool call counts, estimated token usage, and savings.
- `ctx_fetch_and_index`: Fetch URL content over HTTP, convert HTML to Markdown, index JSON by key paths or plain text directly, and return previews. Supports cached and batched fetches; cannot render JavaScript-only pages.
- `ctx_insight`: Open the hosted Insight dashboard in the default browser. This is a dashboard launcher, not routine analysis or a Q&A tool; use `ctx_search` for indexed questions.
- `ctx_doctor`: Diagnose the context-mode installation and return a status report.
- `ctx_upgrade`: Return a shell command for upgrading context-mode. Do not invoke the upgrade workflow or run its returned command unless the user asks for an upgrade.
- `ctx_purge`: Permanently delete indexed/session data. Use only on explicit user request with an unambiguous session or project scope and `confirm: true`. Ask for scope if unclear; never purge merely to save context or improve performance.

## Bounded analysis and fallback

Derive counts, matches, and summaries in code rather than dumping full files or logs. If the context-mode MCP server is unavailable, use bounded shell reads with `rg`, `head`, `sed -n`, and `wc`, then summarize the relevant findings.
