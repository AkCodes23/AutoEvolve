# A worked example

One real task, walked end to end through the loop. The task here is an ordinary bugfix with
no numeric metric, to show that the signal is often just a **failing test that must go
green**, not a score.

**The task.** A bug report: `search("")` raises `KeyError` instead of returning an empty
list. `search` is called from three places.

---

### 0. Understand

Read `search` and reproduce the crash in a REPL. The `KeyError` comes from
`index[query[0]]` when `query` is empty: `query[0]` fails. Three call sites use `search`;
the bug is in the shared function, not any one caller.

### 1. Define the signal

There is no number here. The signal is a **binary**: a test that currently fails and must
pass, without breaking the existing suite.

```python
def test_search_empty_returns_empty():
    assert search("") == []
```

The test lives in the test file, separate from `search` itself (the ruler stays out of the
thing it measures).

### 2. Baseline

```
$ pytest -q
1 failed, 48 passed        # the new test is red; the other 48 are the guardrail
```

Commit this known-good checkpoint (the code, plus the new red test). HEAD is now a state you
can return to.

### 3. Smallest correct change (walk the ladder)

Rung 2 of the ladder: does a guard already exist? No. Rung 7: the minimum code that works
is a one-line early return, placed at the **root** (inside `search`), so all three callers
are fixed at once rather than patched three times.

```python
def search(query):
    if not query:
        return []
    ...
```

### 4. Verify

```
$ pytest -q
49 passed                  # the new test is green, and nothing else broke
```

Does it run: yes. Is it correct: the target test passes and the full suite still passes.
Nothing to optimize for size or speed here.

### 5. Keep or revert

The signal went red to green with no regression. It meets the keep rule, so commit it.

> An earlier attempt guarded at *one call site* instead of inside `search`. That turned the
> target test green but left the other two callers still able to crash, so the full suite
> caught nothing and the fix was in the wrong layer. That attempt was **reverted**
> (`git restore . && git clean -fd`) and recorded, then replaced by the root fix above. A
> reverted experiment is still progress: it ruled the shallow fix out.

### 6. Journal

```
commit  | signal          | status | what changed              | why
7b1c9e2 | search test red->green | keep | early-return guard in search() | root fix, all 3 callers covered
a0f3d51 | search test red->green | revert | guard at one call site      | wrong layer, other callers still crash
```

### 7. Simplify

One line, at the root, no new dependency, no duplication. There is nothing to delete.
Done.

### 8. Repeat / stop

The goal is met and the change is reversible and low-stakes, so there is no need to pause
for a human. Summarize for the human: *"`search("")` now returns `[]`; fixed at the root so
all callers are covered; one line; full suite green."*

---

The same shape scales up. On a hard optimization problem the signal becomes a number, step 3
runs many times, and in **deep** intensity you would keep rival approaches on branches like
`evolve/fast` and `evolve/small` and evolve the most promising lineage. The loop does not
change; only the signal and the number of rounds do.
