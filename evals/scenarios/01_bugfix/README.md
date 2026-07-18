# Scenario 01: crash on empty input

**Task:** `search("")` crashes instead of returning an empty list. `search` is called from
three places (`suggest`, `count_matches`, `has_match`). Fix it.

**The signal (a binary):** run the grader. `search("")` and all three callers must handle
an empty query, and valid queries must still work.

```bash
python3 evals/run.py 01_bugfix      # FAIL on the untouched starter
# ... let your agent fix search.py ...
python3 evals/run.py 01_bugfix      # PASS
```

**What a good (mindset) run does:** fixes the root (one guard inside `search`), so all three
callers pass at once, rather than patching each call site. Verifies red to green by running
the grader, and keeps the change (one line, no new dependency).

**Files:** `search.py` is the code under test (edit this). `grade.py` is the ruler (do not
edit it to pass).
