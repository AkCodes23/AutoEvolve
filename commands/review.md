---
name: review
description: Review a diff for over-engineering — flag what to cut, not correctness.
---

# /review — an over-engineering review

Use on the current change (or a PR diff). This review is about *unnecessary* code, not
correctness — run the tests separately for that.

**Do this:** read the diff and, for each finding, emit one line:

```
L<line>: <tag> <what to cut>. <the leaner replacement>
```

Tags:
- `delete`  — dead, unreachable, or speculative code that isn't needed yet.
- `reuse`   — reinvents a helper/pattern that already exists in this repo.
- `stdlib`  — reimplements something the standard library already does.
- `native`  — a dependency doing a job a native language/platform feature covers.
- `yagni`   — an abstraction (interface, factory, config knob) with a single use.
- `shrink`  — same behavior achievable in fewer lines.

Rules:
- Judge only over-engineering; leave correctness to the tests.
- **Do not flag the guardrails** — input validation, error handling that prevents data
  loss, security, accessibility, and explicitly-requested behavior are never "excess."
- End with the net lines removable. If there's nothing to cut, say: **"Lean already. Ship."**
