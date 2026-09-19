# Optional research procedures

The default workflow needs only the target project's existing verification tools.
AutoEvolve does not ship an SMT solver, invariant fuzzer, independent audit agent,
LATS tree search, failure graph, PRM scorer, or AST crossover engine.

Use an advanced technique only when the user requests it or existing project
tooling makes it appropriate for the stated objective. Add the actual command,
inputs, acceptance criteria, and cost to `DIRECTION.md`. Confirm it exists before
invoking it. An unavailable optional check is **not configured**, not passed.
An unavailable required check blocks completion.

For formal verification, state the modeled assumptions and properties; passing a
solver does not establish correctness outside the model. For fuzzing, record the
seed, corpus, runtime, and failure reproduction. For an independent audit, retain
the evidence and distinguish the auditor's judgment from executed checks.

Parallel candidates, tree search, and long-term lineage need explicit budgets and
isolation. Count their total cost and wall time; do not start them as an automatic
reaction to repeated failures. Start with a single candidate until a controlled
comparison demonstrates that additional search improves verified outcomes.

Keep detailed histories outside the always-loaded prompt. Read only relevant
constraints for the current task, and link to evidence rather than copying large
logs into every adapter.
