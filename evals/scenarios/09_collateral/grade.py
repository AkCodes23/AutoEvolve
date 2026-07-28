"""Grader for 09_collateral. Kept separate from orders.py (the code under test).

WHAT IS BEING MEASURED
----------------------
Not capability: fixing the reported ticket is easy and an unguided model does it. What is
measured is whether the fix went into the shared function `line_total` (which every caller
routes through) or only into the one call site the ticket named.

`line_total` violates its own documented contract three ways: it returns a float instead of
an int, it does not round a fractional cent, and it does not treat a discount above 100 as
100, so it can go negative. The ticket reports only the third one, and only as it surfaces in
`invoice_line`. A guard at that one call site is functionally correct for the ticket and
leaves the other three callers violating the contracts written in their own docstrings.

FAIRNESS NOTE, READ THIS BEFORE TRUSTING THE NUMBERS
----------------------------------------------------
Every check below carries a comment naming the ruleset line that asks for it. The discipline
under test is stated MOST EXPLICITLY BY PONYTAIL, not by AutoEvolve:

    ponytail: "Bug fix = root cause, not symptom. One guard in the shared function is a
               smaller diff than a guard in every caller."

AutoEvolve's claim on it is real but more general ("Context First: Confirm bounds,
dependencies, and callers before editing"). Karpathy's is the weakest and is partly in
tension: section 3 says "Touch only what you must" and "Don't refactor things that aren't
broken", which a reader could take as an argument for patching only `invoice_line`. The
counter-reading is that one edit to `line_total` is a strictly smaller diff than four
call-site guards, so section 3 supports it. That tension is genuine and a reader should
discount karpathy's expected advantage here accordingly.

NO check in this file rewards behaviour that only AutoEvolve asks for.

METHOD
------
Behaviour only. No `inspect.getsource`, no substring matching on source text, no assertions
about exception types. Nine probes, each able to fail for its own reason:

  1-2 are the reported symptom, so a naive call-site guard earns partial credit.
  3-5 are regression canaries over behaviour that ALREADY WORKS in the shipped starter, so a
      destructive rewrite is punished rather than rewarded.
  6-8 are the discriminating probes: one per other caller, each tied to a contract stated in
      that caller's own docstring, and each able to fail independently of the others.
      Check 6 asserts int-ness only and check 7 asserts value only, on purpose: bundling them
      would make "rounds correctly but returns a float" and "returns an int but truncates"
      indistinguishable.
  9  is the root-cause probe. It calls `line_total` directly with inputs no other probe uses.
      It fails on its own, and only on its own, for the solution that guarded each of the four
      shipped call sites individually and left the shared function broken.

Rounding ties are deliberately never probed. A tie is the one input where `round()` (banker's)
and `(x + 50) // 100` (half up) disagree, and both are defensible readings of "rounded to the
nearest whole cent". `_TIES` recomputes this from the probe inputs at grade time and is
reported in the details of checks 7 and 9, so the claim is verified rather than asserted.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE_PATH = os.path.join(HERE, "orders.py")

# A unique module name keeps a sibling scenario out of sys.modules and stops a cached module
# from being reloaded off the wrong file under `run.py --all`.
MODULE_NAME = "autoevolve_09_collateral_orders"


def _expected_cents(price, qty, pct):
    """The contract in integer arithmetic: clamp the discount, round to the nearest cent."""
    pct = min(pct, 100)
    return (price * qty * (100 - pct) + 50) // 100


# Every (price, quantity, discount_pct) triple this grader feeds to the code under test.
PROBE_TRIPLES = [
    (1000, 2, 150), (999, 2, 0), (105, 3, 0), (2000, 2, 25), (1234, 1, 0),
    (1000, 3, 50), (333, 1, 25), (333, 1, 30), (777, 3, 101), (500, 4, 200),
    (777, 3, 15), (451, 7, 33), (1500, 1, 120), (89, 11, 0),
]

# Triples whose exact answer lands on a half-cent tie. Must be empty: see the module docstring.
_TIES = [
    (p, q, d) for p, q, d in PROBE_TRIPLES
    if (p * q * (100 - min(d, 100))) % 100 == 50
]


def _load_code_under_test():
    """Execute orders.py fresh from this directory, leaving sys.path and sys.modules as found."""
    spec = importlib.util.spec_from_file_location(MODULE_NAME, CODE_PATH)
    mod = importlib.util.module_from_spec(spec)
    added_path = HERE not in sys.path
    if added_path:
        sys.path.insert(0, HERE)
    try:
        sys.modules[MODULE_NAME] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if added_path and HERE in sys.path:
            sys.path.remove(HERE)
    return mod


def _line(name, sku, price, qty, pct=None):
    row = {"name": name, "sku": sku, "unit_price_cents": price, "quantity": qty}
    if pct is not None:
        row["discount_pct"] = pct
    return row


def _is_int(value):
    """A real int. bool is a subclass of int and is not an amount of money."""
    return isinstance(value, int) and not isinstance(value, bool)


# --- 1. the reported symptom ------------------------------------------------------------
# All three rulesets ask for the task to actually be done. karpathy section 4: "Transform
# tasks into verifiable success criteria." This is the criterion the ticket states.
def _probe_reported_symptom(mod):
    got = mod.invoice_line(_line("Gizmo", "GZ-1", 1000, 2, 150))
    if got != "Gizmo x2  $0.00":
        return f"invoice_line for the promotional line returned {got!r}, expected 'Gizmo x2  $0.00'"
    return ""


# --- 2. the reported symptom, second promotional line -----------------------------------
# karpathy section 4: "Run tests or verification commands after every edit." A fix verified
# on one input only is the failure mode this second input is here to catch.
def _probe_reported_symptom_generalises(mod):
    got = mod.invoice_line(_line("Sprocket", "SP-9", 500, 4, 200))
    if got != "Sprocket x4  $0.00":
        return f"invoice_line at a 200 percent discount returned {got!r}, expected 'Sprocket x4  $0.00'"
    return ""


# --- 3. regression canary: invoice rendering ---------------------------------------------
# karpathy section 3: "Touch only what you must. Don't 'improve' adjacent code, comments, or
# formatting." ponytail: "Deletion over addition. Shortest working diff wins." These three
# lines already render correctly in the shipped starter; the format must survive the fix.
def _probe_canary_invoice_format(mod):
    for line, expected in [
        (_line("Widget", "W-1", 999, 2), "Widget x2  $19.98"),
        (_line("Bolt", "B-7", 105, 3), "Bolt x3  $3.15"),
        (_line("Gasket", "G-1", 2000, 2, 25), "Gasket x2  $30.00"),
    ]:
        got = mod.invoice_line(line)
        if got != expected:
            return f"invoice_line({line['name']}) returned {got!r}, expected {expected!r}"
    return ""


# --- 4. regression canary: ledger row shape ----------------------------------------------
# AutoEvolve loop step 5: "Keep if strictly better"; karpathy section 3 again. ledger_row
# already returns the right pair for these lines in the starter. A rewrite that returns a
# dict, drops the sku, or changes the amount is a regression, not a fix.
def _probe_canary_ledger_shape(mod):
    for line, expected in [
        (_line("Widget", "W-1", 999, 2), ("W-1", 1998)),
        (_line("Gasket", "G-1", 2000, 2, 25), ("G-1", 3000)),
    ]:
        got = mod.ledger_row(line)
        if not isinstance(got, tuple) or len(got) != 2:
            return f"ledger_row returned {got!r}, expected a 2-tuple (sku, amount_cents)"
        # Numeric equality, so the starter's float passes: this canary is not a second
        # reading of the int-ness probe below.
        if got[0] != expected[0] or got[1] != expected[1]:
            return f"ledger_row returned {got!r}, expected {expected!r}"
    return ""


# --- 5. regression canary: amounts that were already right -------------------------------
# ponytail: "Shortest working diff wins" (do not disturb what works). settle_batch and
# store_credit already produce these exact amounts in the starter.
def _probe_canary_existing_amounts(mod):
    batch = [
        _line("Widget", "W-1", 999, 2),
        _line("Plate", "P-2", 1234, 1),
        _line("Bolt", "B-7", 105, 3),
    ]
    got = mod.settle_batch(batch)
    if got != 3547:
        return f"settle_batch on three whole-cent lines returned {got!r}, expected 3547"
    for line, expected in [
        (_line("Gasket", "G-1", 2000, 2, 25), 3000),
        (_line("Hinge", "H-3", 1000, 3, 50), 1500),
    ]:
        credit = mod.store_credit(line)
        if credit != expected:
            return f"store_credit({line['sku']}) returned {credit!r}, expected {expected}"
    return ""


# --- 6. other caller's contract: ledger_row amount is an int -----------------------------
# ponytail: "Bug fix = root cause, not symptom. One guard in the shared function is a smaller
# diff than a guard in every caller." AutoEvolve guardrails: "Context First: Confirm bounds,
# dependencies, and callers before editing." ledger_row's docstring states that the importer
# rejects a non-integer amount. INT-NESS ONLY: value is check 7's job, so the two can fail
# apart.
def _probe_ledger_amount_is_int(mod):
    for line in [
        _line("Widget", "W-1", 999, 2),
        _line("Chip", "C-4", 333, 1, 25),
        _line("Gizmo", "GZ-1", 1000, 2, 150),
    ]:
        amount = mod.ledger_row(line)[1]
        if not _is_int(amount):
            return (f"ledger_row({line['sku']}) amount is {type(amount).__name__} "
                    f"({amount!r}); its docstring requires a Python int")
    return ""


# --- 7. other caller's contract: settle_batch sums nearest-cent line totals ---------------
# ponytail root-cause line, as above. settle_batch's docstring: the total equals the sum of
# the per-line totals "after each line has been rounded to the nearest whole cent". VALUE
# ONLY: a float that equals the right number passes here and fails check 6 instead.
def _probe_settle_batch_value(mod):
    batch = [
        _line("Chip", "C-4", 333, 1, 25),
        _line("Cap", "C-5", 333, 1, 30),
        _line("Widget", "W-1", 999, 2),
    ]
    expected = (
        _expected_cents(333, 1, 25)
        + _expected_cents(333, 1, 30)
        + _expected_cents(999, 2, 0)
    )
    got = mod.settle_batch(batch)
    if got != expected:
        parts = " + ".join(
            str(_expected_cents(p, q, d)) for p, q, d in [(333, 1, 25), (333, 1, 30), (999, 2, 0)]
        )
        return (f"settle_batch returned {got!r}, expected {expected} ({parts}); "
                f"probe inputs landing on a rounding tie: {_TIES}")
    return ""


# --- 8. other caller's contract: store_credit is never negative ---------------------------
# ponytail root-cause line, as above: this is the SAME defect as the reported ticket, one
# function over. store_credit's docstring: "never negative ... It must never bill the
# customer instead." Non-negativity only, so a float 0.0 passes and this stays independent
# of check 6.
def _probe_store_credit_never_negative(mod):
    for line in [
        _line("Gizmo", "GZ-1", 1000, 2, 150),
        _line("Sprocket", "SP-9", 500, 4, 200),
        _line("Trim", "T-8", 777, 3, 101),
    ]:
        got = mod.store_credit(line)
        if got != 0:
            return (f"store_credit({line['sku']}) at a {line['discount_pct']} percent discount "
                    f"returned {got!r}, expected 0 (its docstring forbids a negative credit)")
    return ""


def _call_line_total(mod, price, qty, pct):
    """Call line_total with a discount, however its parameter list allows it.

    Returns (value, error_detail); exactly one of the two is meaningful.

    Positional first, then by keyword. Making `discount_pct` keyword-only is a style
    choice, not a contract violation, and a correct answer that does it must not lose
    this check to a TypeError raised by argument binding. If BOTH spellings raise
    TypeError the parameter list itself changed (or the body raises on plain ints);
    that is reported as such rather than mis-attributed to the contract.
    """
    try:
        return mod.line_total(price, qty, pct), ""
    except TypeError as positional_error:
        first = positional_error
    try:
        return mod.line_total(price, qty, discount_pct=pct), ""
    except TypeError as keyword_error:
        return None, (
            f"line_total could not be called with a discount for ({price}, {qty}, {pct}): "
            f"positionally it raised TypeError: {first}; by keyword it raised TypeError: "
            f"{keyword_error}. Its parameter list changed, or its body rejects plain ints, "
            "so this check cannot read its contract"
        )


# --- 9. the root-cause probe --------------------------------------------------------------
# ponytail: "One guard in the shared function is a smaller diff than a guard in every caller."
# AutoEvolve loop step 0: "reproduce issue before editing"; guardrails "Confirm ... callers".
# Calls line_total directly, on inputs no other probe uses. A solution that guarded all four
# shipped call sites one at a time passes checks 1-8 and fails here alone, which is exactly
# the distinction this scenario exists to draw.
#
# NOTE on what this check actually bundles: it fires for TWO different reasons. A submission
# that never fixed the shared function fails it (the root-cause reading, which is the ponytail
# citation above). A submission that DID fix the root but only clamped the discount, leaving
# the float return and the missing rounding, also fails it. The second reading is "honour the
# whole contract this function's own docstring states", which is not the same discipline. The
# detail string distinguishes the two, and the README records the measurement that shows it.
def _probe_line_total_contract(mod):
    for price, qty, pct in [(777, 3, 15), (451, 7, 33), (1500, 1, 120), (89, 11, 0)]:
        expected = _expected_cents(price, qty, pct)
        got, call_error = _call_line_total(mod, price, qty, pct)
        if call_error:
            return call_error
        if not _is_int(got):
            return (f"line_total({price}, {qty}, {pct}) returned {type(got).__name__} "
                    f"({got!r}); its docstring requires an int number of cents")
        if got != expected:
            return (f"line_total({price}, {qty}, {pct}) returned {got!r}, expected {expected}; "
                    f"probe inputs landing on a rounding tie: {_TIES}")
    return ""


PROBES = [
    ("the reported symptom: a 150 percent discount invoices as $0.00, not a negative", _probe_reported_symptom),
    ("the reported symptom holds for a second over-100-percent line", _probe_reported_symptom_generalises),
    ("regression canary: ordinary invoice lines render exactly as before", _probe_canary_invoice_format),
    ("regression canary: ledger_row still returns (sku, amount) with the same amount", _probe_canary_ledger_shape),
    ("regression canary: amounts settle_batch and store_credit already got right are unchanged", _probe_canary_existing_amounts),
    ("ledger_row's amount is a Python int, as its docstring requires", _probe_ledger_amount_is_int),
    ("settle_batch equals the sum of the per-line nearest-cent totals", _probe_settle_batch_value),
    ("store_credit is never negative when the discount exceeds 100 percent", _probe_store_credit_never_negative),
    ("line_total honours its own contract at a call site added at grade time", _probe_line_total_contract),
]

CHECK_NAMES = tuple(name for name, _ in PROBES)


def checks():
    try:
        mod = _load_code_under_test()
        # The four CALLERS only. `line_total` is deliberately absent: a solution that inlines
        # the helper into its callers has no root left to probe, and should score 8 of 9 with
        # check 9 failing, not 0 of 9 behind a guard an operator would misread as a harness
        # error. Check 9 calls mod.line_total directly and its own except turns a missing
        # helper into that single failed check.
        for attr in ("invoice_line", "ledger_row", "settle_batch", "store_credit"):
            if not callable(getattr(mod, attr, None)):
                raise AttributeError(f"orders.py has no callable {attr}()")
    except Exception as e:  # noqa: BLE001
        # A candidate that will not import, or that dropped a public function, scores zero. It
        # must never look like a harness bug: run.py would call that a grader error and
        # profile.py would DROP the trial from the averages instead of scoring it.
        detail = f"orders.py is not usable: {type(e).__name__}: {e}"
        return [(name, False, detail) for name in CHECK_NAMES]

    out = []
    for name, probe in PROBES:
        try:
            detail = probe(mod)
            out.append((name, not detail, detail))
        except Exception as e:  # noqa: BLE001
            # An exception is a failed check, never evidence that a guard exists.
            out.append((name, False, f"raised {type(e).__name__}: {e}"))
    return out
