# Scenario 02: a slow function

**Task to give the agent:** "`dedupe(items)` is too slow on large inputs. Make it faster
without changing its behavior."

**Setup:** a `dedupe` that removes duplicates while preserving order using a nested scan
(O(n^2)), a correctness test, and a tiny benchmark that prints elapsed time on a large list.

**The signal:** a number (the benchmark time) gated by a binary (the correctness test must
stay green). Lower time wins only if correctness holds.

**What the mindset should change (treatment vs control):**
- Records the baseline time before editing.
- Makes one small change (track seen items in a `set`), not a rewrite.
- Verifies correctness first, then time, and takes the **median** of a few runs rather than
  the best.
- Keeps the change because it is faster **and** simpler (fewer lines); would reject a
  micro-optimization that shaved a little time by adding hacky complexity.
- Journals the before/after number.

**Failure modes a weak run shows:** reports the best (not median) time, changes output
order, or adds a caching layer nobody asked for.
