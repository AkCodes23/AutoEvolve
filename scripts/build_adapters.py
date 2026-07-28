#!/usr/bin/env python3
"""Generate the per-tool adapters from one source: AGENTS.md.

There is exactly one mindset profile and it lives in AGENTS.md. Every inline adapter is that
same file with a different (or no) frontmatter. Editing four files by hand is how they drift, so
instead edit `AGENTS.md` once and run this to re-stamp them all:

    python3 scripts/build_adapters.py

`--check` writes nothing and exits non-zero if any committed adapter is stale (used by CI
and by scripts/check.py). No dependencies, standard library only.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "AGENTS.md")

LF = chr(10)
CRLF = chr(13) + chr(10)

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


def render(frontmatter: str) -> bytes:
    """The adapter's exact bytes, always LF.

    Rendered and compared as BYTES on purpose. Text mode normalizes newlines on read AND write, so
    `--check` used to report an adapter "up to date" when a rebuild would change every line ending
    in it: on Windows the committed adapters were CRLF while the source was LF, a 42-byte
    difference the invariant could not see. .gitattributes pins the repo to LF; this makes the
    generator agree with it rather than with the platform.
    """
    with open(SOURCE, encoding="utf-8", newline="") as handle:
        body = handle.read().replace(CRLF, LF)
    return (frontmatter + body).encode("utf-8")


def build(check: bool = False) -> list[str]:
    """Write every adapter (check=False) or return the list of stale ones (check=True)."""
    stale = []
    for path, frontmatter in ADAPTERS.items():
        full = os.path.join(ROOT, path)
        content = render(frontmatter)
        if check:
            current = open(full, "rb").read() if os.path.exists(full) else None
            if current != content:
                stale.append(path)
        else:
            with open(full, "wb") as f:
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
        print("Adapters are up to date with AGENTS.md.")
        return 0
    print(f"Wrote {len(ADAPTERS)} adapters from AGENTS.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
