#!/usr/bin/env python3
"""List the callers of every symbol you just changed.

    python scripts/callers.py                      # symbols in your uncommitted changes
    python scripts/callers.py --paths src/api.py   # symbols in specific files
    python scripts/callers.py --rev HEAD~3         # symbols changed since a revision

WHY THIS EXISTS. The loop's step 0 says "confirm bounds, dependencies, and callers before
editing", and an agent that follows it writes better changes. The trouble is that following it
is a choice the agent has to make, and measurement says it usually does not: across roughly 580
graded trials, adding more instruction text produced no detectable improvement, because the
failure mode is not ignorance of the rule. It is anchoring on the one symptom in the bug report.
In one held-out task, 63 of 64 agents fixed the single reported symptom and left five other real
contract violations untouched in the same file, each documented in that file's own docstrings.

Rewording the instruction cannot fix that. Removing the choice can. This script does the looking
and puts the answer in front of the agent, which is a mechanism rather than a request. Run it
after step 3 and before step 4, and read every call site it prints: each one is a place your
change either must keep working or must be updated to match.

Standard library only, so it runs in any checkout with no install step.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tokenize

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
             ".venv", "venv", ".mypy_cache", ".tox", "site-packages", "build", "dist"}
# Names so common that every hit would be noise, which would defeat the purpose: a report nobody
# reads is worse than no report.
IGNORED = {"main", "run", "get", "set", "test", "setup", "init", "__init__", "wrapper", "inner"}


def git(args: list[str], cwd: str) -> tuple[int, str]:
    """Run git and decode its output as UTF-8, never as the machine's locale codec.

    `text=True` decodes with the locale encoding, which on Windows is cp1252. One byte outside
    that codepage kills subprocess's reader thread, and the failure is silent in the worst way:
    `returncode` is still 0 while `stdout` comes back as None, so a caller that trusts the exit
    code gets an AttributeError far from the cause, or worse, treats None as "no output" and
    reports an empty diff. Found by running this against `psf/requests`, whose history contains
    exactly such a byte. Git speaks UTF-8; `errors="replace"` keeps one odd character in a commit
    message from deciding whether the tool works at all.
    """
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                         encoding="utf-8", errors="replace")
    return res.returncode, res.stdout or ""


def unresolvable_rev(root: str, rev: str | None) -> bool:
    """True when git cannot resolve `rev`, so a diff against it would mean nothing.

    A revision git rejects and a revision with nothing changed both yield an empty diff, and only
    one of them is good news. `--rev HEAD~5` in a repository with three commits is the everyday
    way to hit this, a typo the other, and both used to report a clean tree.
    """
    if rev is None:
        return False
    code, _ = git(["rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"], root)
    return code != 0


def changed_files(root: str, rev: str | None, suffix: str | None = ".py") -> list[str]:
    """Files changed versus a revision, or the current uncommitted work if no revision.

    `suffix` of None returns every changed path. Callers that can only read one language need
    that to tell "nothing changed" apart from "something changed that I cannot parse", which are
    the same empty list once the filter has run.
    """
    args = ["diff", "--name-only", rev] if rev else ["diff", "--name-only", "HEAD"]
    code, out = git(args, root)
    # Returning early here treated a failed diff as an unchanged tree. With no revision given
    # that diff is against HEAD, which does not exist before the first commit, so every tool
    # went blind in exactly the repository someone has just run `git init` in to try this out.
    # The staged and untracked work collected below is the whole content of such a repository.
    files = set(out.split()) if code == 0 else set()
    if not rev:  # include staged and freshly added work
        for extra in (["diff", "--name-only", "--cached"], ["ls-files", "--others", "--exclude-standard"]):
            code, out = git(extra, root)
            if code == 0:
                files.update(out.split())
    return sorted(f for f in files if suffix is None or f.endswith(suffix))


def read_source(path: str) -> str | None:
    """Decode a Python file the way Python itself would, or None when it cannot be read.

    Reading source as UTF-8 is wrong, not merely strict: PEP 263 lets a file declare another
    encoding in a coding cookie, and a BOM can select UTF-16. Both are importable Python.
    `tokenize.open` is the standard library's own implementation of that detection, so anything
    the interpreter accepts is readable here.

    This lives in the lowest module of the three so `comments.py`, which already imports from
    here, can share it without the dependency pointing back.
    """
    try:
        with tokenize.open(path) as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError, LookupError):
        return None


def defined_symbols(path: str) -> list[tuple[str, int]]:
    """Top-level functions and classes, plus public methods, defined in one file."""
    source = read_source(path)
    if source is None:
        return []
    try:
        tree = ast.parse(source, filename=path)
    except (SyntaxError, ValueError):
        return []
    found = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.append((node.name, node.lineno))
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                            and not child.name.startswith("_"):
                        found.append((child.name, child.lineno))
    return [(name, line) for name, line in found
            if name not in IGNORED and not name.startswith("__")]


def python_files(root: str) -> list[str]:
    out = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        out.extend(os.path.join(dirpath, f) for f in files if f.endswith(".py"))
    return out


def find_callers(root: str, symbols: dict, corpus: list[str]) -> dict:
    """Map each symbol to the (file, line, text) sites that mention it elsewhere."""
    hits: dict[str, list] = {name: [] for name in symbols}
    if not symbols:
        return hits
    # One alternation covering every symbol, so a line is read once no matter how many symbols
    # changed. Scanning once per symbol made the cost files x symbols x lines; this makes it
    # files x lines, which on a 700-file tree with 25 changed symbols is 11.3s -> 0.5s.
    #
    # Both \b anchors are load-bearing, and not only against `prefetch_all` matching `fetch`:
    # they are also what stops a shorter name shadowing a longer one it prefixes. Matching
    # `fetch` inside `fetch_rows` leaves the trailing \b sitting between two word characters,
    # so the alternation backtracks and takes `fetch_rows`. That makes the result independent
    # of the order names appear in, which sorting alone would not guarantee.
    scanner = re.compile(
        r"\b(" + "|".join(re.escape(n) for n in sorted(symbols)) + r")\b")
    for path in corpus:
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                lines = handle.readlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            # Better than 99 percent of lines mention nothing that changed. Settling that with one
            # search, before allocating an iterator and a dict, is what keeps the single-symbol
            # case from paying for the many-symbol case.
            if scanner.search(line) is None:
                continue
            # A name can occur twice on one line. The report carries one entry per line, and a
            # single call occurrence makes the whole line a call site, which is what searching
            # the entire line for `name(` used to decide.
            seen: dict[str, bool] = {}
            for match in scanner.finditer(line):
                name = match.group(1)
                rest = line[match.end():]
                is_call = rest[:1] == "(" or rest.lstrip()[:1] == "("
                seen[name] = seen.get(name, False) or is_call
            for name, is_call in seen.items():
                # The defining file is scanned too, with only the `def` line itself skipped.
                # Skipping the whole file hid every same-module caller, which is the common shape
                # of a single-file fix and precisely the case this tool exists for: a shared
                # helper with three siblings calling it, all in the file you were handed. Worse,
                # the tool then reported "no references found" and suggested it might be dead.
                info = symbols[name]
                if info["file"] == rel and info["line"] == i:
                    continue
                # A bare word match may be a docstring or a task description rather than a call.
                # Both are worth seeing, but only one is a contract you can break, so they are
                # labelled instead of silently mixed.
                hits[name].append((rel, i, "call" if is_call else "text", line.strip()[:104]))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--paths", nargs="*", help="files to analyze instead of the git diff")
    parser.add_argument("--rev", help="compare against this revision instead of the working tree")
    parser.add_argument("--root", default=".", help="repository root to search (default: .)")
    parser.add_argument("--max-per-symbol", type=int, default=12,
                        help="cap the sites listed per symbol, so the report stays readable")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    if unresolvable_rev(root, args.rev):
        print(f"Error: git cannot resolve revision '{args.rev}', so there is nothing to compare "
              "against. Reporting no changed files here would read as a clean tree.",
              file=sys.stderr)
        return 66
    targets = args.paths if args.paths else changed_files(root, args.rev)
    if not targets:
        print("No changed Python files found. Pass --paths explicitly, or check --rev.")
        return 0

    symbols: dict = {}
    unreadable: list[str] = []
    for rel in targets:
        full = rel if os.path.isabs(rel) else os.path.join(root, rel)
        norm = os.path.relpath(full, root).replace(os.sep, "/")
        # "Defines nothing" and "could not be opened" are the same empty list, and this tool
        # exists to say which call sites you must check. Reporting none of them because a file
        # would not decode is the failure it is meant to prevent.
        if read_source(full) is None:
            unreadable.append(norm)
            continue
        for name, line in defined_symbols(full):
            symbols[name] = {"file": norm, "line": line}
    if unreadable:
        print(f"{len(unreadable)} file(s) could not be decoded, so nothing was read from them:")
        for norm in unreadable:
            print(f"    {norm}")
        print("Python reads these; this tool could not. Check the encoding declaration.\n")
    if not symbols:
        readable = [t for t in targets if t not in unreadable]
        if readable:
            print(f"No top-level functions or classes found in: {', '.join(readable)}")
        return 0

    hits = find_callers(root, symbols, python_files(root))
    print(f"Changed files: {', '.join(targets)}")
    print(f"Symbols defined there: {len(symbols)}\n")

    uncalled = []
    for name in sorted(symbols):
        sites = hits[name]
        origin = f"{symbols[name]['file']}:{symbols[name]['line']}"
        if not sites:
            uncalled.append(f"{name} ({origin})")
            continue
        # Real call sites first: those are the ones that can break.
        sites.sort(key=lambda s: (s[2] != "call", s[0], s[1]))
        calls = sum(1 for s in sites if s[2] == "call")
        shown = sites[:args.max_per_symbol]
        print(f"{name}  defined {origin}  -> {calls} call site(s), {len(sites) - calls} text mention(s)")
        for rel, line, kind, text in shown:
            print(f"    [{kind}] {rel}:{line}  {text}")
        if len(sites) > len(shown):
            # Never silently truncate: a hidden call site is the exact failure this tool exists
            # to prevent.
            print(f"    ... and {len(sites) - len(shown)} more (raise --max-per-symbol to see them)")
        print()

    if uncalled:
        print("No references found elsewhere for: " + ", ".join(uncalled))
        print("  Either they are entry points, or they are dead code worth deleting (the ladder")
        print("  prefers deletion). Confirm which before moving on.")
    print("\nEvery [call] site above either must keep working after your change, or must be")
    print("updated to match it. Check them before you run the signal, not after. A [text] line is")
    print("a mention in prose or a docstring: not a contract, but often a claim that just went stale.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
