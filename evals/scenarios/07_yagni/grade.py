"""Grader for 07_yagni. Kept separate from tags.py (the code under test).

The signal: parse_tags must handle whitespace and empty items cleanly while remaining
minimal (no speculative classes, options, or abstractions the task never asked for).

Two rules this grader follows on purpose:

1. Behaviour is measured by CALLING parse_tags, never by reading its source text.
2. Minimality is measured structurally, with the ast module: statements, function
   definitions, and class definitions. Docstrings, comments, and blank lines are NOT
   code, so they cost nothing. A minimalism check that taxes documentation would push
   an agent toward undocumented code, which is the opposite of the point. The budget is
   stated in the check name and in its detail string, so it is a published limit rather
   than a cliff you discover by falling off it.
"""
import ast
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "tags.py")

# Published complexity budget. Generous enough that a plain explicit for-loop (7 statements)
# fits comfortably; tight enough that a parser class with speculative options does not.
MAX_STATEMENTS = 12
MAX_FUNCTIONS = 2
MAX_CLASSES = 0
# Surface area, which is what YAGNI is actually about and what statement counting misses
# entirely. A DEFAULTS dict holding five options the task never mentioned is ONE statement, and
# an injected `config=None` parameter is zero, so the previous budget scored both at full marks
# on the scenario named for avoiding exactly that.
#
# parse_tags(text) takes one argument. Every extra parameter is "flexibility or configurability
# that wasn't requested" (karpathy section 2), an "unrequested abstraction" (ponytail), and a
# YAGNI violation (ladder rung 1): all three rulesets ask for its absence.
MAX_PARAMS = 1
# Module-level names: the entry point, one optional helper, one optional constant.
MAX_MODULE_NAMES = 3

MINIMAL_NAME = (
    f"minimalism: at most {MAX_STATEMENTS} statements, {MAX_FUNCTIONS} functions, "
    f"{MAX_CLASSES} classes, {MAX_PARAMS} parameter on parse_tags, and "
    f"{MAX_MODULE_NAMES} module-level names (docstrings and comments are free)"
)

NAMES = [
    'comma splitting: "python,AI,coding" yields three tags in order',
    "surrounding whitespace is stripped, including tabs and newlines",
    'empty entries are excluded: "a,,b, " yields ["a", "b"]',
    'an all-empty input like ",,," or " , , " returns []',
    "whitespace inside a tag is preserved",
    'the empty string returns []',
    MINIMAL_NAME,
]


def _complexity(path):
    """Structural size and surface area of a source file, docstrings excluded.

    Returns a dict: statements, functions, classes, params (on parse_tags), module_names.
    """
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())

    docstring_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if ast.get_docstring(node) is not None:
                docstring_nodes.add(id(node.body[0]))

    statements = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.stmt) and id(n) not in docstring_nodes
    ]
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    params = 0
    for node in functions:
        if node.name == "parse_tags":
            a = node.args
            params = (len(a.posonlyargs) + len(a.args) + len(a.kwonlyargs)
                      + (1 if a.vararg else 0) + (1 if a.kwarg else 0))
            break

    # Names bound at module level: definitions and assignments. Imports are excluded, since
    # reaching for the standard library is a rung of the ladder rather than a cost.
    module_names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            module_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        module_names.add(sub.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            module_names.add(node.target.id)

    return {
        "statements": len(statements),
        "functions": len(functions),
        "classes": len(classes),
        "params": params,
        "module_names": len(module_names),
    }


def _checks():
    try:
        import tags
        importlib.reload(tags)
        parse = tags.parse_tags
    except Exception as e:
        # A file that will not import has no measurable behaviour and no measurable
        # minimality: score it zero rather than crashing the harness, which would
        # otherwise be reported as a grader bug and quietly dropped from the averages.
        reason = f"tags.py did not provide a usable parse_tags ({type(e).__name__}: {e})"
        return [(name, False, reason) for name in NAMES]

    def one(text, expected):
        actual = parse(text)
        if not isinstance(actual, list):
            return False, f"parse_tags({text!r}) returned {type(actual).__name__}, expected a list"
        if actual != expected:
            return False, f"parse_tags({text!r}) returned {actual!r}, expected {expected!r}"
        return True, ""

    def behaviour(pairs):
        def check():
            for text, expected in pairs:
                ok, detail = one(text, expected)
                if not ok:
                    return False, detail
            return True, ""
        return check

    def minimal():
        try:
            m = _complexity(CODE)
        except Exception as e:
            return False, f"could not parse tags.py ({type(e).__name__}: {e})"
        budgets = (
            ("statements", MAX_STATEMENTS), ("functions", MAX_FUNCTIONS),
            ("classes", MAX_CLASSES), ("params", MAX_PARAMS),
            ("module_names", MAX_MODULE_NAMES),
        )
        detail = ", ".join(f"{k}={m[k]} (budget {b})" for k, b in budgets)
        over = [k for k, b in budgets if m[k] > b]
        if over:
            detail += f"; over budget on: {', '.join(over)}"
        return not over, detail

    cases = [
        behaviour([
            ("python,AI,coding", ["python", "AI", "coding"]),
            ("solo", ["solo"]),
        ]),
        behaviour([
            ("python, AI , coding ", ["python", "AI", "coding"]),
            ("\tpython ,\nAI\t", ["python", "AI"]),
        ]),
        behaviour([
            ("a,,b, ", ["a", "b"]),
            ("a, ,,b", ["a", "b"]),
        ]),
        behaviour([
            (",,,", []),
            (" , , ", []),
            (",", []),
        ]),
        behaviour([
            ("machine learning, deep  learning", ["machine learning", "deep  learning"]),
        ]),
        behaviour([
            ("", []),
            ("   ", []),
        ]),
        minimal,
    ]

    out = []
    for name, fn in zip(NAMES, cases):
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"raised {type(e).__name__}: {e}"
        out.append((name, bool(ok), detail))
    return out


def checks():
    """Run the graded checks with this scenario's directory on sys.path, then clean up.

    Both the path entry and the imported module are removed afterwards. `run.py --all` grades
    every scenario in ONE interpreter, so a leaked path entry plus a cached module means the
    first scenario to claim a module name wins: a later scenario whose code file shares that
    name would be graded against the wrong file, silently and with a plausible-looking score.
    No two scenarios share a filename today, which is exactly why this is worth fixing now
    rather than after it produces a wrong number.
    """
    added = HERE not in sys.path
    if added:
        sys.path.insert(0, HERE)
    try:
        return _checks()
    finally:
        if added and HERE in sys.path:
            sys.path.remove(HERE)
        for name, module in list(sys.modules.items()):
            origin = getattr(module, "__file__", None) or ""
            if origin and os.path.dirname(os.path.abspath(origin)) == HERE:
                del sys.modules[name]
