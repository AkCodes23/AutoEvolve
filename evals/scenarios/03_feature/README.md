# Scenario 03: add pagination

**Task:** add a `page` parameter to `list_items`. With no page, behave exactly as before
(return all items). With `page=N` (1-based), return that page of `per_page` items. Reject an
invalid page.

**The signal (an acceptance check):** run the grader. The paged results must be correct,
the no-page default must be unchanged, and an invalid `page` must be rejected.

```bash
python3 evals/run.py 03_feature      # FAIL on the untouched starter
# ... let your agent add pagination in listing.py ...
python3 evals/run.py 03_feature      # PASS
```

**What a good (mindset) run does:** writes the acceptance conditions down first, then makes
the smallest change that satisfies them (no wholesale rewrite of the handler). It treats the
guardrail as non-negotiable and **validates** `page` (rejects zero, negative, and
non-integer input) rather than trusting it. It verifies every condition by running the
grader, and does not break the no-page default.

**Files:** `listing.py` is the code under test. `grade.py` is the ruler.
