# Design artifacts

Use these prompts and templates selectively. Follow existing project documentation conventions, omit irrelevant fields, and avoid generating a document for every small edit.

## Product or redesign brief

The brief provides enough direction to research references. It is not the final screen specification.

```markdown
# UI brief

Mode: New UI / redesign / focused improvement
Product:
Audience and usage context:
Primary task and desired outcome:
Essential scope and exclusions:
Primary user flow:
Technical, content, and device constraints:
Design intent and supplied references:

For redesigns:
Observed problems and their user impact:
Successful patterns and behavior to preserve:
Permitted navigation or interaction changes:

Confirmed requirements:
Assumptions:
Material open questions:
```

Ask about missing facts that would change the next decision. Useful questions include the main task, highest-priority screens, redesign success criteria, and which existing flows must remain intact. Do not repeat questions answered by the request or project evidence.

## Reference notes

Record relevant findings, not a gallery of unrelated attractive sites. URLs and images may serve different parts of the direction.

| Source or existing screen | Pattern and evidence | Why it fits | Adaptation or exclusion |
| --- | --- | --- | --- |
| Link / screenshot / route | Specific observed structure or treatment | Connection to a task or constraint | What to reuse, change, or avoid |

Keep facts separate from inference. A homepage screenshot cannot verify a complete navigation flow, keyboard behavior, or mobile layout. Document access limitations and avoid extrapolating unobserved behavior.

Summarize the selected direction and the design decisions it supports. List unresolved conflicts between references rather than mixing incompatible patterns indiscriminately.

## UI specification checklist

Pass these findings into the existing `spec` workflow when available. This checklist supplements its engineering requirements.

- **Scope and behavior:** requested surfaces, exclusions, appearance changes, behavior changes, and preserved flows.
- **Screens and navigation:** routes, information hierarchy, primary actions, entry/exit points, and back navigation.
- **Flows and interactions:** primary path, forms and validation, action feedback, recovery, and alternate paths that matter.
- **Components and tokens:** reuse versus changes, typography, semantic colors, spacing, density, component variants, and necessary shared-component updates.
- **States and content:** loading, empty, error, success, disabled, focus, selected, and destructive-action states where relevant; realistic data volume, long text, and overflow.
- **Responsive behavior:** stacking, navigation adaptation, table behavior, touch targets, and representative viewport checks suited to the actual users.
- **Accessibility:** semantic structure, accessible names, keyboard operation, visible focus, contrast, and reduced-motion behavior where relevant.
- **Motion and media, if used:** purpose, triggers, fallback, loading behavior, and performance implications.
- **Acceptance evidence:** observable outcomes, key flow checks, screenshots or browser inspection, and relevant repository checks.
- **Architecture and integration:** stack constraints, component boundaries, data connections, and proposals required by the project's engineering workflow.

Write criteria as user-observable outcomes, for example:

- A user can create an invoice through the existing save flow; the redesigned editor preserves required fields and validation.
- On the agreed mobile viewport, invoice actions remain reachable without clipped controls or page-level horizontal overflow.
- An empty invoice list explains the state and offers the primary create action.
- Keyboard users can reach the filters and row actions, see focus, and dismiss an open menu.

Avoid acceptance criteria that merely assert the presence of a CSS class or repeat implementation details.

## Prototype comparison and completion evidence

For variants, compare the same representative task and content. Judge hierarchy, readability, density, brand fit, consistency, responsiveness, and implementation cost. Record the chosen direction and rationale; carry decisions into the specification.

Before delivery, distinguish:

- What was implemented and visually inspected.
- Which flows and automated checks passed.
- Which states, devices, integrations, or interactions remain unverified.
- Whether implementation review was self-review or an explicitly requested independent review.

Screenshots support appearance checks, not proof of working interactions. Design critique supports visual quality, not proof of implementation correctness.
