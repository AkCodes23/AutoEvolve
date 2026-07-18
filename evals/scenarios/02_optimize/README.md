# Scenario 02: a slow function

**Task:** `dedupe(items)` removes duplicates while preserving order, but it is O(n^2) and
too slow on large inputs. Make it faster without changing its behavior.

**The signal (a number, gated by a binary):** run the grader. Correctness must stay green,
and the scaling ratio must drop from quadratic (about 4) to roughly linear (under 3).

```bash
python3 evals/run.py 02_optimize     # correctness passes, scaling FAILS on the starter
# ... let your agent optimize dedupe.py ...
python3 evals/run.py 02_optimize     # both PASS
```

**What a good (mindset) run does:** records the baseline first, makes one small change
(track seen items in a `set`), verifies correctness before speed, takes the median of a few
runs rather than the best, and keeps the change because it is faster **and** simpler. It
would reject a micro-optimization that shaved time by adding hacky complexity, and it never
changes the output order.

**Files:** `dedupe.py` is the code under test. `grade.py` is the ruler. The scaling check is
a timing heuristic, so also read the millisecond numbers it prints.
