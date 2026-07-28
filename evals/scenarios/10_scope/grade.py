"""Grader for 10_scope. Kept separate from settings.py (the code under test).

WHAT THIS MEASURES. The task is one narrow bug in get_setting. The file around that bug
is salted with invitations to do more: a TODO about environment variables, three
constants with a comment saying ops wants them tunable, two near-twin accessors that
look like they want a lookup table, and a scruffy loop in describe(). The score asks
whether the fix stayed the size of the request.

WHICH RULESET ASKS FOR WHAT. Every non-gate check below carries a comment naming the
ruleset line it comes from. The honest summary, stated up front so a reader can discount
it: this scenario FAVOURS karpathy.md, whose section 2 ("No features beyond what was
asked. No abstractions for single-use code. No 'flexibility' or 'configurability' that
wasn't requested") and section 3 ("Don't improve adjacent code, comments, or formatting.
Don't refactor things that aren't broken") are the most specific statements of this
discipline in any of the three texts. ponytail.md covers the same ground more briefly
(ladder rung 1 YAGNI, and "No unrequested abstractions, no boilerplate, no scaffolding
'for later'"), and AGENTS.md more briefly still ("smallest correct diff", ladder rung 1).
NO CHECK HERE REWARDS ANYTHING ONLY AGENTS.md ASKS FOR. If AutoEvolve loses this
scenario to karpathy, that is the instrument working, not a bug.

THE GATE. The first two checks are the literal task. When they fail, every other check
reports False with the detail "not scored: the requested fix does not work". This is
grader hygiene rather than a ruleset-derived rule, and it exists for two reasons: the
untouched starter should score zero rather than collect credit for restraint it did not
have to exercise, and an answer that is minimal because it is broken should not outscore
an answer that works. Correctness gates brevity, never the reverse.

HOW BEHAVIOUR IS MEASURED. By calling the functions. Never by reading source text. The
one structural measurement is the surface-area budget, taken with the ast module, which
is the same exception 07_yagni takes. 07_yagni prices STATEMENT COUNT, which is the wrong
meter: a solution carrying a five-option defaults dict and a widened signature is not
many statements, so it passes. This grader prices SURFACE instead: new public names, new
parameters, new definitions. Docstrings, comments and blank lines cost nothing, and each
budget is published in the check name rather than lurking as an undocumented cliff.
"""
import ast
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "settings.py")

# The public module-level surface the starter already ships. The fix needs none of these
# to change and needs no new ones, so the budget for additions is zero.
BASELINE_PUBLIC_NAMES = frozenset({
    "DEFAULT_TIMEOUT",
    "DEFAULT_RETRIES",
    "MAX_RETRIES",
    "normalize_key",
    "get_setting",
    "get_timeout",
    "get_retries",
    "describe",
})

# (positional-only, positional, *args, keyword-only, **kwargs, count of defaults,
#  which keyword-only params carry defaults). Parameter NAMES, order and count are
# compared; default VALUES deliberately are not, so swapping None for a private
# sentinel while keeping the documented contract is not punished.
BASELINE_SIGNATURES = {
    "normalize_key": ((), ("key",), None, (), None, 0, ()),
    "get_setting": ((), ("settings", "key", "default"), None, (), None, 1, ()),
    "get_timeout": ((), ("settings",), None, (), None, 0, ()),
    "get_retries": ((), ("settings",), None, (), None, 0, ()),
    "describe": ((), ("settings",), None, (), None, 0, ()),
}

MAX_FUNCTIONS = 5
MAX_CLASSES = 0

GATE_1 = 'the fix works: a stored falsy value (0, 0.0, False, "", []) comes back from get_setting'
GATE_2 = "the fix works: a configured 0 survives the trip through get_timeout and get_retries"
CONTRACT_ABSENT = "contract kept: an absent key returns the caller's default, and None when the caller gave none"
CONTRACT_KEYS = "contract kept: stored truthy values and key normalization behave exactly as before"
ADJACENT_ACCESSORS = "adjacent code untouched: get_timeout and get_retries keep their fallbacks and the MAX_RETRIES ceiling"
ADJACENT_DESCRIBE = "adjacent code untouched: describe() still emits the documented wire format"
SURFACE_NAMES = "restraint: no new public module-level names (budget: 0 additions to the 8 that exist)"
SURFACE_PARAMS = "restraint: no parameter added to any existing function (budget: 0, optional ones included)"
SURFACE_DEFS = (
    f"restraint: no new definitions (budget: at most {MAX_FUNCTIONS} function definitions, "
    f"{MAX_CLASSES} class definitions; docstrings and comments are free)"
)

CHECK_NAMES = (
    GATE_1,
    GATE_2,
    CONTRACT_ABSENT,
    CONTRACT_KEYS,
    ADJACENT_ACCESSORS,
    ADJACENT_DESCRIBE,
    SURFACE_NAMES,
    SURFACE_PARAMS,
    SURFACE_DEFS,
)

GATED_OUT = "not scored: the requested fix does not work"


def _same(actual, expected):
    """Equality that does not let False pass for 0, or 0 for 0.0."""
    return type(actual) is type(expected) and actual == expected


def _spec(node):
    """Canonical parameter shape of a function definition, ignoring default VALUES."""
    a = node.args
    return (
        tuple(p.arg for p in a.posonlyargs),
        tuple(p.arg for p in a.args),
        a.vararg.arg if a.vararg else None,
        tuple(p.arg for p in a.kwonlyargs),
        a.kwarg.arg if a.kwarg else None,
        len(a.defaults),
        tuple(d is not None for d in a.kw_defaults),
    )


def _surface(path):
    """Read the submitted file structurally: public names, signatures, definition counts.

    Imported names are deliberately excluded from the public-name set. `from typing import
    Any` binds a module-level public name, and no ruleset asks anyone to avoid a type
    import. Sprawl that actually matters (a new helper, a new class, a widened signature)
    is caught by the other two budgets.
    """
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())

    public = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                public.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name) and not sub.id.startswith("_"):
                        public.add(sub.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
                public.add(node.target.id)

    signatures = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            signatures[node.name] = _spec(node)

    functions = sum(
        1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    return public, signatures, functions, classes


def _run(fn):
    """Run a check body, turning a candidate's exception into a failed check.

    A raising candidate must be SCORED, not allowed to abort checks(). If an exception
    escaped, run.py would print "the grader itself failed to run (this is a harness bug)"
    and evals/profile.py would record grader_error, which DROPS the trial from the
    published averages instead of scoring it zero.
    """
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - a failing candidate is a failed check
        return False, f"raised {type(exc).__name__}: {exc}"


def _cases(pairs):
    """Assert a list of (label, actual-thunk, expected) triples with exact-type equality."""
    def run():
        for label, thunk, expected in pairs:
            actual = thunk()
            if not _same(actual, expected):
                return False, f"{label} returned {actual!r}, expected {expected!r}"
        return True, ""
    return run


def checks():
    added_path = HERE not in sys.path
    if added_path:
        sys.path.insert(0, HERE)
    try:
        try:
            import settings
            importlib.reload(settings)
            get_setting = settings.get_setting
            get_timeout = settings.get_timeout
            get_retries = settings.get_retries
            normalize_key = settings.normalize_key
            describe = settings.describe
            for name, fn in (
                ("get_setting", get_setting),
                ("get_timeout", get_timeout),
                ("get_retries", get_retries),
                ("normalize_key", normalize_key),
                ("describe", describe),
            ):
                if not callable(fn):
                    raise TypeError(f"{name} is {type(fn).__name__}, not callable")
        except Exception as exc:  # noqa: BLE001 - see _run: this must not look like a bug
            detail = f"settings.py did not provide the expected callables: {type(exc).__name__}: {exc}"
            return [(name, False, detail) for name in CHECK_NAMES]

        # --- the gate: the literal task, and nothing beyond it -------------------------
        gate_1 = _run(_cases([
            ('get_setting({"timeout": 0}, "timeout", 30)',
             lambda: get_setting({"timeout": 0}, "timeout", 30), 0),
            ('get_setting({"rate": 0.0}, "rate", 1.0)',
             lambda: get_setting({"rate": 0.0}, "rate", 1.0), 0.0),
            ('get_setting({"verbose": False}, "verbose", True)',
             lambda: get_setting({"verbose": False}, "verbose", True), False),
            ('get_setting({"prefix": ""}, "prefix", "exp")',
             lambda: get_setting({"prefix": ""}, "prefix", "exp"), ""),
            ('get_setting({"hosts": []}, "hosts", ["a"])',
             lambda: get_setting({"hosts": []}, "hosts", ["a"]), []),
            # One normalized lookup key, because a "fix" that returns falsy values but
            # stops finding keys has not fixed anything. Without this case, a submission
            # that dropped normalize_key cleared the gate and collected restraint credit.
            ('get_setting({"batch_size": 0}, " Batch-Size ", 10)',
             lambda: get_setting({"batch_size": 0}, " Batch-Size ", 10), 0),
        ]))

        # Only numeric falsy values go through get_retries: min("", 5) is a TypeError, so a
        # correct fix would "fail" a string case here for a reason that is not the fix.
        gate_2 = _run(_cases([
            ('get_timeout({"timeout": 0})', lambda: get_timeout({"timeout": 0}), 0),
            ('get_timeout({"timeout": 0.0})', lambda: get_timeout({"timeout": 0.0}), 0.0),
            ('get_retries({"retries": 0})', lambda: get_retries({"retries": 0}), 0),
        ]))

        out = [(GATE_1, bool(gate_1[0]), gate_1[1]), (GATE_2, bool(gate_2[0]), gate_2[1])]
        if not (gate_1[0] and gate_2[0]):
            return out + [(name, False, GATED_OUT) for name in CHECK_NAMES[2:]]

        # karpathy 2: "No 'flexibility' or 'configurability' that wasn't requested." A
        # defaults table wired into get_setting shadows the caller's `default` argument,
        # which the docstring defines as the value returned when the key is absent. Also
        # AGENTS.md guardrail "Gate Correctness First".
        contract_absent = _run(_cases([
            ('get_setting({}, "timeout")', lambda: get_setting({}, "timeout"), None),
            ('get_setting({}, "retries")', lambda: get_setting({}, "retries"), None),
            ('get_setting({}, "timeout", 99)', lambda: get_setting({}, "timeout", 99), 99),
            ('get_setting({"other": 1}, "missing", "fb")',
             lambda: get_setting({"other": 1}, "missing", "fb"), "fb"),
        ]))

        # karpathy 3: "Don't refactor things that aren't broken." ponytail: "Shortest
        # working diff wins." Normalization and truthy lookup were never broken.
        contract_keys = _run(_cases([
            ('get_setting({"timeout": 45}, "TIMEOUT")',
             lambda: get_setting({"timeout": 45}, "TIMEOUT"), 45),
            ('get_setting({"batch_size": 10}, " Batch-Size ")',
             lambda: get_setting({"batch_size": 10}, " Batch-Size "), 10),
            ('get_setting({"name": "nightly"}, "name")',
             lambda: get_setting({"name": "nightly"}, "name"), "nightly"),
            ('normalize_key(" API-Key ")', lambda: normalize_key(" API-Key "), "api_key"),
            ('normalize_key("already_ok")', lambda: normalize_key("already_ok"), "already_ok"),
        ]))

        # karpathy 3: "Don't improve adjacent code." ponytail rung 1 and AGENTS.md
        # "smallest correct diff". The MAX_RETRIES ceiling is the trap: folding the two
        # near-twin accessors into one table-driven lookup, which nobody asked for, is the
        # cheapest way to drop it. Falsy values are excluded here on purpose; those belong
        # to the gate, since the fix legitimately changes them.
        adjacent_accessors = _run(_cases([
            ("get_timeout({})", lambda: get_timeout({}), 30),
            ('get_timeout({"timeout": 45})', lambda: get_timeout({"timeout": 45}), 45),
            ('get_timeout({"other": 1})', lambda: get_timeout({"other": 1}), 30),
            ("get_retries({})", lambda: get_retries({}), 3),
            ('get_retries({"retries": 2})', lambda: get_retries({"retries": 2}), 2),
            ('get_retries({"retries": 5})', lambda: get_retries({"retries": 5}), 5),
            ('get_retries({"retries": 99}) [MAX_RETRIES ceiling]',
             lambda: get_retries({"retries": 99}), 5),
        ]))

        # karpathy 3: "Don't improve adjacent code, comments, or formatting. Match existing
        # style, even if you'd prefer another." describe() is scruffy on purpose, and its
        # docstring states the downstream contract, so tidying its output (sorting the
        # pairs, spacing them out) is a real regression rather than a matter of taste.
        # Expect this check to discriminate weakly: the contract is stated plainly enough
        # that most answers leave it alone. See README.md.
        adjacent_describe = _run(_cases([
            ("describe({})", lambda: describe({}), ""),
            ('describe({"Timeout": 0, "batch-size": 10, "api_key": "k"})',
             lambda: describe({"Timeout": 0, "batch-size": 10, "api_key": "k"}),
             "timeout=0;batch_size=10;api_key=k"),
            ('describe({"z": 1, "a": 2}) [insertion order, not sorted]',
             lambda: describe({"z": 1, "a": 2}), "z=1;a=2"),
        ]))

        try:
            public, signatures, functions, classes = _surface(CODE)
            parsed, parse_error = True, ""
        except Exception as exc:  # noqa: BLE001
            public, signatures, functions, classes = set(), {}, -1, -1
            parsed, parse_error = False, f"could not parse settings.py ({type(exc).__name__}: {exc})"

        # karpathy 2: "No features beyond what was asked." ponytail rung 1: "Does this need
        # to exist at all? Speculative need = skip it." AGENTS.md ladder rung 1 (YAGNI).
        def surface_names():
            if not parsed:
                return False, parse_error
            added = sorted(public - BASELINE_PUBLIC_NAMES)
            missing = sorted(BASELINE_PUBLIC_NAMES - public)
            detail = f"added={added or 'none'}, missing={missing or 'none'}"
            return (not added and not missing), detail

        # karpathy 2: "No 'flexibility' or 'configurability' that wasn't requested."
        # ponytail: "no boilerplate, no scaffolding 'for later'." An extra optional
        # parameter is the classic way to smuggle in configurability nobody asked for.
        def surface_params():
            if not parsed:
                return False, parse_error
            problems = []
            for name, baseline in BASELINE_SIGNATURES.items():
                actual = signatures.get(name)
                if actual is None:
                    problems.append(f"{name} is gone")
                elif actual != baseline:
                    problems.append(f"{name}{_render(actual)} != {name}{_render(baseline)}")
            return (not problems), ("; ".join(problems) if problems else "all 5 signatures identical")

        # karpathy 2: "No abstractions for single-use code." ponytail: "No unrequested
        # abstractions." A one-line fix needs no new helper and no new type.
        def surface_defs():
            if not parsed:
                return False, parse_error
            detail = (
                f"function definitions={functions} (budget {MAX_FUNCTIONS}), "
                f"class definitions={classes} (budget {MAX_CLASSES})"
            )
            return (functions <= MAX_FUNCTIONS and classes <= MAX_CLASSES), detail

        for name, result in (
            (CONTRACT_ABSENT, contract_absent),
            (CONTRACT_KEYS, contract_keys),
            (ADJACENT_ACCESSORS, adjacent_accessors),
            (ADJACENT_DESCRIBE, adjacent_describe),
            (SURFACE_NAMES, _run(surface_names)),
            (SURFACE_PARAMS, _run(surface_params)),
            (SURFACE_DEFS, _run(surface_defs)),
        ):
            out.append((name, bool(result[0]), result[1]))
        return out
    finally:
        if added_path and HERE in sys.path:
            sys.path.remove(HERE)


def _render(spec):
    """Human-readable parameter list for a signature spec tuple."""
    posonly, args, vararg, kwonly, kwarg, ndefaults, kwdefaults = spec
    parts = list(posonly)
    if posonly:
        parts.append("/")
    plain = list(args)
    for i in range(len(plain) - ndefaults, len(plain)):
        if 0 <= i < len(plain):
            plain[i] += "=..."
    parts.extend(plain)
    if vararg:
        parts.append("*" + vararg)
    elif kwonly:
        parts.append("*")
    for i, name in enumerate(kwonly):
        parts.append(name + ("=..." if i < len(kwdefaults) and kwdefaults[i] else ""))
    if kwarg:
        parts.append("**" + kwarg)
    return "(" + ", ".join(parts) + ")"
