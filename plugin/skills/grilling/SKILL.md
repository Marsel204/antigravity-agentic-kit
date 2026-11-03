---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
metadata:
  source-repository: https://github.com/mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  source-path: skills/productivity/grilling
---

Use this interview when the user requests exploration or stress-testing. Reuse decisions already settled in the conversation; an authorized implementation does not need to repeat this interview. Interview until you reach a shared understanding of the consequential decisions. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Word each question so "yes" accepts your recommended answer.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job: inspect code, tools, and documentation yourself. Do not ask the user for discoverable facts. Delegate research only when the user explicitly requests delegation; parallel agents require an explicit parallel request. Ask the user about material product or scope decisions that remain unresolved.

The session is done when the frontier is empty: the material branches are resolved and assumptions are explicit. Deliver the agreed direction. Continue implementation only when the existing task authorizes it; do not add a second approval for work already authorized.
