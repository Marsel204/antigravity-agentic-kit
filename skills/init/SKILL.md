---
name: init
description: Initialize a software project for the Agentic Engineering Kit (AEK), preparing its starter, checks, architecture, runtime integration, reviewed enrollment, and initial baseline proposal. Use for new-project setup or adopting AEK in an existing repository.
---

# Initialize an AEK project

Turn a project idea into a working starter and a concrete AEK enrollment proposal. Carry out setup within the user's request and active harness permissions; do not give a command checklist in place of authorized work. Preserve existing agent adaptations and project conventions. Scope this skill to project setup and the initial baseline; feature requirements and implementation milestones belong to `spec` and `plan` (or a Codex-adapted `agentic-plan`) when available. Reuse existing accepted specifications and plans rather than requiring repeat invocations.

## Resolve the target

Use the project path, product idea, stack, agent selection, and GitHub destination already provided. Ask only for information that materially blocks progress. If the stack is unspecified, choose a small suitable starter and state the choice. Do not assume React, financial data, a GitHub account, or a particular Projects directory for every request.

Inspect the target and parent Git boundaries before creating files. For a new project, scaffold in its own directory. For an existing project, preserve its implementation, unrelated changes, remote, and branch; do not scaffold over it. Inspect `.aek/project.json` before changing runner, test, or architecture files. If already enrolled, load `aek context` and route protected changes through the proposal workflow instead of reinitializing policy.

## Prepare the starter

Create the minimal runnable scaffold and dependency lockfile, then configure noninteractive tests and appropriate build/type checks. For applications, add a bounded smoke check that starts the application and exercises a basic operation. Add a meaningful passing baseline test for the starter, keeping requested feature logic for the later approved test proposal.

Document module responsibilities, interfaces, and constraints in a reviewable architecture proposal. Initialize Git for a new standalone project. Commit only intended setup files when bootstrap includes committing; preserve any unrelated staged content. Create a GitHub repository or push only when publishing is authorized and the destination and visibility are known. Missing remote setup should not prevent finishing the local starter.

Run the declared starter checks and inspect their results. Resolve setup errors before proposing them as a baseline; an empty test suite is not a passing baseline.

## Prepare AEK

Read [AEK setup](references/aek-setup.md) for installation, enrollment, activation, and authority details. Inspect `aek --help`, installed provenance, and the applicable kit docs rather than assuming a specific version. If AEK installation is needed for the requested setup, prepare and validate a reviewed source bundle, reconcile existing skill collisions, then install the requested integrations. Use the current agent as the default; install both only when requested. Preserve local adaptations and back up replaced files. Avoid silently treating an upstream install with `--replace` as a migration.

Separate device integration from repository enrollment. Hooks require live activation validation; installation and local check success cannot establish GitHub enforcement.

## Prepare enrollment and hand off authority

Keep Graphify disabled by default. If requested, prepare its isolated installation and reviewed policy opt-in, then refresh and query only after policy approval. See the optional Graphify instructions in the setup reference.

Generate the full proposal with `aek init --human-id NUMBER` in the target repository once its GitHub destination and allowlisted human ID are established. Inspect proposed runners, protected files, ignored artifacts, architecture, modules, and GitHub fields. Use the supplied source launcher's `init` for proposal generation if device installation is blocked, clearly recording that integration remains inactive.

If authority details are unavailable, save a clearly marked setup draft outside protected paths and report the exact missing fields. Do not invent account IDs, App IDs, credentials, image digests, or approval records. Continue independent local work while awaiting needed input.

Present the concrete enrollment configuration and its effects before requesting acceptance. Apply `init --accept ... --ci` only after the reviewed proposal has been accepted. Prepare owner bootstrap files and exact remaining GitHub actions. Run `aek doctor --online` when credentials permit; inspect its reported status even when it exits nonzero.

When setup is complete and publishing is authorized, prepare the initial baseline test proposal using `aek harness workspace` and `propose`. The human submits the exact GitHub approval marker through their separate session. Freeze only after that live approval exists. After baseline setup, hand off feature requirements and milestones to `spec` and `plan` (or `agentic-plan` in an adapted installation). Feature test proposals and implementation follow the development workflow and need their own authorized scope; an approved starter baseline does not approve future protected changes.

## Report readiness

Report the project path, launch command, checks actually run, device activation status, enrollment status, and remaining owner actions. Distinguish a working local starter, an enrollment proposal, and complete AEK enforcement. Give the next concrete action and resume from recorded state on a subsequent invocation rather than recreating the project.
