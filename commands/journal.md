---
name: journal
description: Record each experiment in an append-only log so context survives long runs.
---

# /journal — one line per experiment

Use after every keep/revert decision. The journal is your external memory: it's how you
spot trends, avoid repeating dead ends, and find combinable near-misses without re-reading
code. Keep it in a file the repo (or your local notes) can hold — e.g. `JOURNAL.md`.

**Append one row per experiment** (tab- or pipe-separated so descriptions can't break it):

```
commit | signal | status | what changed | why
a1b2c3d | score=0.982 | keep   | reuse existing LRU cache instead of a new dict | fewer lines, same score
b2c3d4e | score=0.980 | revert | hand-rolled cache                             | slower and more code
c3d4e5f | score=0.000 | revert | guard empty input                            | crashed: KeyError on empty input
```

Conventions:
- **status** is `keep` or `revert` (a crashed or broken run is just a `revert` — note the
  reason in the *why* column).
- Record the *actual* measured number(s), not your expectation.
- Note deletions explicitly — a simplification that holds the signal is a win worth
  remembering.
- Keep it append-only; don't rewrite history. The current git HEAD is the champion; the
  journal is the diverse record of ideas tried, including the best per niche.

At the start of a session, **re-read the journal** before proposing the next change.
