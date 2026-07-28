"""Grader for 08_reuse. Kept separate from reuse.py (the code under test).

WHAT THIS MEASURES
------------------
reuse.py already contains normalize_sku(), a documented helper that defines what
"the same product code" means, and three existing functions already route through
it. The task asks for two lookups whose whole requirement is "canonicalise the
code, then use the dict". A solution can satisfy the literal task by writing that
canonicalisation again inline; a disciplined one calls the helper that is already
there.

Checks 1 to 5 are ordinary correctness and gate the result: an answer that
reuses the helper but returns the wrong product cannot outscore a correct one,
because every reuse probe below also asserts the right product came back.

Checks 6, 7 and 8 measure ONE discipline (reuse an existing helper rather than
duplicating its logic) from three angles: find_product, remove_product, and
whether the two new functions still agree with the rest of the module when the
canonical rule changes. A reader who wants to discount that discipline should
discount all three together, not one of them.

WHICH RULESET ASKS FOR WHAT (stated per check in CHECK_SOURCES below)
  - ponytail, ladder rung 2: "Already in this codebase? A helper, util, type, or
    pattern that already lives here -> reuse it. Look before you write."
  - AutoEvolve, minimalism ladder rung 2: "Reuse: Use existing helper/pattern in
    this codebase."
  - karpathy: does NOT ask for reuse anywhere. Checks 6 to 8 therefore reward
    behaviour that two of the three rulesets ask for and the third does not, and
    this scenario is expected to favour ponytail and AutoEvolve for that reason.
    Karpathy #3 ("Don't refactor things that aren't broken") does overlap check 8
    in the branch where a submission rewrote the existing functions; that is a
    partial overlap, not coverage of the check.

HOW REUSE IS DETECTED, AND WHAT THAT MISSES
-------------------------------------------
No source text is read. The module's normalize_sku is replaced with a stub and
the new functions are called; if the stub does not change what they find, they
are not routing through it. This is the technique 04_refactor uses, extended to
cover the aliasing forms that plain patch.object misses:

  - a module-level alias (`_norm = normalize_sku`): every module attribute whose
    value IS the original function object is patched, so the alias is patched too
    and counts as reuse, which is the honest verdict since there is still one
    definition of the rule.
  - a captured default argument (`def find_product(c, s, _norm=normalize_sku)`):
    __defaults__ and __kwdefaults__ entries holding the original object are
    swapped as well.
  - a thin wrapper (`def _canon(raw): return normalize_sku(raw)`) needs no
    special handling: it resolves the global at call time, so the stub reaches it.

Known limits, stated rather than silently mis-reported: a submission that
captures the helper in a CLOSURE (defining the new functions inside a factory
function) or wraps it in a module-level functools.partial keeps a direct
reference the stub cannot reach, and would be scored as a reimplementation. Both
shapes are unlikely at module level in a single-file answer, and neither is
suggested by the task, but a run that shows them is a false negative.

The stubs are IDEMPOTENT on purpose (stub(stub(x)) == stub(x)). A legitimate
solution that canonicalises both sides of a comparison, for example scanning the
catalog with normalize_sku(key) == normalize_sku(query), then still matches under
the stub. A non-idempotent stub would have failed that correct solution.

Correctness inputs never contain a repeated separator ("AB  12", "AB--12"). The
documented rule maps each space or underscore to one hyphen, while a regex
spelling of the same rule collapses runs; the two agree on every input that has
no run, and the difference is not what this scenario is measuring.
"""
import contextlib
import importlib
import os
import sys
import types
from unittest.mock import patch

HERE = os.path.dirname(os.path.abspath(__file__))

# Constant-return stub for the delegation probes. No canonicalisation of the
# query string can produce this key, so only a call to the helper reaches it.
SENTINEL_KEY = "ZZ-SENTINEL-9"
UNRELATED_CODE = "unrelated-code-77"

# Single source for the check names, so an unimportable submission is still
# reported as a full set of failed checks. If the import escaped checks(),
# run.py would print "[ERROR] the grader itself failed to run (this is a harness
# bug)" and evals/profile.py would record outcome=grader_error with
# checks_total=None, DROPPING the trial from the published averages instead of
# scoring it zero.
CHECK_NAMES = (
    "find_product resolves any spelling of a registered product code",
    "find_product returns None for an unknown or blank code, catalog untouched",
    "remove_product removes the entry for any spelling and reports success",
    "remove_product reports failure for an unknown code and changes nothing",
    "existing normalize_sku, register_product and rename_product still behave as before",
    "find_product routes through the module's normalize_sku",
    "remove_product routes through the module's normalize_sku",
    "find_product and remove_product follow the module's canonical rule when it changes",
)

# Which ruleset explicitly asks for each check, by index. Kept next to the names
# so the mapping cannot drift away from the checks it describes.
CHECK_SOURCES = (
    "correctness; all three rulesets gate correctness (AutoEvolve guardrails "
    "'Gate Correctness First'; karpathy 4 'verifiable success criteria'; ponytail "
    "'Trust-boundary validation ... never cut')",
    "correctness, as above",
    "correctness, as above",
    "correctness, as above",
    "correctness plus karpathy 3 'Don't improve adjacent code ... don't refactor "
    "things that aren't broken'",
    "ponytail rung 2 and AutoEvolve minimalism ladder rung 2 (reuse). karpathy does not ask for this",
    "ponytail rung 2 and AutoEvolve minimalism ladder rung 2 (reuse). karpathy does not ask for this",
    "ponytail rung 2 and AutoEvolve minimalism ladder rung 2 (reuse); partial overlap "
    "with karpathy 3 only when existing functions were rewritten",
)


def _alt_rule(raw):
    """A different but equally valid canonical rule: dots instead of hyphens.

    Idempotent, and injective over the codes used below, so two distinct products
    stay distinct under it.
    """
    return raw.strip().upper().replace(" ", ".").replace("_", ".").replace("-", ".")


@contextlib.contextmanager
def _stub_normalize(module, stub):
    """Replace normalize_sku everywhere a module-level call site can reach it.

    Patches every module attribute bound to the original function object (so a
    module-level alias is covered) and every function default argument holding it
    (so a captured default is covered). Everything is restored on exit.
    """
    original = getattr(module, "normalize_sku", None)
    if original is None:
        yield False
        return
    restore = []
    with contextlib.ExitStack() as stack:
        for name, value in list(vars(module).items()):
            if value is original:
                stack.enter_context(patch.object(module, name, stub))
        for value in list(vars(module).values()):
            if not isinstance(value, types.FunctionType):
                continue
            defaults = value.__defaults__
            if defaults and any(d is original for d in defaults):
                restore.append((value, "__defaults__", defaults))
                value.__defaults__ = tuple(stub if d is original else d for d in defaults)
            kwdefaults = value.__kwdefaults__
            if kwdefaults and any(d is original for d in kwdefaults.values()):
                restore.append((value, "__kwdefaults__", dict(kwdefaults)))
                value.__kwdefaults__ = {
                    k: (stub if v is original else v) for k, v in kwdefaults.items()
                }
        try:
            yield True
        finally:
            for func, attr, old in reversed(restore):
                setattr(func, attr, old)


def _record(sku, name, price_cents):
    return {"sku": sku, "name": name, "price_cents": price_cents}


def checks():
    added_path = HERE not in sys.path
    if added_path:
        sys.path.insert(0, HERE)
    try:
        return _checks()
    finally:
        if added_path and HERE in sys.path:
            sys.path.remove(HERE)


def _checks():
    try:
        import reuse
        importlib.reload(reuse)
        for attr in ("find_product", "remove_product", "register_product"):
            if not callable(getattr(reuse, attr, None)):
                raise AttributeError(f"reuse.py has no callable {attr}")
    except Exception as exc:  # noqa: BLE001 - an unusable submission fails, it is not a bug
        reason = f"reuse.py did not import a usable module: {type(exc).__name__}: {exc}"[:170]
        return [(name, False, reason) for name in CHECK_NAMES]

    def fresh():
        catalog = {}
        reuse.register_product(catalog, "ab 12", "Blue Widget", 1250)
        reuse.register_product(catalog, "CD-34", "Red Gadget", 999)
        return catalog

    def find_any_spelling():
        catalog = fresh()
        if set(catalog) != {"AB-12", "CD-34"}:
            return False, f"register_product produced keys {sorted(catalog)}, expected AB-12 and CD-34"
        wanted = {"AB-12": catalog["AB-12"], "CD-34": catalog["CD-34"]}
        spellings = [
            ("AB-12", "AB-12"), ("ab-12", "AB-12"), ("ab 12", "AB-12"),
            ("AB_12", "AB-12"), ("  Ab-12  ", "AB-12"), ("\tab_12\n", "AB-12"),
            ("CD-34", "CD-34"), ("cd 34", "CD-34"), ("cd_34", "CD-34"),
        ]
        for raw, key in spellings:
            got = reuse.find_product(catalog, raw)
            if got != wanted[key]:
                return False, f"find_product(catalog, {raw!r}) returned {got!r}, expected the {key} record"
        return True, ""

    def find_misses():
        catalog = fresh()
        before = {k: dict(v) for k, v in catalog.items()}
        for raw in ("EF-56", "ef 56", "", "   ", "-", "zz 99"):
            got = reuse.find_product(catalog, raw)
            if got is not None:
                return False, f"find_product(catalog, {raw!r}) returned {got!r}, expected None"
        if catalog != before:
            return False, "find_product modified the catalog"
        return True, ""

    def remove_any_spelling():
        for raw in ("AB-12", "ab 12", "ab_12", "  Ab-12  "):
            catalog = fresh()
            got = reuse.remove_product(catalog, raw)
            if not got:
                return False, f"remove_product(catalog, {raw!r}) returned {got!r}, expected a true value"
            if "AB-12" in catalog:
                return False, f"remove_product(catalog, {raw!r}) left AB-12 in the catalog"
            if set(catalog) != {"CD-34"}:
                return False, f"remove_product(catalog, {raw!r}) left the catalog as {sorted(catalog)}"
            if reuse.find_product(catalog, "AB-12") is not None:
                return False, f"after remove_product(catalog, {raw!r}) the product was still findable"
        return True, ""

    def remove_misses():
        catalog = fresh()
        before = {k: dict(v) for k, v in catalog.items()}
        for raw in ("EF-56", "", "   ", "zz 99"):
            got = reuse.remove_product(catalog, raw)
            if got:
                return False, f"remove_product(catalog, {raw!r}) returned {got!r}, expected a false value"
            if catalog != before:
                return False, f"remove_product(catalog, {raw!r}) changed the catalog"
        return True, ""

    def existing_preserved():
        for raw, want in ((" ab 12 ", "AB-12"), ("AB-12", "AB-12"), ("ab_12", "AB-12"),
                          ("xy 9", "XY-9")):
            got = reuse.normalize_sku(raw)
            if got != want:
                return False, f"normalize_sku({raw!r}) returned {got!r}, expected {want!r}"
        catalog = {}
        key = reuse.register_product(catalog, "ef 56", "Green Thing", 500)
        if key != "EF-56":
            return False, f"register_product returned {key!r}, expected 'EF-56'"
        if catalog.get("EF-56") != _record("EF-56", "Green Thing", 500):
            return False, f"register_product stored {catalog.get('EF-56')!r}"
        if not reuse.rename_product(catalog, "EF_56", "Green Thing v2"):
            return False, "rename_product did not rename a registered product"
        if catalog["EF-56"]["name"] != "Green Thing v2":
            return False, f"rename_product left the name as {catalog['EF-56']['name']!r}"
        if reuse.rename_product(catalog, "zz 99", "Nope"):
            return False, "rename_product reported success for an unregistered code"
        return True, ""

    def find_delegates():
        catalog = {SENTINEL_KEY: _record(SENTINEL_KEY, "Sentinel Widget", 1)}
        with _stub_normalize(reuse, lambda raw: SENTINEL_KEY) as patched:
            if not patched:
                return False, "reuse.py no longer defines normalize_sku, so nothing routes through it"
            got = reuse.find_product(catalog, UNRELATED_CODE)
        if got == catalog[SENTINEL_KEY]:
            return True, ""
        if got is None:
            return False, (
                f"with normalize_sku stubbed, find_product(catalog, {UNRELATED_CODE!r}) returned "
                "None; the stubbed helper had no effect, so find_product canonicalises the code "
                "itself instead of using the module helper"
            )
        return False, (
            f"with normalize_sku stubbed, find_product(catalog, {UNRELATED_CODE!r}) returned "
            f"{got!r}, which is not the stored record; the stub did reach it, so this is the "
            "return shape being wrong rather than a reuse failure (see check 1)"
        )

    def remove_delegates():
        catalog = {SENTINEL_KEY: _record(SENTINEL_KEY, "Sentinel Widget", 1)}
        with _stub_normalize(reuse, lambda raw: SENTINEL_KEY) as patched:
            if not patched:
                return False, "reuse.py no longer defines normalize_sku, so nothing routes through it"
            got = reuse.remove_product(catalog, UNRELATED_CODE)
        if got and not catalog:
            return True, ""
        if catalog:
            return False, (
                f"with normalize_sku stubbed, remove_product(catalog, {UNRELATED_CODE!r}) "
                f"returned {got!r} and left {sorted(catalog)}; the stubbed helper had no effect, "
                "so remove_product canonicalises the code itself instead of using the module helper"
            )
        return False, (
            f"with normalize_sku stubbed, remove_product(catalog, {UNRELATED_CODE!r}) removed the "
            f"record but reported {got!r}; the stub did reach it, so this is the return value "
            "being wrong rather than a reuse failure (see checks 3 and 4)"
        )

    def follows_rule_change():
        with _stub_normalize(reuse, _alt_rule) as patched:
            if not patched:
                return False, "reuse.py no longer defines normalize_sku, so nothing routes through it"
            catalog = {}
            key_a = reuse.register_product(catalog, "ab 12", "Blue Widget", 1250)
            reuse.register_product(catalog, "cd-34", "Red Gadget", 999)
            # Attribution guard: if the EXISTING writer no longer routes through the
            # helper, the catalog keys are not built by the swapped rule and this
            # check can say nothing about find_product or remove_product. Report the
            # real cause rather than blaming the new code.
            if key_a != _alt_rule("ab 12"):
                return False, (
                    f"register_product returned {key_a!r} under the swapped rule; it no longer "
                    "routes through normalize_sku, so this check cannot attribute a failure to "
                    "find_product or remove_product"
                )
            renamed = reuse.rename_product(catalog, "AB_12", "Blue Widget v2")
            if not renamed:
                return False, (
                    "rename_product no longer routes through normalize_sku under the swapped "
                    "rule, so this check cannot attribute a failure to the new code"
                )
            found = reuse.find_product(catalog, " Ab-12 ")
            other = reuse.find_product(catalog, "cd 34")
            removed = reuse.remove_product(catalog, "CD_34")
            gone = reuse.find_product(catalog, "cd-34")
            leftover = sorted(catalog)
        if not isinstance(found, dict) or found.get("name") != "Blue Widget v2":
            if found is None:
                return False, (
                    "under the swapped canonical rule find_product(catalog, ' Ab-12 ') returned "
                    "None; it applies its own copy of the rule, so it no longer agrees with the "
                    "keys register_product and rename_product wrote"
                )
            return False, (
                f"under the swapped canonical rule find_product(catalog, ' Ab-12 ') returned "
                f"{found!r} rather than the renamed record (see checks 1 and 5)"
            )
        if not isinstance(other, dict) or other.get("name") != "Red Gadget":
            return False, f"under the swapped rule find_product(catalog, 'cd 34') returned {other!r}"
        if not removed or gone is not None or leftover != [_alt_rule("ab 12")]:
            return False, (
                f"under the swapped rule remove_product(catalog, 'CD_34') returned {removed!r} "
                f"and left {leftover}"
            )
        return True, ""

    probes = (
        find_any_spelling,
        find_misses,
        remove_any_spelling,
        remove_misses,
        existing_preserved,
        find_delegates,
        remove_delegates,
        follows_rule_change,
    )

    out = []
    for name, fn in zip(CHECK_NAMES, probes):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001 - a failing candidate is a failed check
            ok, detail = False, f"raised {type(exc).__name__}: {exc}"[:150]
        out.append((name, bool(ok), detail))
    return out
