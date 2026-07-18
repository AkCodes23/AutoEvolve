# Scenario 01: crash on empty input

**Task to give the agent:** "`search("")` raises `KeyError` instead of returning an empty
list. `search` is called from three places. Fix it."

**Setup:** a `search(query)` that does `index[query[0]]` with no guard, plus three call
sites and a small existing test suite that passes.

**The signal:** a binary. A new test, `assert search("") == []`, is red and must go green
without breaking the existing suite.

**What the mindset should change (treatment vs control):**
- Names the signal first: writes (or points at) the failing test before editing.
- Fixes at the **root** (a one-line guard inside `search`), not per-caller, so all three
  callers are covered by one change. Grepping the callers is the tell.
- Runs the suite and reads the actual result (red to green), rather than declaring it fixed.
- Leaves a journal line, and keeps the change (one line, no new dependency).

**Failure modes a weak run shows:** guards one call site (suite still catches nothing),
rewrites `search`, or marks it done without running the test.
