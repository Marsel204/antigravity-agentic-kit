---
name: code-review
description: Review committed and working changes against repository standards and the originating specification; disclose self-review and delegate only when requested.
metadata:
  source-repository: https://github.com/mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  source-path: skills/engineering/code-review
---

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

Review both axes sequentially yourself by default and disclose self-review. Use an independent reviewer only when requested; parallel reviewers require an explicit parallel request. Keep the two lenses distinct in either mode.

Use the project's tracker convention when available. An absent tracker setup does not block review; use the conversation and local specification as evidence.

## Process

### 1. Pin the fixed point

Use the fixed point supplied by the user or the task/PR context. Otherwise infer the target from the remote default branch and state it. Ask only if the base is materially ambiguous; an uncommitted-only review can use `HEAD`.

Resolve and record the merge-base with `git merge-base <fixed-point> HEAD`. Review `git diff <merge-base>` so staged and unstaged tracked work is included along with commits. Also inspect `git ls-files --others --exclude-standard` and read relevant untracked files; an untracked-only change is not an empty review. Note the commit list with `git log <fixed-point>..HEAD --oneline`. For commit-only review use `git diff <merge-base> HEAD`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the selected committed/working/untracked scope contains changes. Report an invalid base or truly empty scope before reviewing.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.), fetched via the workflow in the tracker doc.
2. A path the user passed as an argument.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. Use the accepted user request and conversation if no formal spec exists. If neither is available, report "no spec available" and review Standards without inventing requirements.

### 3. Identify the standards sources

Search the repo for every file that documents how code should be written. When `CODING_STANDARDS.md` or `CONTRIBUTING.md` exists, it must be on the list.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Review both axes

Review both axes yourself unless delegation was explicitly requested. The briefs below also define the two sequential review passes. For authorized independent review, supply raw evidence and let the reviewer assess it; do not steer it toward a conclusion. Run agents in parallel only when requested, and wait for their results before reporting.

**Standards sub-agent prompt** should include:

- The full diff command and commit list.
- The list of standards-source files you found in step 3, **plus the smell baseline from step 3** pasted in full (the sub-agent has no other access to it).
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** should include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

If no specification or accepted request is available, mark Spec unavailable and note the limitation.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings, because the two axes are deliberately separate (see _Why two axes_).

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.

For AEK-enrolled projects, load `aek-verify` to run required checks and record the review against the exact clean commit. Working-change review is useful feedback but does not establish exact-commit release evidence.
