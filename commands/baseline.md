---
name: baseline
description: Establish the honest signal and record the starting point before any change.
---

# /baseline — define "better" and measure where you stand

Use at the very start of a task, before editing anything. You cannot improve what you
can't measure.

**Do this:**

1. **Check for a direction file.** If the repo has a human-owned direction/spec file
   (the objective, the signal, the guardrails, the budget), read it and treat it as
   read-only law. If there isn't one and the goal is non-trivial, propose one and ask the
   human to set direction rather than inventing the objective yourself.
2. **Name the signal.** In one line, state how a change will be judged better: a specific
   test, a benchmark number, a lint/type check, or a runnable assertion. If several
   qualities matter (correctness, speed, memory, size, readability), list them — track
   more than one so you don't silently regress one while chasing another.
3. **Find or build the cheapest scorer.** Locate the repo's existing test/benchmark/lint
   command. If none scores the behavior you're about to touch, write the smallest honest
   harness that runs it on representative inputs and prints a number plus any errors.
4. **Keep the ruler separate.** The scorer must live outside the code it measures and stay
   effectively read-only — so the code being optimized can never quietly rewrite its own
   grader.
5. **Record the baseline.** Ensure a clean git tree (commit or stash), run the scorer, and
   write down the starting number(s). HEAD is now your best-known state.
6. **Report** the signal and the baseline, and confirm they look right before iterating.
