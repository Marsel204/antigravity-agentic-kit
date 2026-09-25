---
name: flowchart
description: Create clean, verified flowcharts and process diagrams. Generates both inline GitHub-flavored Mermaid flowcharts and interactive Archify workflow diagrams for logic branching, algorithms, decision trees, and user flows. Supports direct export to draw.io and JPG/PNG/SVG.
---

# /flowchart — Process & Logic Flowcharts

Use this skill whenever you need to map out execution flow, algorithms, state transitions, or decision trees.

## 1. Fast Inline Mermaid Flowchart (Default)
Generate clean, readable Mermaid syntax using appropriate node shapes:
- `([Start / End])` — Pill shapes for boundaries.
- `[Process / Action]` — Rectangles for computational steps.
- `{"Decision ?"}` — Rhombus/diamond for conditional branching.
- `[(Database / Storage)]` — Cylinders for storage.
- `-->|Yes / No|` — Labeled transition edges.

## 2. Exporting to draw.io (diagrams.net)
Mermaid flowcharts are natively editable in draw.io:
1. Open draw.io (or app.diagrams.net).
2. Click **`+` (Insert) → Advanced → Mermaid** (or Arrange → Insert → Advanced → Mermaid).
3. Paste the generated Mermaid code and click **Insert**.
4. All shapes and arrows become native, draggable, fully editable draw.io vector components.

## 3. Exporting to JPG / PNG / SVG
- **Via /archify:** Generates standalone HTML with built-in **Export → JPEG / PNG / SVG** buttons in the toolbar.
- **Via draw.io:** Once pasted in draw.io, click **File → Export as → JPEG**.
- **Via CLI:** Run `npx -y @mermaid-js/mermaid-cli -i chart.mmd -o chart.jpg`.
