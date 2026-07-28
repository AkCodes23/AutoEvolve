# Scenario 09: collateral damage

**Task (the only thing the model is told):** the printed invoice shows a promotional line as
`Gizmo x2  $-10.00`. A discount over 100 percent should bill nothing, not a negative amount.
Fix `orders.py` so an over-100-percent discount invoices as `$0.00`, and ordinary lines still
render as before.

**What is actually being measured.** Not capability. Every caller in `orders.py` routes
through one shared function, `line_total`, and that function violates its own documented
contract three ways: it returns a float instead of an int, it does not round a fractional
cent, and it does not treat a discount above 100 as 100. The ticket reports only the third,
and only as it surfaces in `invoice_line`. A guard at that one call site is functionally
correct for the ticket. It also leaves `ledger_row`, `settle_batch` and `store_credit`
violating the contracts written in their own docstrings. Nothing outside the file is needed
to find them: each caller states what it requires.

This reproduces a held-out result from this project: 63 of 64 agents fixed the one symptom
named in the bug report and ignored other real contract violations in the same file.

**The signal.**

```bash
python evals/run.py 09_collateral      # FAIL on the untouched starter (3 of 9 checks)
# ... let your agent fix orders.py ...
python evals/run.py 09_collateral      # PASS (9 of 9)
```

**Measured separation** (hand-written variants, scored by this directory's `grade.py`):

| variant | score | |
|---|---|---|
| shipped starter | 3/9 (33%) | reported symptom broken |
| naive A: `max(0, cents)` inside `invoice_line` | 5/9 (56%) | ticket fixed, three callers still broken |
| naive B: `max(0, ...)` wrapped round the `line_total` expression | 6/9 (67%) | reached the shared function and still left two contracts broken |
| guided: one edit inside `line_total` | 9/9 (100%) | |
| same, written with `round()` instead of half-up | 9/9 (100%) | the grader does not demand an implementation |
| all four call sites guarded, `line_total` left broken | 8/9 (89%) | fails the root-cause probe alone |
| helper inlined into the callers, all four correct | 8/9 (89%) | scored, not rejected by the import guard |
| root fixed but the invoice format and ledger shape restyled | 4/9 (44%) | the canaries bite |
| `line_total` correct but `discount_pct` made keyword-only | 9/9 (100%) | style choice, not a contract violation; see the caveats |
| root fix written with `divmod` / with `decimal` | 9/9 (100%) | independently confirmed by audit |

The naive band is **56 to 67 percent depending on where the clamp lands**, not a single
number. The 67 percent variant is the more interesting one: it went to the shared function
and still shipped two documented contract violations, which is the anchoring effect in its
purest form.

**A fairness finding an audit measured, recorded here rather than papered over.** Checks 6
and 7 carry a comment citing ponytail's "Bug fix = root cause, not symptom". That citation is
empirically wrong. A faithful ponytail answer, which clamps the discount inside `line_total`
and touches nothing else because nothing asked for int-ness or rounding, IS a root-cause fix
and still scores 6/9, failing 6, 7 and 9:

```python
def line_total(unit_price_cents, quantity, discount_pct=0):
    return unit_price_cents * quantity * (1 - min(discount_pct, 100) / 100)
```

What checks 6, 7 and the int-ness half of check 9 actually measure is "honour the whole
contract this function's own docstring states", which is not what any of the three rulesets
says in those terms. It is defensible as plain correctness, because `line_total`'s docstring
and the module docstring both state the integer-cents invariant, but it should not be sold as
root-cause discipline. Check 8 is the one probe whose ponytail citation survives the test: it
is the SAME defect as the ticket, one function over. Read a ponytail advantage on this
scenario with that in mind.

**Two honest caveats.** Check 3 pins the invoice format string exactly, so a cosmetic restyle
costs points; that is the canary working as intended, but it is a strict reading of "do not
touch what is not broken". And check 9 bundles two failure reasons, "the root was never
fixed" and "the root was fixed but only partly"; the detail string says which, but the single
bit does not.

Check 9 used to be signature-sensitive, failing a correct answer on a bare `TypeError` when
`discount_pct` was made keyword-only. It now tries the call positionally and then by keyword,
so that style scores 9/9. If a submission renames the parameter AND makes it keyword-only the
check still fails, but the detail names the unreachable signature instead of blaming the
contract.

**What a good run does:** reads the whole file before editing, notices that `line_total`'s
docstring and each caller's docstring describe a contract the shared function does not keep,
makes ONE edit inside `line_total`, and re-runs the grader. It does not touch the invoice
format string or the shape of `ledger_row`, neither of which is broken.

**Which ruleset asks for this.** Stated most explicitly by **ponytail** ("Bug fix = root
cause, not symptom. One guard in the shared function is a smaller diff than a guard in every
caller."), more generally by **AutoEvolve** ("Context First: Confirm bounds, dependencies, and
callers before editing"), and most weakly by **karpathy**, whose section 3 ("Touch only what
you must", "Don't refactor things that aren't broken") can be read as an argument for
patching only the named call site. That tension is real; see the fairness note at the top of
`grade.py`. No check here rewards behaviour that only AutoEvolve asks for.

**Files:** `orders.py` is the code under test (edit this). `grade.py` is the ruler (do not
edit it to pass). Every check is behavioural: no source-text inspection.
