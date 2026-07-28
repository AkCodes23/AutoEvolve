#!/usr/bin/env python3
"""Measure scripts/ruler.py against real human commits that touch tests.

    python3 scripts/ruler_audit.py --root path/to/some/repo --commits 200

WHY THIS EXISTS. `ruler.py` flags changes to the thing that judges a change, and its whole value
is that a person believes the flag. Human developers edit tests constantly and legitimately, so
the only way to know whether the tool is usable is to run it over commits made by people who were
not gaming anything and count how often it complains.

The bar is stated in `ruler.py` before any measurement was taken: **if more than 25 percent of
human commits touching tests raise a `weakened` finding, that tier is too loose.** This prints the
rate, so the claim can be checked instead of trusted. `--sample` prints findings to hand-audit,
seeded so two people see the same ones.
"""
from __future__ import annotations

import argparse
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ruler  # noqa: E402
from callers import git  # noqa: E402


def commits_touching_rulers(root: str, limit: int, declared: list[str],
                            scan: int = 4000) -> dict[str, list[str]]:
    """Commits that touch a ruler file, mapped to those files.

    One `git log --name-only` rather than a `git show` per commit. The per-commit form spent the
    whole budget on process starts, and against a `--filter=blob:none` clone each one is a network
    round trip, so a 120-commit audit could not finish in two minutes.
    """
    code, out = git(["log", f"-{scan}", "--format=%x00%H", "--name-only", "--no-merges"], root)
    if code != 0:
        raise SystemExit(f"not a git repository, or no history: {root}")
    found: dict[str, list[str]] = {}
    for chunk in out.split("\x00")[1:]:
        lines = chunk.strip().split("\n")
        sha, paths = lines[0].strip(), [p.strip() for p in lines[1:] if p.strip()]
        rulers = [p for p in paths if p.endswith(".py") and ruler.is_ruler(p, declared)]
        if rulers:
            found[sha] = rulers
        if len(found) >= limit:
            break
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".", help="repository to audit")
    parser.add_argument("--commits", type=int, default=100, help="test-touching commits to scan")
    parser.add_argument("--sample", type=int, default=0, help="print N findings to hand-audit")
    parser.add_argument("--seed", type=int, default=20260728)
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    declared = ruler.signal_paths(root)
    by_commit = commits_touching_rulers(root, args.commits, declared)
    shas = list(by_commit)
    if not shas:
        raise SystemExit("no commits touching the ruler were found")

    tiers: collections.Counter = collections.Counter()
    flagged: collections.Counter = collections.Counter()
    every = []
    for sha in shas:
        touched = by_commit[sha]
        worst = None
        names, bodies = set(), set()
        for rel in touched:
            code, text = git(["show", f"{sha}:{rel}"], root)
            if code == 0:
                for name, node in ruler.test_functions(text).items():
                    names.add(name.rsplit(".", 1)[-1])
                    bodies.add(ruler.body_text(node))
        for rel in touched:
            before = git(["show", f"{sha}~1:{rel}"], root)
            after = git(["show", f"{sha}:{rel}"], root)
            if before[0] != 0 or after[0] != 0:
                continue
            for tier, name, message in ruler.compare(
                    before[1], after[1], frozenset(names), frozenset(bodies)):
                tiers[tier] += 1
                every.append((sha[:9], rel, tier, name, message))
                if tier == "weakened":
                    worst = "weakened"
                elif worst is None:
                    worst = "review"
        flagged[worst or "clean"] += 1

    total = len(shas)
    weak = flagged["weakened"]
    print(f"repo    : {root}")
    print(f"commits : {total} that touch the ruler ({'DIRECTION.md: ' + ', '.join(declared) if declared else 'by convention'})")
    print(f"\ncommits raising a `weakened` finding : {weak:4}  ({100 * weak / total:.0f}%)")
    print(f"commits raising only `review`        : {flagged['review']:4}  ({100 * flagged['review'] / total:.0f}%)")
    print(f"commits raising nothing              : {flagged['clean']:4}  ({100 * flagged['clean'] / total:.0f}%)")
    print(f"\ntotal findings: {dict(tiers)}")
    verdict = "PASSES" if 100 * weak / total <= 25 else "FAILS"
    print(f"\nPre-registered bar: `weakened` on at most 25% of human test-touching commits.")
    print(f"  {verdict} at {100 * weak / total:.0f}%.")

    if args.sample and every:
        random.seed(args.seed)
        print(f"\nRandom sample of {min(args.sample, len(every))}, seed {args.seed}:\n")
        for i, (sha, rel, tier, name, message) in enumerate(
                random.sample(every, min(args.sample, len(every))), 1):
            print(f"{i:3}. [{tier}] {sha} {rel}\n     {message[:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
