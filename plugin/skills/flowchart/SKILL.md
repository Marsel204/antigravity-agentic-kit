---
name: flowchart
description: Create clean, verified flowcharts and process diagrams. Generates both inline GitHub-flavored Mermaid flowcharts and interactive Archify workflow diagrams for logic branching, algorithms, decision trees, and user flows. Supports direct export to draw.io and JPG/PNG/SVG.
---

# /flowchart — Process & Logic Flowcharts

Use this skill whenever you need to map out execution flow, algorithms, state transitions, or decision trees.

## 1. Worktree-Aware File Placement

When asked to generate or save a flowchart, the agent MUST place files into the **current active worktree / repository**:
* **Target Directory:** `./docs/diagrams/` relative to the current working directory (`pwd`).
* **Files Generated:**
  1. `<name>.drawio` — Native draw.io XML file, directly openable in draw.io without copy-pasting.
  2. `<name>.mmd` — Plain text Mermaid source code stored cleanly on disk.
* **Why:** In Git worktrees (`wt`), saving to `./docs/diagrams/` ensures the diagram stays strictly isolated on that feature branch, ready to be committed and reviewed in your Pull Request (`/pr`) without polluting other worktrees.

## 2. In-Chat Output Standards

The agent MUST keep chat output clean and uncluttered:
1. The **Visual Mermaid diagram** rendered directly in the response for instant visual review.
2. The **Clickable file link** to the generated `./docs/diagrams/<name>.drawio` file.
* **Note:** Do NOT print duplicate raw text code blocks in the chat response. The user opens the `.drawio` file directly.

## 3. Standard Node Shapes
* `([Start / End])` — Pill shapes for boundaries.
* `[/ Input or Output /]` — Parallelograms for reading/writing variables or sensor data.
* `[Process / Action]` — Rectangles for computational steps.
* `{"Decision ?"}` — Rhombus/diamond for conditional branching.
* `[(Database / Storage)]` — Cylinders for storage.
* `-->|Yes / No|` — Labeled transition edges.

## 4. Exporting to draw.io and JPG
* **Open in draw.io:** Simply open `./docs/diagrams/<name>.drawio` directly (File → Open From → Device).
* **JPG Export:** Inside draw.io, click **File → Export as → JPEG**.
