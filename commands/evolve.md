---
name: evolve
description: Run the AutoEvolve loop on a task, iterate in small, verified, kept-only-if-better steps.
---

# /evolve: iterate toward a goal, one verified step at a time

Use when you have a goal in this repo (fix, feature, optimization, refactor) and want to
make real, measured progress instead of one big unverified change.

**Do this:**

1. Restate the goal in one sentence, and identify the **signal**: how will we know a
   change is better? Name the test, metric, or runnable check. If none exists, create the
   smallest honest one, and keep it separate from the code it measures.
2. **Baseline:** run the signal now and record the result. Make sure the working tree is
   clean (commit or stash) so every experiment is revertible.
3. **Loop** until the goal is met or you hit a real blocker:
   - Propose the *smallest correct change* (walk the ladder in `AGENTS.md`). One concern.
   - Verify: smoke test → correctness → (only then) size/speed/clarity. Median of a few
     runs if noisy.
   - **Keep** (commit) if it's better, *or* neutral-but-simpler, *or* a deletion, and
     still correct; else **revert** and note why.
   - Append one line to the journal: *commit · signal · keep/revert · what changed · why.*
   - Try to **simplify** the kept change further.
   - If stuck, don't stop, re-read context, combine near-misses, or try a radical
     alternative. Keep a second distinct approach alive if the problem has room.
4. **Stop** at the goal, at a genuine terminal blocker, or before anything irreversible, 
   and summarize: what changed, what the signal says now, what's next.
