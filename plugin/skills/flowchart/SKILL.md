---
name: flowchart
description: Create process and logic flowcharts as inline Mermaid diagrams, with saved Mermaid and draw.io sources when requested. Route interactive, architecture, and image/video export work to archify when installed.
---

# Flowcharts

Map process steps, decisions, algorithms, and user flows with clear labels and labeled decision branches. Default to one inline Mermaid block in chat: that block is the visual. Do not print the same diagram twice.

Use `([Start / End])` for boundaries, `[/Input or Output/]` for I/O, `[Action]` for processes, `{"Decision?"}` for decisions, and `[(Storage)]` for stored data. Check node identifiers, edge targets, branch labels, and syntax before presenting the diagram.

## Saved diagrams

Write files only when the user asks to save/export or the task is repository documentation. Save Mermaid source in `docs/diagrams/<name>.mmd` in the active repository/worktree. When draw.io is wanted, also create `docs/diagrams/<name>.drawio` and return clickable file links.

Use valid uncompressed draw.io XML. Extend this minimal skeleton with the actual nodes, geometry, labels, and connections; check that every edge endpoint exists:

```xml
<mxfile host="app.diagrams.net">
  <diagram id="flow" name="Flow">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="step" value="Start" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="edge" value="Next" style="endArrow=classic;" edge="1" parent="1" source="step">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="240" y="70" as="targetPoint"/>
          </mxGeometry>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Other diagram formats

For interactive HTML diagrams, architecture diagrams, or PNG/SVG/WebM export, use the `archify` skill when installed. If unavailable, provide Mermaid or draw.io source and explain the export limitation without claiming an export was generated.
