"""Grader for 01_bugfix. Kept separate from search.py (the code under test).

Contract under test (from search.py and README.md): search(query) maps a query to the list of
indexed words whose first letter is the query's first letter, and an EMPTY query yields an
empty list. suggest/count_matches/has_match are thin callers that must inherit that.

Six probes, each able to fail on its own for its own reason:
  1. search("") itself returns []. This is the root-cause discriminator: four per-call-site
     guards leave search() broken, so this probe fails for them while their callers pass.
  2. A caller CONSTRUCTED HERE AT GRADE TIME, over a mixed sequence of queries. A solution
     that patched each shipped call site cannot have wrapped a call site the grader invents,
     so this only passes when the fix lives inside search itself.
  3. suggest hands search's result back unchanged, for an empty and for a valid query.
  4. count_matches returns integer counts.
  5. Valid queries still return the indexed words in index order, with no drop, duplicate or
     reorder, and the results are stable across repeated calls. This probe issues no empty
     query of its own, so it is a regression guard rather than a second reading of probe 1
     (it can still catch a fix that corrupts shared state on the empty path).
  6. has_match returns real booleans (a root fix leaves has_match untouched, so `is False`
     can only catch a solution that gratuitously changed its return type).

Deliberately NOT probed, because the contract does not cover them and two legitimate fixes
disagree there: a first letter absent from the index (search("z")) and a whitespace-only
query. `if not query: return []` raises KeyError on "z" while `_INDEX.get(query[0:1], [])`
returns []; both are correct single-guard fixes, so probing that would fail one of them.
Every probe checks BEHAVIOUR: no source-text inspection, no exception-type assertions, and an
exception is never read as evidence of a working guard.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE_PATH = os.path.join(HERE, "search.py")

# A unique module name keeps a sibling scenario's search.py out of sys.modules["search"],
# where a cached module would otherwise be reloaded from the wrong file under run.py --all.
MODULE_NAME = "autoevolve_01_bugfix_search"

WORDS_BY_LETTER = {"a": ["apple", "apricot"], "b": ["banana"], "c": ["cherry"]}


def _load_code_under_test():
    """Execute search.py fresh from this directory, leaving sys.path and sys.modules as found."""
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


def _probe_root_empty_query(mod):
    got = mod.search("")
    if got != []:
        return f"search('') returned {got!r}, expected []"
    return ""


def _probe_grade_time_caller(mod):
    # Built here, at grade time. The solution has never seen this call site, so it cannot have
    # been guarded one call site at a time.
    def fresh_caller(queries):
        return [mod.search(q) for q in queries]

    queries = ["", "a", "", "b", "c", ""]
    expected = [[], ["apple", "apricot"], [], ["banana"], ["cherry"], []]
    got = fresh_caller(queries)
    if got != expected:
        return f"a new call site got {got!r} for {queries!r}, expected {expected!r}"
    return ""


def _probe_suggest(mod):
    empty = mod.suggest("")
    if empty != []:
        return f"suggest('') returned {empty!r}, expected []"
    valid = mod.suggest("a")
    if valid != WORDS_BY_LETTER["a"]:
        return f"suggest('a') returned {valid!r}, expected {WORDS_BY_LETTER['a']!r}"
    return ""


def _probe_count_matches(mod):
    for query, expected in [("", 0), ("a", 2), ("b", 1), ("c", 1)]:
        got = mod.count_matches(query)
        if got != expected:
            return f"count_matches({query!r}) returned {got!r}, expected {expected}"
    return ""


def _probe_valid_queries(mod):
    for letter, words in WORDS_BY_LETTER.items():
        got = mod.search(letter)
        if got != words:
            return f"search({letter!r}) returned {got!r}, expected {words!r}"
        again = mod.search(letter)
        if again != words:
            return f"search({letter!r}) returned {again!r} on a second call, expected {words!r}"
    return ""


def _probe_has_match(mod):
    for query, expected in [("", False), ("a", True), ("c", True)]:
        got = mod.has_match(query)
        if got is not expected:
            return f"has_match({query!r}) returned {got!r}, expected {expected!r}"
    return ""


PROBES = [
    ('search("") returns [] at the root, not just in its callers', _probe_root_empty_query),
    ("a call site added at grade time gets correct results from search", _probe_grade_time_caller),
    ("suggest returns search's list unchanged, empty and valid", _probe_suggest),
    ("count_matches returns integer counts", _probe_count_matches),
    ("valid queries still return the indexed words in order", _probe_valid_queries),
    ("has_match returns real booleans", _probe_has_match),
]


def checks():
    try:
        mod = _load_code_under_test()
    except Exception as e:
        # A candidate that cannot even be imported scores zero: it must not look like a
        # harness bug, which would drop the row from the benchmark instead of failing it.
        detail = f"search.py failed to import: {type(e).__name__}: {e}"
        return [(name, False, detail) for name, _ in PROBES]

    out = []
    for name, probe in PROBES:
        try:
            detail = probe(mod)
            out.append((name, not detail, detail))
        except Exception as e:
            # An exception is a failure, never evidence that a guard exists.
            out.append((name, False, f"raised {type(e).__name__}: {e}"))
    return out
