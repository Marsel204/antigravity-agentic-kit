# Antigravity Agentic Engineering Kit

> High-discipline Software Development Life Cycle (SDLC) skills, TDD enforcement, token-efficient action formatting, interactive architecture generation (`archify`), large-codebase context sandboxing (`context-mode`), persistent knowledge-graph memory, and parallel Git worktree management for **Google Antigravity**.

---

## 🚀 One-Line Installation (Any Device)

On any machine running Antigravity (Arch / Omarchy, Ubuntu, Debian, Fedora, macOS, or NVIDIA Jetson):

```bash
git clone https://github.com/Marsel204/antigravity-agentic-kit.git ~/.antigravity-agentic-kit
~/.antigravity-agentic-kit/install.sh
```

---

## 📦 What's Included

### 1. Slash Command Skills (`~/.gemini/config/skills/`)
Directly accessible in the Antigravity chat input via `/`:

| Command | Phase | Core Action |
| :--- | :--- | :--- |
| **`/spec`** | Specification | Analyzes contracts, edge cases, failure states, and non-blocking I/O budgets. |
| **`/plan`** | Milestone Plan | Decomposes task into ordered steps with acceptance criteria and rollback plans. |
| **`/test`** | TDD Scaffold | Scaffolds failing unit/integration tests in `tests/` *before* touching code. |
| **`/build`** | Implementation | Minimal, scoped implementation strictly turning failing tests green. |
| **`/review`** | Self-Audit | Audits git diffs for null safety, memory leaks, security, and race conditions. |
| **`/ship`** | Release Gate | Runs tests, verifies cleanliness, commits, pushes, and opens PR. |
| **`/pr`** | GitHub PR | Creates feature branch, pushes, and opens a structured PR via `gh pr create`. |
| **`/engineering-lifecycle`** | Full SDLC | Executes the end-to-end disciplined cycle (`/spec` → `/plan` → `/test` → `/build` → `/review`). |
| **`/terse-action`** | Format Style | Strips conversational filler; enforces numbered steps, time estimates, and diffs. |
| **`/archify`** | Architecture | Generates interactive, motion-enabled, explorable HTML architecture & dataflow diagrams. |
| **`/flowchart`** | Diagram | Generates clean process flowcharts, decision trees, and logic flows. |
| **`/context-mode`** | Context Shield | Sandboxes file reads and tool executions into an SQLite/FTS5 store, cutting token waste by up to 98% on large codebases. |

### 2. Global Engineering Rules (`~/.gemini/config/GEMINI.md`)
* **Test-Driven Mandate**: Prohibits touching core logic without verified test coverage.
* **Token Economy**: Guards against dumping unbounded log files or multi-megabyte datasets into LLM context.
* **Hardware & Safety Constraints**: Non-blocking serial I/O, bounded memory for edge devices (e.g. Jetson Orin Nano).

### 3. Cross-Session Memory & Context MCPs
* **`server-memory`**: Registers `@modelcontextprotocol/server-memory` to persist architectural decisions, hardware pinouts, and key constraints across restarts.
* **`context-mode`**: Registers `context-mode` to prevent context decay in multi-thousand file repositories.

### 4. Parallel Worktree Isolation (`worktrunk`)
* Automates `cargo install worktrunk` to provide the `wt` CLI.
* Allows multiple AI agents to work on separate git branches simultaneously without collisions.

---

## 🛠️ Usage Patterns

### A. Phased Feature Development
```text
/spec add emergency vehicle detection to edge_daemon
/test write failing unit tests for the emergency vehicle flag
/build implement the flag on TrafficSnapshot
/review
```

### B. Interactive System Architecture
```text
/archify map the dataflow pipeline from Kannala-Brandt lens rectifier to Sugeno ANFIS and RS-485 actuation
```

### C. Large Codebase Context Sandboxing
```text
/context-mode find all references to Modbus telemetry and summarize error handling paths
```

### D. Parallel Worktrees (Terminal)
```bash
wt switch -c new-feature-branch
wt list
wt switch main
wt merge new-feature-branch
```

---

## 🔄 Project-Specific Deployment (`.agents/`)
To bake these skills directly into a specific project (so anyone who clones the project automatically gets the skills):

```bash
cd your-project-repo
mkdir -p .agents
cp -r ~/.gemini/config/skills .agents/skills
cp ~/.gemini/config/GEMINI.md .agents/GEMINI.md
git add .agents
git commit -m "chore: add antigravity agentic skills and engineering rules"
```

---

## 📄 License
MIT © Marselinus Nugraha
