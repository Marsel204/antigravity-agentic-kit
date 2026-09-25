---
name: flowchart
description: Create clean, verified flowcharts and process diagrams. Generates both inline GitHub-flavored Mermaid flowcharts and interactive Archify workflow diagrams for logic branching, algorithms, decision trees, and user flows.
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

## 2. Interactive Animated Flowchart (Archify Workflow)
When the user asks for an interactive, standalone HTML diagram:
- Use `/archify` with the `workflow` schema.
- Outputs self-contained HTML with step-by-step trace animations, theme switching, and pan/zoom.
