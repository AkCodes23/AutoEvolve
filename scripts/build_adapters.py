#!/usr/bin/env python3
"""Generate the per-tool adapters from one source: adapters/_core.md.

Every inline adapter is the same condensed core with a different (or no) frontmatter.
Editing four files by hand is how they drift, so instead edit `adapters/_core.md` once and
run this to re-stamp them all:

    python3 scripts/build_adapters.py

`--check` writes nothing and exits non-zero if any committed adapter is stale (used by CI
and by scripts/check.py). No dependencies, standard library only.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "adapters", "_core.md")

# path -> frontmatter prepended before the shared core ("" means no frontmatter).
ADAPTERS: dict[str, str] = {
    "adapters/claude.md": "",
    "adapters/copilot-instructions.md": "",
    "adapters/cursor.mdc": (
        "---\n"
        "description: AutoEvolve operating mindset, small, verified, kept-if-better changes; simplify relentlessly.\n"
        "globs:\n"
        "alwaysApply: true\n"
        "---\n\n"
    ),
    "adapters/windsurf.md": (
        "---\n"
        "trigger: always_on\n"
        "description: AutoEvolve operating mindset, small, verified, kept-if-better changes; simplify relentlessly.\n"
        "---\n\n"
    ),
}


def render(frontmatter: str) -> str:
    return frontmatter + open(CORE, encoding="utf-8").read()


def build(check: bool = False) -> list[str]:
    """Write every adapter (check=False) or return the list of stale ones (check=True)."""
    stale = []
    for path, frontmatter in ADAPTERS.items():
        full = os.path.join(ROOT, path)
        content = render(frontmatter)
        if check:
            current = open(full, encoding="utf-8").read() if os.path.exists(full) else None
            if current != content:
                stale.append(path)
        else:
            with open(full, "w", encoding="utf-8") as f:
                f.write(content)
    return stale


def main() -> int:
    check = "--check" in sys.argv
    stale = build(check=check)
    if check:
        if stale:
            print("Adapters are stale. Run: python3 scripts/build_adapters.py")
            for p in stale:
                print("  " + p)
            return 1
        print("Adapters are up to date with adapters/_core.md.")
        return 0
    print(f"Wrote {len(ADAPTERS)} adapters from adapters/_core.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
