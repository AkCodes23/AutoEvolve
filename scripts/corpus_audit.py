#!/usr/bin/env python3
"""Measure the comment reporter against a corpus nobody here wrote.

    python3 scripts/corpus_audit.py                    # the Python standard library
    python3 scripts/corpus_audit.py --root path/to/repo
    python3 scripts/corpus_audit.py --sample 30        # print a random sample to hand-audit

WHY THIS EXISTS. `scripts/comments.py` was first calibrated against twelve files written by one
author in one week, which is the weakest possible evidence for a false-positive claim: the tool
and the corpus shared every habit. Pointing it at 282k lines of standard library written by
hundreds of people over decades found five false positives in two sittings, and each one became
a test. A rate quoted from a corpus you cannot re-measure is an anecdote, so this is the command
that produced the numbers in that module's docstring.

The sample is seeded, so `--sample 30` gives the same 30 findings on the same corpus every time
and an audit of it can be checked by someone else. Findings per KLOC will still drift with the
Python version supplying the corpus; the point is the method and the sample, not a frozen number.
"""
from __future__ import annotations

import argparse
import collections
import os
import random
import sys
import sysconfig

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comments  # noqa: E402
from callers import SKIP_DIRS  # noqa: E402

# `test` holds deliberately broken fixtures, and `lib2to3`/`idlelib` are frozen or unmaintained,
# so findings there say nothing about code anyone reviews.
CORPUS_SKIP = SKIP_DIRS | {"test", "tests", "idlelib", "lib2to3", "turtledemo"}


def python_files(root: str) -> list[str]:
    found = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in CORPUS_SKIP]
        found.extend(os.path.join(dirpath, f) for f in files if f.endswith(".py"))
    return sorted(found)


def kind_of(message: str) -> str:
    for needle, name in (("commented-out", "commented-out code"), ("decoration", "decoration"),
                         ("already say", "vacuous docstring"), ("narrates", "diff narration")):
        if needle in message:
            return name
    return "restates the code"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="corpus root (default: this interpreter's stdlib)")
    parser.add_argument("--sample", type=int, default=0,
                        help="print N random findings to hand-audit (seeded, so reproducible)")
    parser.add_argument("--seed", type=int, default=20260728)
    args = parser.parse_args()

    root = os.path.abspath(args.root or sysconfig.get_paths()["stdlib"])
    files = python_files(root)
    if not files:
        raise SystemExit(f"no Python files under {root}")

    lines = 0
    tiers: collections.Counter = collections.Counter()
    kinds: collections.Counter = collections.Counter()
    every = []
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                lines += sum(1 for _ in handle)
        except OSError:
            continue
        for line, tier, message in comments.scan(path):
            tiers[tier] += 1
            kinds[kind_of(message)] += 1
            every.append((os.path.relpath(path, root).replace(os.sep, "/"), line, tier, message))

    print(f"corpus : {root}")
    print(f"         {len(files)} files, {lines:,} lines")
    print(f"noise    : {tiers['noise']:5}  ({1000 * tiers['noise'] / lines:.2f} per KLOC)")
    print(f"candidate: {tiers['candidate']:5}  ({1000 * tiers['candidate'] / lines:.2f} per KLOC)")
    for kind, count in kinds.most_common():
        print(f"    {kind:22} {count:5}")

    if args.sample and every:
        random.seed(args.seed)
        print(f"\nRandom sample of {min(args.sample, len(every))}, seed {args.seed}. Judge each")
        print("as right, defensible, or wrong. A wrong one is a bug: fix the detector and add the")
        print("case to scripts/test_comments.py, which is how every case in that file got there.\n")
        for i, (rel, line, tier, message) in enumerate(
                random.sample(every, min(args.sample, len(every))), 1):
            print(f"{i:3}. [{tier}] {rel}:{line}\n     {message.splitlines()[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
