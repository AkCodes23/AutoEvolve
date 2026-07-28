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
               a docstring built only from the signature, a bare rule of punctuation).
               --strict fails on these alone.
    candidate  a comment whose words are already in the line it describes, whether that is the
               next line or its own. Advisory: read it and decide, it never fails --strict.

TODO, FIXME, HACK, XXX, tool directives (`# type:`, `# noqa`) and the repo's own `evolve:`
markers are left alone: they are work markers, not descriptions.

Python only. Deciding whether a comment holds a statement needs a parser, and the standard
library ships one for this language and no other.

MEASURED ACCURACY, and the limits that come with it. Measured on code nobody here wrote, since
the first calibration used twelve files by one author and shared every habit with the tool.
Noise per KLOC, via `scripts/corpus_audit.py`:

    stdlib 0.57 | jinja2 0.49 | pip 0.30 | setuptools 0.30 | numpy 0.26 | urllib3 0.17
    | click 0.00 | requests 0.47                            (626k lines, 8 corpora)

Two hand audits of 30 random stdlib findings drove every detector here. The residual known
errors, all found that way and all left in deliberately:

  * A banner block (`# ====` / `# Section` / `# ====`) is NOT reported, because the same shape
    is an ASCII table in dataclasses.py, and a missed banner costs less than deleting a drawn
    table. Bare rules with nothing between them are still caught.
  * A block of assignments used as illustration, like traceback.py's `# text = "   foo\\n"`
    above the code computing it, reads as disabled code. One case in 282k lines.
  * A docstring is compared to the signature after removing stopwords only, not verbs, so
    'Get the json charset.' on `json_charset(headers)` is missed. Subtracting verbs too was
    measured: it adds 26 findings on the stdlib, concentrated in the one detector whose audit
    produced the most arguable calls, so the miss is the cheaper error.
"""
from __future__ import annotations

import argparse
import ast
import collections
import io
import os
import re
import sys
import textwrap
import tokenize
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from callers import changed_files, git  # noqa: E402

# `pyright: reportUnusedImport=false` parses as an assignment, so a directive that is not in
# this list gets reported as commented-out code. Found on the first real repository this was
# pointed at, in requests/src/requests/compat.py.
KEEP_PREFIXES = ("todo", "fixme", "hack", "xxx", "evolve:", "type:", "noqa", "pragma",
                 "pylint:", "mypy:", "ruff:", "flake8:", "isort:", "fmt:", "nosec",
                 "pyright:", "pytype:", "bandit:", "yapf:", "black", "codespell:",
                 "cspell:", "spell-checker:", "sourcery", "coding:", "-*-", "!")

# Comments that narrate the change rather than the code: `# Fix: use a parameterized query`.
# This is the single most common thing a model writes, measured. Across 146 comments authored by
# llama-3.1-8b over 90 graded trials, 43 percent matched this shape, at the same rate under every
# ruleset tested including two competitors: 13 under control, 12 under AutoEvolve, 8 under
# karpathy. No wording moved it, which is why it is worth detecting rather than requesting.
#
# It is a candidate and not noise because the tail sometimes carries a real why ("to prevent SQL
# injection"). The `Fix:` framing is still wrong: it addresses a reviewer of the diff, git already
# records that this line changed, and one merge later it describes history rather than code.
# Requiring the colon or dash keeps ordinary prose out, so "# fixed in 3.11, see bpo-12345" and
# "# fix the caller too" do not match.
NARRATION = re.compile(
    r"^(fix|fixed|fixes|change[d]?|update[d]?|add[ed]?|remove[d]?|delete[d]?|modif\w+|"
    r"refactor\w*|rename[d]?|replace[d]?|improve[d]?|new|before|after|old|was)\b\s*[:\-]",
    re.IGNORECASE)

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

CALL_WITH_SPACE = re.compile(r"^\w+(\.\w+)*\s+\(")
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


def quietly_parse(source: str) -> ast.Module | None:
    """Parse without letting the attempt itself say anything.

    Every comment in a file is offered to `ast.parse`, and a perfectly ordinary one like
    `# re.compile("\\s+")` makes it emit a SyntaxWarning about the escape. Those land on stderr
    mixed into the report, blaming `<unknown>:1`, for comments the tool then correctly ignores.
    Whether text parses is a question, not an event worth narrating.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return ast.parse(source)
        except (SyntaxError, ValueError, MemoryError, RecursionError):
            return None


def is_commented_out_code(body: str, trailing: bool = False) -> bool:
    """True when the text after the `#` parses as a statement rather than reading as prose.

    Bare names and literals are rejected on purpose. `# TODO`, `# noqa` and `# ok` all parse
    cleanly as expressions, so requiring a statement (or an expression that calls something) is
    what separates a disabled line of code from an English fragment that happens to be one word.

    `trailing` says the comment sits after live code on the same line, which changes the answer
    for a bare call. You disable a statement by commenting out its whole line, so a lone call
    riding along beside working code is nearly always an annotation: `scale = 2.0 ** -512
    # sqrt(1 / sys.float_info.max)` in statistics.py records where the constant came from.
    """
    body = body.strip()
    if len(body) < 3:
        return False
    wrapped = "def _():\n" + textwrap.indent(body, "    ")
    for source, unwrap in ((body, False), (wrapped, True)):
        tree = quietly_parse(source)
        if tree is None:
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
            # `# Quechua (Peru)` in locale.py parses as a call. Nobody writes `f (x)` in Python
            # and PEP 8 forbids it, so the space is the tell that this is prose.
            return not trailing and not CALL_WITH_SPACE.match(body)
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


def comment_tokens(source: str) -> list[tokenize.TokenInfo]:
    """Every comment token, keeping what was read before an unbalanced file stops the lexer.

    `tokenize` raises TokenError at EOF inside an unclosed bracket, and `list()` around the
    generator throws away every token it had already produced. That turned a file with one stray
    paren into a silent "no comment noise found", which is the same false all-clear a mistyped
    path used to give: an absence of findings has to mean the file was actually read.
    """
    found = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                found.append(token)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return found


def comment_blocks(source: str, lines: list[str]) -> list[list[tokenize.TokenInfo]]:
    """Group consecutive own-line comments at the same indent into one comment.

    Judging each `#` line separately is wrong, and an audit of 30 random findings in the Python
    standard library showed it was the single cause of every false positive: `# module).` in
    dataclasses.py is the tail of a four-line sentence, `# D = C[[int, str], float]` in typing.py
    is an indented example inside an explanation, and `# +-------+-------+-------+` is a row of
    an ASCII table. Each looks like noise alone and is obviously not noise in its block.
    """
    blocks: list[list[tokenize.TokenInfo]] = []
    current: list[tokenize.TokenInfo] = []
    for token in comment_tokens(source):
        row, col = token.start
        own_line = not lines[row - 1][:col].strip()
        joins = (current and own_line and row == current[-1].start[0] + 1
                 and col == current[-1].start[1])
        if joins:
            current.append(token)
            continue
        if current:
            blocks.append(current)
        current = []
        if own_line:
            current = [token]
        else:
            blocks.append([token])
    if current:
        blocks.append(current)
    return blocks


def next_code_line(lines: list[str], start: int) -> tuple[int, str] | None:
    for offset in range(start, min(start + 3, len(lines))):
        text = lines[offset].strip()
        if text and not text.startswith("#"):
            return offset + 1, text
    return None


def file_at_rev(root: str, rel: str, rev: str) -> str | None:
    code, out = git(["show", f"{rev}:{rel}"], root)
    return out if code == 0 else None


def new_findings(path: str, baseline_source: str | None) -> list[tuple[int, str, str]]:
    """Findings in the file now that were not already there in `baseline_source`.

    Adopting this in an existing repository is the case that decides whether anyone keeps it.
    Pointed at `requests`, the hook blocked a clean commit because `utils.py` already carried a
    restating docstring nine hundred lines from the edit. A gate that fails for someone else's
    old comment gets switched off within a day, and then it protects nothing.

    Findings are matched by message, not by line, because inserting a function above one moves
    every line under it without changing a thing about it.
    """
    findings = scan(path)
    if baseline_source is None:
        return findings
    prior = collections.Counter(message for _, _, message in scan_source(baseline_source, path))
    fresh = []
    for line, tier, message in findings:
        if prior[message]:
            prior[message] -= 1
        else:
            fresh.append((line, tier, message))
    return fresh


def scan(path: str) -> list[tuple[int, str, str]]:
    """Every finding in one file as (line, tier, message), ordered by line."""
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except (OSError, UnicodeDecodeError):
        return []
    return scan_source(source, path)


def scan_source(source: str, path: str) -> list[tuple[int, str, str]]:
    lines = source.splitlines()

    found: list[tuple[int, str, str]] = []
    tree = quietly_parse(source)
    if tree is not None:
        found.extend(find_vacuous_docstrings(tree))

    for block in comment_blocks(source, lines):
        row = block[0].start[0]
        raws = [t.string.lstrip("#").strip() for t in block]
        # Keep the leading whitespace: a disabled `if`/`return` pair only parses as a
        # block because of how its lines are indented relative to each other.
        indented = [t.string[1:] if t.string.startswith("#") else t.string
                    for t in block]
        bodies = [undecorate(r) for r in raws]
        if any(b.lower().startswith(KEEP_PREFIXES) for b in bodies if b):
            continue
        if len(block) > 1:
            found.extend(judge_block(row, raws, bodies, indented))
            continue
        token, raw, body = block[0], raws[0], bodies[0]
        if not raw:
            continue
        if is_divider(raw):
            found.append((row, "noise", f"# {raw[:88]}  (decoration, not information)"))
            continue
        if not body:
            continue
        before = lines[row - 1][:token.start[1]].strip()
        if is_commented_out_code(body, trailing=bool(before)):
            found.append((row, "noise", f"# {body[:88]}  (commented-out code: delete it, "
                                        "git remembers)"))
            continue
        if NARRATION.match(body):
            found.append((row, "candidate", narration_message(body)))
            continue
        described = (row, before) if before else next_code_line(lines, row)
        if described is None:
            continue
        content = words(body) - STOPWORDS - VERBS
        if content and content <= words(described[1]):
            where = "its own line" if before else f"line {described[0]}"
            found.append((row, "candidate", f"# {body[:88]}\n        restates {where}:  "
                                            f"{described[1][:88]}"))
    return sorted(found)


def narration_message(body: str) -> str:
    return (f"# {body[:88]}\n        narrates the change, not the code: git already records "
            "that this line changed. Keep the why, drop the framing.")


def judge_block(row: int, raws: list[str], bodies: list[str],
                indented: list[str]) -> list[tuple[int, str, str]]:
    """A multi-line comment is prose unless every one of its lines is code.

    Restatement is not tested here at all. A comment that needed several lines is explaining
    something, and matching its last line against the code that follows compares a sentence
    fragment to an unrelated statement, which is how `# module).` came to be a finding.
    """
    # Before the emptiness guard: undecorate() reduces a bare rule to "", so a block of nothing
    # but rules has no written content and would otherwise return early as unremarkable.
    rules = [r for r in raws if r and is_divider(r)]
    if rules and all(is_divider(r) for r in raws if r):
        return [(row, "noise", f"# {raws[0][:88]}  ({len(raws)} lines of decoration)")]
    written = [b for b in bodies if b]
    if not written:
        return []
    if is_commented_out_block(indented) or all(is_commented_out_code(b) for b in written):
        return [(row, "noise", f"# {written[0][:76]}  (commented-out code block, "
                               f"{len(written)} lines: delete it, git remembers)")]
    if NARRATION.match(written[0]):
        return [(row, "candidate", narration_message(written[0]))]
    return []


def is_commented_out_block(indented: list[str]) -> bool:
    """True when the block's lines parse together as code, even though none parses alone.

    Disabling a branch produces `# if x is None:` above `#     return None`, and neither line is
    valid Python by itself: the first has no body, the second is a return outside a function.
    Judging them one at a time therefore misses the most worthwhile thing this tool can find.
    Their original indentation relative to each other is what makes them parse, so it is kept.
    """
    snippet = textwrap.dedent("\n".join(indented)).strip("\n")
    if not snippet.strip() or "\n" not in snippet:
        return False
    for source in (snippet, "def _():\n" + textwrap.indent(snippet, "    ")):
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError, MemoryError, RecursionError):
            continue
        body = tree.body[0].body if source is not snippet else tree.body
        if body and all(isinstance(n, CODE_NODES) or isinstance(n, ast.Expr)
                        and isinstance(n.value, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom))
                        for n in body):
            return True
    return False


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
    """The files to scan, refusing a path the caller named but that is not there.

    An unreadable file scanned to zero findings, so a mistyped `--paths` printed "no comment noise
    found" and the caller read a clean bill of health for a file that was never opened. A tool
    whose good news is an absence has to be loud about the difference between "nothing wrong" and
    "nothing looked at".
    """
    if paths:
        missing = [p for p in paths
                   if not os.path.isfile(p if os.path.isabs(p) else os.path.join(root, p))]
        if missing:
            raise SystemExit(f"no such file: {', '.join(missing)}")
        skipped = [p for p in paths if not p.endswith(".py")]
        if skipped:
            print(f"Skipping non-Python path(s): {', '.join(skipped)}", file=sys.stderr)
        return [p for p in paths if p.endswith(".py")]
    if staged:
        return [p for p in staged_files(root) if os.path.isfile(os.path.join(root, p))]
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
    parser.add_argument("--baseline", metavar="REV",
                        help="report only findings this change introduced, hiding what the file "
                             "already carried at REV. --staged implies --baseline HEAD, so "
                             "adopting the hook in an existing repo does not block on someone "
                             "else's old comment. Pass --baseline '' to see everything.")
    args = parser.parse_args()

    # A comment holding any character outside the console codepage crashed the report on Windows
    # partway through, losing every finding after it. requests/src/requests/status_codes.py has a
    # U+2717 in one. Findings matter more than glyph fidelity, so unencodable characters degrade.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    root = os.path.abspath(args.root)
    targets = python_targets(root, args.paths, args.rev, args.staged)
    baseline = args.baseline
    if baseline is None and args.staged:
        baseline = "HEAD"
    if not targets:
        print("No changed Python files found. Pass --paths explicitly, or check --rev.")
        return 0

    noise = candidates = hidden = 0
    for target in sorted(targets):
        full = target if os.path.isabs(target) else os.path.join(root, target)
        rel = os.path.relpath(full, root).replace(os.sep, "/")
        prior_source = file_at_rev(root, rel, baseline) if baseline else None
        findings = new_findings(full, prior_source)
        hidden += len(scan(full)) - len(findings)
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

    carried = (f" ({hidden} pre-existing finding(s) not introduced by this change are hidden; "
               f"re-run without --baseline to see them)" if hidden else "")
    if not noise and not candidates:
        print(f"No comment noise found in {len(targets)} file(s).{carried}")
        return 0

    print(f"{noise} noise, {candidates} candidate across {len(targets)} file(s).{carried}")
    print("Delete the noise. For each candidate, keep the comment only if it records something")
    print("the code cannot: a measured result, a rejected alternative, a caveat. If it just")
    print("narrates the line below, the better fix is usually a clearer name.")
    return 1 if args.strict and noise else 0


if __name__ == "__main__":
    sys.exit(main())
