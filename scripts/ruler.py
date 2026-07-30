#!/usr/bin/env python3
"""Report what your change did to the tests that judge it.

    python3 scripts/ruler.py                # your uncommitted changes
    python3 scripts/ruler.py --rev HEAD~3

"Optimize the objective, never the scorer" is stated in five places in this mindset and nothing
checked it. It is also the guardrail whose violation is worst: a change that weakens its own test
voids the evidence that anything else improved.

What is frozen comes from `DIRECTION.md`, the human-owned declaration of the signal; convention
(`tests/`, `test_*.py`, `conftest.py`) is the fallback. Two tiers: `weakened` is a test gone from
the whole ruler, or a new skip marker. `review` is a surviving test that lost assertions or
changed what it expects.

REPORT ONLY: no `--strict`, not in the hook, always exits 0, and a test keeps it that way. Unlike
`comments.py` nothing here is provable. A changed expectation is equally a bug fix, and adding
tests is the commonest honest reason to touch a test file, so a gate would block real work.

Measured before trusted, bar written first: at most 25 percent of human test-touching commits may
raise `weakened`. `urllib3` gives 7 percent and `click` 14 (`scripts/ruler_audit.py`). Read those
with their caveat: two small repositories, and click's history motivated the move detection, so it
is not an independent test of it. Python only.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from callers import changed_files, git  # noqa: E402
from comments import file_at_rev, quietly_parse  # noqa: E402

SKIP_MARKERS = ("skip", "skipif", "skipunless", "xfail", "expectedfailure", "disabled", "ignore")
TEST_CONVENTIONS = re.compile(r"(^|/)(tests?/|test_[^/]*\.py$|[^/]*_test\.py$|conftest\.py$)")
ASSERT_CALL = re.compile(r"^assert[A-Z_]")


def signal_paths(root: str) -> list[str]:
    """Path-like tokens from DIRECTION.md's `Signal:` line, which the human owns."""
    path = os.path.join(root, "DIRECTION.md")
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError:
        return []
    match = re.search(r"^Signal:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return []
    line = match.group(1).split("(")[0]
    found = []
    for token in line.split():
        token = token.strip("\"'`,")
        # A placeholder that was never filled in names nothing.
        if token.startswith("<") or token.startswith("{{"):
            continue
        if "/" in token or token.endswith(".py"):
            found.append(token.rstrip("/"))
    return found


def is_ruler(rel: str, declared: list[str]) -> bool:
    rel = rel.replace(os.sep, "/")
    if declared:
        return any(rel == d or rel.startswith(d + "/") for d in declared)
    return bool(TEST_CONVENTIONS.search(rel))


def test_functions(source: str) -> dict[str, ast.AST]:
    """Every test callable, keyed by `Class.name` so two suites cannot collide."""
    tree = quietly_parse(source)
    if tree is None:
        return {}
    found: dict[str, ast.AST] = {}

    def collect(node: ast.AST, prefix: str) -> None:
        for child in getattr(node, "body", []):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child.name.startswith("test"):
                    found[prefix + child.name] = child
            elif isinstance(child, ast.ClassDef):
                collect(child, prefix + child.name + ".")

    collect(tree, "")
    return found


def skip_markers(node: ast.AST) -> set[str]:
    names = set()
    for decorator in getattr(node, "decorator_list", []):
        text = ast.unparse(decorator).lower()
        for marker in SKIP_MARKERS:
            if re.search(rf"\b{marker}\b", text):
                names.add(ast.unparse(decorator)[:60])
    return names


def assertion_count(node: ast.AST) -> int:
    total = 0
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            total += 1
        elif isinstance(child, ast.Call):
            name = getattr(child.func, "attr", None) or getattr(child.func, "id", "")
            if ASSERT_CALL.match(str(name)) or str(name) in {"assert_", "fail", "raises"}:
                total += 1
    return total


def expectations(node: ast.AST) -> list[str]:
    """The literal values a test asserts about, as text, in source order."""
    found = []
    for child in ast.walk(node):
        if isinstance(child, (ast.Assert, ast.Call)):
            for sub in ast.walk(child):
                if isinstance(sub, ast.Constant) and not isinstance(sub.value, bool):
                    if isinstance(sub.value, str) and len(sub.value) > 60:
                        continue
                    found.append(repr(sub.value))
    return found


def body_text(node: ast.AST) -> str:
    return ast.unparse(node.body) if hasattr(node, "body") else ""


def compare(before: str, after: str, elsewhere_names: frozenset[str] = frozenset(),
            elsewhere_bodies: frozenset[str] = frozenset()) -> list[tuple[str, str, str]]:
    """Findings as (tier, name, message) for one test file across two revisions.

    `elsewhere_*` describe every other ruler file AFTER the change, and without them the tool
    calls a move a deletion. Click's commit 7007982 split `tests/test_utils.py` into a directory
    and read as ten removed tests, which is a tidy-up reported as the worst thing the tool can
    say. A suite is not weaker because a test changed file.
    """
    old, new = test_functions(before), test_functions(after)
    if not old:
        return []
    findings = []

    # A test whose body reappears under another name was renamed, not removed. Without this a
    # tidy-up that renames half a suite reads as the worst finding the tool has.
    surviving_bodies = {body_text(node): name for name, node in new.items() if name not in old}
    for name, node in old.items():
        if name in new:
            continue
        bare = name.rsplit(".", 1)[-1]
        if surviving_bodies.get(body_text(node)) or bare in elsewhere_names:
            continue
        if body_text(node) in elsewhere_bodies:
            continue
        findings.append(("weakened", name,
                         f"test `{name}` existed at the baseline and is gone, with no renamed "
                         "copy of its body. If it was obsolete say so; if the code it covered "
                         "still ships, the suite got easier rather than the code getting better."))

    for name, node in new.items():
        if name not in old:
            continue
        gained = skip_markers(node) - skip_markers(old[name])
        if gained:
            findings.append(("weakened", name,
                             f"test `{name}` gained {', '.join(sorted(gained))}. A skipped test "
                             "reports success without running."))
        before_n, after_n = assertion_count(old[name]), assertion_count(node)
        if after_n < before_n:
            findings.append(("review", name,
                             f"test `{name}` went from {before_n} to {after_n} assertions. "
                             "Fewer checks can be a simplification or a lowered bar."))
        old_exp, new_exp = expectations(old[name]), expectations(node)
        if old_exp != new_exp and after_n >= before_n:
            changed = [e for e in old_exp if e not in new_exp][:4]
            if changed:
                findings.append(("review", name,
                                 f"test `{name}` no longer expects {', '.join(changed)}. "
                                 "Changing what a test expects is how a fix looks and also how "
                                 "moving the goalposts looks."))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rev", default="HEAD", help="baseline revision (default: HEAD)")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--paths", nargs="*", help="files to inspect instead of the git diff")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    declared = signal_paths(root)
    targets = args.paths if args.paths else changed_files(
        root, args.rev if args.rev != "HEAD" else None, suffix=None)
    in_ruler = [t for t in targets if is_ruler(t, declared)]
    # Only Python can be compared, but the ruler is whatever the human declared, so a JavaScript
    # or Go test file is part of the signal even though nothing here can read it.
    rulers = [t for t in in_ruler if t.endswith(".py")]
    unreadable = [t for t in in_ruler if not t.endswith(".py")]

    source = (f"DIRECTION.md names {', '.join(declared)}" if declared
              else "convention (no DIRECTION.md signal names a path)")
    if not rulers:
        # Saying "no changes to the frozen signal" here would be a false all-clear: the signal
        # did change, in a language this tool cannot parse. That is the one sentence this tool
        # must never print wrongly, since a silent pass is exactly what it exists to prevent.
        if unreadable:
            print(f"Cannot judge this change. Scope: {source}.")
            print(f"{len(unreadable)} changed file(s) belong to the ruler but are not Python, "
                  "so nothing here can read them:")
            for rel in sorted(unreadable):
                print(f"    {rel}")
            print("Review them yourself. Absence of findings below is not evidence of anything.")
            return 0
        others = len(targets)
        print(f"No changes to the frozen signal. Scope: {source}.")
        if others:
            print(f"{others} changed file(s), none of them part of the ruler. This is what you "
                  "want to see.")
        return 0

    print(f"Scope: {source}")
    print(f"Your change touches {len(rulers)} file(s) that judge it:\n")
    tiers = {"weakened": 0, "review": 0}

    # Every test present anywhere in the ruler after the change, so one that moved between files
    # is recognised as moved rather than reported as deleted.
    names: set[str] = set()
    bodies: set[str] = set()
    for rel in rulers:
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as handle:
            for name, node in test_functions(handle.read()).items():
                names.add(name.rsplit(".", 1)[-1])
                bodies.add(body_text(node))

    for rel in sorted(rulers):
        before = file_at_rev(root, rel, args.rev)
        full = os.path.join(root, rel)
        if before is None or not os.path.isfile(full):
            print(f"{rel}  (new file, nothing to compare)\n")
            continue
        with open(full, encoding="utf-8", errors="replace") as handle:
            after = handle.read()
        findings = compare(before, after, frozenset(names), frozenset(bodies))
        if not findings:
            print(f"{rel}  -> changed, but no test was removed, skipped or loosened\n")
            continue
        print(rel)
        for tier, _, message in findings:
            tiers[tier] += 1
            print(f"    [{tier}] {message}")
        print()

    if unreadable:
        # The counts below cover the Python files only. Printing them without this would let a
        # clean tally stand for files that were never opened.
        print(f"{len(unreadable)} further changed ruler file(s) are not Python and were not "
              "examined:")
        for rel in sorted(unreadable):
            print(f"    {rel}")
        print()

    print(f"{tiers['weakened']} weakened, {tiers['review']} to review"
          f"{', across the Python files only' if unreadable else ''}.")
    print("Nothing here is proof. A deleted test may be obsolete and a changed expectation may be")
    print("the fix. But the loop only means something while the ruler holds still, so the one")
    print("thing you may not do is change it in the same breath as the code and not say so.")
    print("If a change to the signal is genuinely needed, that is the documented moment to stop")
    print("and ask a human.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
