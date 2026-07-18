---
name: autoevolve
description: >-
  An operating mindset for making changes to a codebase: work in small, verified
  steps — define an honest signal for "better", make the smallest correct change, keep
  it only if it measurably improves things (else revert), journal each experiment, and
  relentlessly simplify. Use this whenever you are fixing a bug, adding a feature,
  optimizing, refactoring, or iterating toward a target in an existing repository, and
  especially when you'll make many changes in a row or work with limited supervision.
---

# AutoEvolve — evolve the code, don't just write it

Adopt this loop for the task at hand. The full rationale lives in the repo's
[`AGENTS.md`](../../AGENTS.md); this is the actionable core.

## The loop

1. **Understand** the problem first — read the code, reproduce the bug, pin the goal.
2. **Define the signal.** Decide how you'll *measure* whether a change is better: a test,
   a metric, a runnable assertion. Make it fast and hard to game, and keep the ruler
   **separate** from the code it measures (don't let the thing being optimized rewrite
   its own scorer).
3. **Baseline.** Record the current behavior/score; make sure the tree is clean so you
   can revert.
4. **Propose the smallest correct change** — walk the ladder (below). One concern per
   change; prefer a surgical diff to a rewrite.
5. **Verify** in cascade: does it run? → is it correct? → *only then* is it smaller /
   faster / cleaner? Correctness and safety gate everything; a wrong answer is wrong no
   matter how short. If the signal is noisy, take the **median** of a few runs.
6. **Keep or revert.** Keep if it's strictly better with no regression, *or*
   neutral-but-simpler, *or* a deletion — and still correct; commit it (new best).
   Otherwise revert, and keep the lesson. A reverted experiment still made progress: it
   ruled an option out.
7. **Record** one line: *commit · signal · keep/revert · what changed · why.*
8. **Simplify** — can you get the same result with less? Deleting code is a win.
9. **Repeat**, keeping a couple of distinct working approaches alive so you don't get
   stuck. When you run out of ideas, **don't stop — think harder**: re-read the code and
   references, combine near-misses, or try a deliberately radical alternative.

## The minimalism ladder — run before writing any code

> 1. Does this need to be built at all? (YAGNI)
> 2. Does it already exist in this codebase? Reuse the helper/util/pattern.
> 3. Does the standard library already do this? Use it.
> 4. Does a native platform/language feature cover it? Use it.
> 5. Does an already-installed dependency solve it? Use it — don't add a new one.
> 6. Can this be one line? Make it one line.
> 7. Only then: write the minimum code that works.
>
> The ladder runs *after* you understand the problem. The smallest change in the wrong
> place isn't lazy — it's a second bug.

## Never be lazy about (guardrails)

Input validation at trust boundaries · error handling that prevents data loss ·
security · accessibility · anything explicitly requested · picking the edge-case-correct
option over the flimsier one. Minimalism is about the solution, never about rigor.

## Autonomy

Proceed on reversible, in-scope changes; keep going when stuck rather than asking "should
I continue?"; **pause for a human** before anything hard to reverse (deleting data,
force-pushing, destructive or outbound actions) or on genuine ambiguity. Leave an audit
trail — small commits + the journal — so a human can trust and roll back your work.

## Conventions

- Mark a deliberate corner-cut with an `evolve:` comment naming the ceiling and the
  upgrade path (e.g. `# evolve: O(n^2) scan, fine < 10k rows; use a hash index above`).
- Non-trivial logic leaves **one** small runnable check behind; trivial one-liners need
  none.
- Small commits are the experiment log; the current state is the best-known solution.
