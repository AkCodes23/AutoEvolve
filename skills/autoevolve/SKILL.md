---
name: autoevolve
description: >-
  Operating mindset for changing an existing codebase in small, verified steps: define an
  honest signal for "better", make the smallest correct change, keep it only if it
  measurably improves things (else revert), journal each experiment, and relentlessly
  simplify. Use when fixing a bug, adding a feature, optimizing, refactoring, or iterating
  toward a target in an existing repository, especially across many consecutive changes or
  with limited supervision.
argument-hint: "[quick|default|deep]"
license: MIT
---

# AutoEvolve: evolve the code, don't just write it

Adopt this loop for the task at hand. The full rationale lives in the repo's root
`AGENTS.md` and `README.md`; this is the actionable core.

## The loop

1. **Understand** the problem first: read the code, reproduce the bug, pin the goal.
2. **Define the signal.** Decide how you'll tell whether a change is better. A signal can
   be a **number** (benchmark, timing), a **binary** (a test that goes red to green, a
   type/lint check that passes), or an **acceptance check** you confirm by running or
   re-reading. Not every task has a number, but every task has a "better" you can pin down.
   Make it fast and hard to game, and keep the ruler **separate** from the code it measures
   (don't let the thing being optimized rewrite its own scorer).
3. **Baseline.** Record the current behavior/score; make sure the tree is clean so you
   can revert.
4. **Propose the smallest correct change** by walking the ladder (below). One concern per
   change; prefer a surgical diff to a rewrite.
5. **Verify** in cascade: does it run? → is it correct? → *only then* is it smaller /
   faster / cleaner? Correctness and safety gate everything; a wrong answer is wrong no
   matter how short. If the signal is noisy, take the **median** of a few runs.
6. **Keep or revert.** Keep if it's strictly better with no regression, *or*
   neutral-but-simpler, *or* a deletion, and still correct; commit it (new best).
   Otherwise revert, and keep the lesson. A reverted experiment still made progress: it
   ruled an option out.
7. **Record** one line: *commit · signal · keep/revert · what changed · why.*
8. **Simplify.** Can you get the same result with less? Deleting code is a win.
9. **Repeat**, keeping a couple of distinct working approaches alive so you don't get
   stuck. When you run out of ideas, **don't stop; think harder**: re-read the code and
   references, combine near-misses, or try a deliberately radical alternative.

## The minimalism ladder: run before writing any code

> 1. Does this need to be built at all? (YAGNI)
> 2. Does it already exist in this codebase? Reuse the helper/util/pattern.
> 3. Does the standard library already do this? Use it.
> 4. Does a native platform/language feature cover it? Use it.
> 5. Does an already-installed dependency solve it? Use it; don't add a new one.
> 6. Can this be one line? Make it one line.
> 7. Only then: write the minimum code that works.
>
> The ladder runs *after* you understand the problem. The smallest change in the wrong
> place isn't lazy; it's a second bug.

## Never be lazy about (guardrails)

Input validation at trust boundaries · error handling that prevents data loss ·
security · accessibility · anything explicitly requested · picking the edge-case-correct
option over the flimsier one. Minimalism is about the solution, never about rigor.

## Autonomy

Proceed on reversible, in-scope changes; keep going when stuck rather than asking "should
I continue?"; **pause for a human** before anything hard to reverse (deleting data,
force-pushing, destructive or outbound actions) or on genuine ambiguity. Leave an audit
trail (small commits plus the journal) so a human can trust and roll back your work.

"Keep going when stuck" is bounded: **stop after 10 loops** and check in with a human, as
`AGENTS.md` requires. Persevering through a hard problem is the
point; looping past 10 without new information is not.

When reverting, restore only the paths you touched (from `HEAD`, so a staged change is also
undone) and delete only the untracked files you created. Never bulk-discard a dirty tree: work
you did not create may be in it, and `git checkout -- .` destroys it unrecoverably.

## Modes

The mode sets ceremony, not rigor. Correctness, validation, and security are never reduced.

- `quick`: a small, obviously-scoped change. Define the signal, make the diff, verify, keep or
  revert. Journal one line. No branching.
- `default`: the full loop as described above, one hypothesis at a time against `HEAD`.
- `deep`: hold competing candidates on `evolve/<niche>` branches, score each against the same
  frozen signal, and promote the winner to `HEAD`. Use when several approaches are plausible and
  you want to compare them rather than guess.

## Conventions

- Mark a deliberate corner-cut with an `evolve:` comment naming the ceiling and the
  upgrade path (e.g. `# evolve: O(n^2) scan, fine < 10k rows; use a hash index above`).
- Non-trivial logic leaves **one** small runnable check behind; trivial one-liners need
  none.
- Small commits are the experiment log; the current state is the best-known solution.
