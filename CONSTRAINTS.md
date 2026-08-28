# Active Constraints (Cumulative Evidence Store)

<!--
AutoEvolve inherits failure knowledge as first-class constraints.
When an experiment fails or is reverted, append a typed finding below.
Subsequent loops and agent sessions MUST read and satisfy these active constraints.
-->

| ID | Type | Surface | Attempted Mechanism | Failure Outcome & Root Cause | Action |
|---|---|---|---|---|---|
| C-000 | procedural | `DIRECTION.md` | Single-stage evaluation | Evaluator timeout under full suite without smoke gate | enforce-ladder |
