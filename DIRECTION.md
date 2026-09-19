# Direction

Complete this from the user's request and existing project documentation before
editing code. Ask only for essential information that cannot be inferred.

## Outcome and evidence

- Objective: [one user-visible result]
- Success criterion: [observable behavior or measurable threshold]
- Verification command: [an actual command in this project]
- Guardrail commands: [existing tests, lint, type checks, or other required checks]
- Baseline: **not measured** — record revision, command, exit status, and result
- Known target failure: [if this is a repair, identify the expected baseline failure]
- In scope: [files, interfaces, or behavior]
- Out of scope / must preserve: [data, APIs, existing work, performance bounds]

## Limits

- Maximum attempts: **3**
- Maximum elapsed minutes, including planning and verification: **15**
- Maximum consecutive failed candidates: **2**
- Parallel candidates: **1**
- Token / cost cap: [optional; use host controls when available]
- Per-command timeout: [fit within remaining elapsed budget]

Use positive limits. Stop on verified success, any exhausted limit, required user
input, or unavailable required access/checks. Request approval before extending
limits. These are prompt instructions; configure host limits for hard enforcement.
Report unobservable usage as unavailable.

## Optional capabilities

List additional verification commands only if they exist and serve this objective.
Formal verification, fuzzing, independent audits, and parallel search are **not
configured** by this template and are not prerequisites for the default workflow.
