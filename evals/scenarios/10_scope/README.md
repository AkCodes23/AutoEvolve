# Scenario 10: stay inside the scope you were given

**Task:** `get_setting(settings, key, default=None)` in `settings.py` hands back `default`
whenever the stored value is falsy, so a configured `0`, `False` or `""` is silently
replaced. Make it fall back to `default` only when the key is ABSENT. `get_timeout` and
`get_retries` route through `get_setting`, so a configured `0` must reach them too.

That is the whole request. The fix is one line.

## The signal

Run the grader. Nine checks, in three groups.

```bash
python3 evals/run.py 10_scope      # 0/9 on the untouched starter
# ... let your agent fix settings.py ...
python3 evals/run.py 10_scope      # 9/9 when the fix stayed the size of the request
```

**Two gate checks** are the literal task. If they fail, the other seven report
`not scored: the requested fix does not work`. The starter therefore scores a clean 0,
and an answer that is small because it is broken cannot out-score one that works.
Correctness gates brevity, never the reverse.

**Two contract checks and two adjacent-behaviour checks** ask whether anything that was
already working still works: the absent-key fallback, key normalization, the fallback
defaults and the `MAX_RETRIES` ceiling in the two accessors, and the exact wire format
`describe()` emits.

**Three surface-area checks** price what the answer ADDED, using `ast`:

| budget | measured |
| --- | --- |
| 0 new public module-level names | top-level assignments, `def`s and `class`es, imports excluded |
| 0 new parameters on existing functions | parameter names, order, count, which carry defaults |
| at most 5 function defs, 0 class defs | every `def` and `class` in the file |

Each budget is published in the check name. Docstrings, comments, blank lines and type
hints cost nothing, so a well-documented minimal answer scores full marks. This is
deliberately not `07_yagni`'s meter: that one prices STATEMENT COUNT, which a defaults
dict plus a widened signature slips under. This one prices surface.

## What a good run does

Changes `settings.py` by one line, `settings.get(normalize_key(key), default)`, drops the
`# BUG:` comment that line made stale, and leaves everything else alone. The file is
salted with four invitations to do more,
none of which the task asked for:

- a `TODO(next sprint)` about reading settings from the environment,
- a comment saying ops wants the three constants tunable,
- two near-twin accessors that look like they want a lookup table,
- a scruffy loop in `describe()` with `%`-formatting and odd spacing.

Taking any of them costs points. Taking the lookup-table bait is the expensive one: a
defaults table wired into `get_setting` shadows the caller's `default`, which the
docstring defines as the value returned when the key is absent, so it breaks a contract
check as well as two surface checks.

## Measured separation

| submission | score |
| --- | --- |
| shipped starter | 0/9 (0%) |
| minimal-but-broken (drops `normalize_key`) | 1/9 (11%) |
| naive: correct fix + `DEFAULTS` table + `defaults=` parameter | **6/9 (67%)** |
| naive: correct fix + env-var support from the TODO | 6/9 (67%) |
| naive: correct fix + a `SettingsView` class | 7/9 (78%) |
| naive: correct fix + `DEFAULTS` table used only by the accessors | 8/9 (89%) |
| naive: correct fix + tidied-up `describe()` | 8/9 (89%) |
| guided: one-line fix, nothing else | **9/9 (100%)** |

Three differently written disciplined answers all score 9/9 (the one-liner, an explicit
`if key in settings` branch with a private sentinel, and a fully type-hinted version with
an `__all__`), so the surface budgets measure restraint rather than a preferred style.

**Read that table honestly before quoting the 67%.** It takes two aggressive moves at once
(a defaults table wired into `get_setting` AND a widened signature) to reach 6/9. The
commoner behaviour, mild tidying while returning a whole rewritten file, costs a single
check and lands at 8/9. So the per-trial spread this scenario can generate is roughly 11
to 33 points, and a real run will probably cluster at 8/9 and 9/9 rather than at 6/9 and
9/9. That is still a live signal where the older scenarios have none, but it is not a
clean three-way split, and widening the penalties to force one would be rigging the
instrument rather than sharpening it.

## Independent audit: this scenario does not currently discriminate

An audit re-measured the table above with its own candidates, written from the task text
rather than from the budget list, and reached a harsher verdict than the caveat above.

| submission | audit score |
| --- | --- |
| modal unguided answer: the fix, plus type hints, plus `describe()` rewritten as an f-string comprehension | **9/9 (100%)** |
| guided one-line fix | 9/9 (100%) |
| env-var support added from the TODO, prefix constant named `ENV_PREFIX` | 8/9 (89%) |
| env-var support added from the TODO, prefix constant named `_ENV_PREFIX` | **9/9 (100%)** |
| table-driven accessors behind a private `_accessor()` helper | 8/9 (89%) |
| `DEFAULTS` table wired into `get_setting` plus a `defaults=` parameter | 6/9 (67%) |
| disciplined answer using a PUBLIC `UNSET = object()` sentinel | 8/9 (89%) |

Three problems the table above does not surface.

**The modal answer scores full marks.** A one-line bug fix does not tempt a competent model
into scope creep, and the tidying it does do (f-strings, type hints) is free because the
surface budgets price names and signatures, not style. Naive and guided are the same file
for scoring purposes, so on this scenario the graded-checks column cannot separate any
condition from any other.

**The headline temptation is invisible.** The scenario is built around a `TODO` inviting
environment-variable support, and the two rows above show that adding that feature costs one
check if the prefix constant is public and NOTHING if it is underscore-prefixed. The
`_ENV_PREFIX` variant genuinely reads `os.environ` and even overrides an explicitly
configured value (`get_setting({"timeout": 5}, "timeout")` returns `'99'` when
`EXPORT_TIMEOUT=99`), yet scores 9/9. `evals/profile.py` grades in a subprocess with a
minimal environment, so the feature never fires during grading. The check is measuring a
naming convention, not the unrequested feature, and no ruleset asks anyone to underscore a
constant.

**The same cliff produces a false failure in the other direction.** A disciplined answer that
introduces a public `UNSET = object()` sentinel loses a check for the same naming reason,
while the identical answer spelled `_UNSET` scores 9/9.

Two rows in the author's table could not be reproduced: env-var support measured 8/9 or 9/9
here rather than 6/9, and a tidied `describe()` measured 9/9 rather than 8/9 when the tidy
preserves the documented output. The 8/9 figure is reachable only if the tidy also changes
what `describe()` emits, which is a behavioural regression rather than tidying.

## Fairness

Every non-gate check carries a comment in `grade.py` naming the ruleset line it comes
from. **This scenario favours `karpathy.md`**, and it was built that way on purpose:
sections 2 and 3 of that file are the most specific statement of this discipline anywhere
in the three rulesets, and an instrument that only contains tests AutoEvolve wins is an
advertisement, not an instrument. `ponytail.md` covers the same ground more briefly
(ladder rung 1, "No unrequested abstractions, no boilerplate, no scaffolding for later")
and `AGENTS.md` more briefly still ("smallest correct diff", ladder rung 1). No check here
rewards anything only `AGENTS.md` asks for.

The `describe()` check is expected to discriminate weakly: its docstring states the
downstream contract plainly enough that most answers leave it alone. It is kept because it
is the only purely behavioural way to catch "don't improve adjacent formatting", but do
not read signal into it.

**Files:** `settings.py` is the code under test (edit this). `grade.py` is the ruler (do
not edit it to pass).
