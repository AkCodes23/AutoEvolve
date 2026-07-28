#!/usr/bin/env python3
"""Report the comment noise in the code you just changed.

    python scripts/comments.py                      # comments in your uncommitted changes
    python scripts/comments.py --paths src/api.py   # specific files
    python scripts/comments.py --rev HEAD~3         # comments changed since a revision
    python scripts/comments.py --strict             # exit 1 when noise is found (for a hook)

WHY THIS EXISTS. The mindset asks for direct code: a comment earns its place only by recording
what the code cannot say, and one that restates the line below it is a second copy of the truth
that nothing keeps in sync. Asking an agent for that is cheap and, on this repository's own
measurements, does nothing: across roughly 580 graded trials, more instruction text produced no
detectable change in behaviour. So this does the reading instead of requesting it, the way
scripts/callers.py does, and puts the specific lines in front of you.

It reports and never rewrites, because deleting a comment is a judgement about whether the
sentence carries a why, and that judgement is yours. Two tiers are printed:

    noise      a comment that provably says nothing the code does not (commented-out code,
               a docstring built only from the signature, a decoration bar). --strict fails
               on these alone.
    candidate  a comment that looks like a restatement of the next line. Read it and decide.

TODO, FIXME, HACK, XXX, tool directives (`# type:`, `# noqa`) and the repo's own `evolve:`
markers are left alone: they are work markers, not descriptions.

Python only. Deciding whether a comment holds a statement needs a parser, and the standard
library ships one for this language and no other.
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys
import textwrap
import tokenize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from callers import changed_files, git  # noqa: E402

KEEP_PREFIXES = ("todo", "fixme", "hack", "xxx", "evolve:", "type:", "noqa", "pragma",
                 "pylint:", "mypy:", "ruff:", "flake8:", "isort:", "fmt:", "nosec",
                 "coding:", "-*-", "!")

# `ast.Global`/`ast.Nonlocal` are deliberately absent: "# global state" is ordinary prose that
# parses as a Global statement, and one false positive in a report costs more than the rare
# commented-out `global` it would have caught.
CODE_NODES = (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Return, ast.Import, ast.ImportFrom,
              ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.For, ast.AsyncFor,
              ast.While, ast.If, ast.With, ast.AsyncWith, ast.Try, ast.Raise, ast.Assert,
              ast.Delete, ast.Pass, ast.Break, ast.Continue)

STOPWORDS = {
    "a", "an", "the", "this", "that", "these", "those", "it", "its", "we", "you", "i", "is",
    "are", "was", "were", "be", "been", "being", "do", "does", "did", "has", "have", "had",
    "of", "to", "in", "on", "at", "by", "for", "from", "with", "as", "and", "or", "but", "if",
    "then", "so", "not", "no", "all", "any", "each", "per", "into", "out", "up", "down",
    "over", "here", "there", "when", "where", "which", "what", "how", "just", "only", "now",
    "given", "one", "will", "would", "can", "should", "must", "may", "else", "than", "them",
}

# Subtracted from a comment before comparing it to the next line, where the verb is almost never
# an identifier: "# set the user name" above `user.name = name` restates it, and the only word
# stopping the comparison from seeing that is "set".
VERBS = {
    "set", "get", "create", "make", "build", "return", "returns", "check", "add", "remove",
    "update", "initialize", "init", "loop", "iterate", "call", "define", "declare", "increment",
    "decrement", "print", "open", "close", "read", "write", "start", "stop", "run", "handle",
    "compute", "calculate", "convert", "parse", "store", "save", "load", "find", "fetch",
    "append", "insert", "delete", "clear", "reset", "apply", "assign", "instantiate", "setup",
}

WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*")
PART = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z][a-z0-9]*")
DIVIDER_CHARS = "=-*~_+#.<>|/ "


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def words(text: str) -> set[str]:
    """The lowercase word stems in a string, splitting camelCase and snake_case identifiers."""
    found: set[str] = set()
    for token in WORD.findall(text):
        for part in PART.findall(token):
            found.add(_stem(part.lower()))
    return found


def is_commented_out_code(body: str) -> bool:
    """True when the text after the `#` parses as a statement rather than reading as prose.

    Bare names and literals are rejected on purpose. `# TODO`, `# noqa` and `# ok` all parse
    cleanly as expressions, so requiring a statement (or an expression that calls something) is
    what separates a disabled line of code from an English fragment that happens to be one word.
    """
    body = body.strip()
    if len(body) < 3:
        return False
    wrapped = "def _():\n" + textwrap.indent(body, "    ")
    for source, unwrap in ((body, False), (wrapped, True)):
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError, MemoryError, RecursionError):
            continue
        node = tree.body[0] if tree.body else None
        if unwrap:
            node = node.body[0] if node is not None and getattr(node, "body", None) else None
        if node is None:
            continue
        # A bare annotation is where prose most often sneaks through: `# ponytail: "one guard in
        # the shared function is a smaller diff"` parses as AnnAssign, and so does any
        # `Label: "quoted sentence"`. Real disabled code assigns something.
        if isinstance(node, ast.AnnAssign):
            return node.value is not None
        if isinstance(node, CODE_NODES):
            return True
        if isinstance(node, ast.Expr) and isinstance(
                node.value, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom, ast.NamedExpr)):
            return True
    return False


def is_divider(body: str) -> bool:
    """True only for a bare rule. A banner with words in it is judged on those words instead.

    `# --- 4. regression canary: ledger row shape ---` is decorated, but the decoration is not
    the content: it names what the next block does, in a file with nine numbered checks. Calling
    that noise would fail a commit over punctuation, so undecorate() strips the rules and the
    remaining sentence goes through the same tests as any other comment.
    """
    stripped = body.strip()
    return len(stripped) >= 4 and all(c in DIVIDER_CHARS for c in stripped)


def undecorate(body: str) -> str:
    return re.sub(r"[=\-*~_#]{3,}\s*$", "", re.sub(r"^[=\-*~_#]{3,}\s*", "", body.strip())).strip()


def signature_words(node: ast.AST) -> set[str]:
    found = words(node.name)
    args = getattr(node, "args", None)
    if isinstance(args, ast.arguments):
        every = [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]
        for arg in every:
            if arg is not None:
                found |= words(arg.arg)
    return found


def find_vacuous_docstrings(tree: ast.AST) -> list[tuple[int, str, str]]:
    """One-line docstrings whose every word already appears in the name and parameters."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        doc = ast.get_docstring(node, clean=True)
        if doc is None or "\n" in doc.strip():
            continue
        if words(doc) - STOPWORDS <= signature_words(node):
            line = node.body[0].lineno
            found.append((line, "noise", f'"""{doc.strip()}"""  (says only what `{node.name}` '
                                         "and its parameters already say)"))
    return found


def next_code_line(lines: list[str], start: int) -> tuple[int, str] | None:
    for offset in range(start, min(start + 3, len(lines))):
        text = lines[offset].strip()
        if text and not text.startswith("#"):
            return offset + 1, text
    return None


def scan(path: str) -> list[tuple[int, str, str]]:
    """Every finding in one file as (line, tier, message), ordered by line."""
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except (OSError, UnicodeDecodeError):
        return []
    lines = source.splitlines()

    found: list[tuple[int, str, str]] = []
    try:
        found.extend(find_vacuous_docstrings(ast.parse(source, filename=path)))
    except (SyntaxError, ValueError):
        pass

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        tokens = []

    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        row = token.start[0]
        raw = token.string.lstrip("#").strip()
        if not raw:
            continue
        if is_divider(raw):
            found.append((row, "noise", f"# {raw[:88]}  (decoration, not information)"))
            continue
        body = undecorate(raw)
        if not body or body.lower().startswith(KEEP_PREFIXES):
            continue
        if is_commented_out_code(body):
            found.append((row, "noise", f"# {body[:88]}  (commented-out code: delete it, "
                                        "git remembers)"))
            continue
        before = lines[row - 1][:token.start[1]].strip()
        described = (row, before) if before else next_code_line(lines, row)
        if described is None:
            continue
        content = words(body) - STOPWORDS - VERBS
        if content and content <= words(described[1]):
            where = "its own line" if before else f"line {described[0]}"
            found.append((row, "candidate", f"# {body[:88]}\n        restates {where}:  "
                                            f"{described[1][:88]}"))
    return sorted(found)


def staged_files(root: str) -> list[str]:
    """The Python files in the index.

    A pre-commit hook wants exactly this set, and reading it here rather than expanding it in
    the hook's shell keeps a path containing a space from silently becoming two arguments.
    """
    code, out = git(["diff", "--cached", "--name-only", "--diff-filter=ACM"], root)
    if code != 0:
        return []
    return sorted(name for name in out.splitlines() if name.endswith(".py"))


def python_targets(root: str, paths: list[str] | None, rev: str | None, staged: bool) -> list[str]:
    if paths:
        return [p for p in paths if p.endswith(".py")]
    if staged:
        return [p for p in staged_files(root) if os.path.exists(os.path.join(root, p))]
    return changed_files(root, rev)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--paths", nargs="*", help="files to analyze instead of the git diff")
    parser.add_argument("--rev", help="compare against this revision instead of the working tree")
    parser.add_argument("--staged", action="store_true",
                        help="analyze the Python files in the index (for a pre-commit hook)")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--max-per-file", type=int, default=20,
                        help="cap the findings listed per file, so the report stays readable")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 if any noise is found; candidates never fail")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    targets = python_targets(root, args.paths, args.rev, args.staged)
    if not targets:
        print("No changed Python files found. Pass --paths explicitly, or check --rev.")
        return 0

    noise = candidates = 0
    for rel in sorted(targets):
        full = rel if os.path.isabs(rel) else os.path.join(root, rel)
        findings = scan(full)
        if not findings:
            continue
        shown = findings[:args.max_per_file]
        print(f"{rel}  -> {sum(1 for f in findings if f[1] == 'noise')} noise, "
              f"{sum(1 for f in findings if f[1] == 'candidate')} candidate")
        for line, tier, message in shown:
            print(f"    [{tier}] {rel}:{line}  {message}")
        if len(findings) > len(shown):
            print(f"    ... and {len(findings) - len(shown)} more "
                  "(raise --max-per-file to see them)")
        print()
        noise += sum(1 for f in findings if f[1] == "noise")
        candidates += sum(1 for f in findings if f[1] == "candidate")

    if not noise and not candidates:
        print(f"No comment noise found in {len(targets)} file(s).")
        return 0

    print(f"{noise} noise, {candidates} candidate across {len(targets)} file(s).")
    print("Delete the noise. For each candidate, keep the comment only if it records something")
    print("the code cannot: a measured result, a rejected alternative, a caveat. If it just")
    print("narrates the line below, the better fix is usually a clearer name.")
    return 1 if args.strict and noise else 0


if __name__ == "__main__":
    sys.exit(main())
