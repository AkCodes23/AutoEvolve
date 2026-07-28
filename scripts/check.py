#!/usr/bin/env python3
"""AutoEvolve self-check: the repo's own signal.

Runs the invariants this repo promises. No dependencies, standard library only.
Exit code 0 if everything holds, 1 (with a report) otherwise. Run it before you
commit, and let CI run it on every change:

    python3 scripts/check.py
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

failures: list[str] = []


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT)


def read_lines(path: str) -> list[str]:
    """Read a markdown file without letting one bad byte abort the whole self-check.

    A hard `encoding="utf-8"` open used to raise a UnicodeDecodeError that did not name the
    offending file, and because it escaped before the remaining invariants ran, a single stray
    byte silently disabled every other check.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.readlines()
    except UnicodeDecodeError as exc:
        failures.append(f"{rel(path)} is not valid UTF-8 ({exc.reason} at byte {exc.start}).")
        return []


# Directories that are never this project's prose. Pruned rather than filtered so the walk does
# not descend into a vendored tree: a single dependency's markdown could otherwise fail this
# repo's self-check on files nobody here wrote.
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
             ".venv", "venv", ".mypy_cache", ".tox", "site-packages", ".code-review-graph"}


def markdown_files() -> list[str]:
    out = []
    for dp, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".md", ".mdc")):
                out.append(os.path.join(dp, f))
    return sorted(out)


def check_no_em_dashes() -> None:
    hits = []
    for path in markdown_files():
        for i, line in enumerate(read_lines(path), 1):
            if "—" in line or "–" in line:
                hits.append(f"  {rel(path)}:{i}")
    if hits:
        failures.append("Em/en dashes found (use commas, colons, or parentheses):\n" + "\n".join(hits))


# The mindset core must work with any tool, so it should not name a specific assistant
# product. The generated adapters, the README, and INSTALL are exempt: those legitimately name
# tools. AGENTS.md is the single profile and the file the installers write into a target, so it is
# the most important file this invariant protects. The generated adapters are exempt because they
# legitimately carry tool-specific frontmatter.
CORE = ("AGENTS.md", "templates/", "skills/", "commands/",
        "docs/PRINCIPLES.md", "docs/EXAMPLE.md", "docs/CHECKLIST.md")
ASSISTANT_PRODUCTS = ["claude", "cursor", "copilot", "windsurf", "codex", "antigravity", "gemini", "cline", "devin"]


def check_core_is_tool_neutral() -> None:
    pat = re.compile(r"\b(" + "|".join(ASSISTANT_PRODUCTS) + r")\b", re.IGNORECASE)
    hits = []
    for path in markdown_files():
        r = rel(path).replace(os.sep, "/")
        if not r.startswith(CORE):
            continue
        for i, line in enumerate(read_lines(path), 1):
            m = pat.search(line)
            if m:
                hits.append(f"  {r}:{i} (names '{m.group(0)}')")
    if hits:
        failures.append(
            "The mindset core names a specific tool. Keep AGENTS.md and the core "
            "tool-neutral; tool names belong in adapters/:\n" + "\n".join(hits)
        )


def resolves_with_exact_case(full_path: str) -> bool:
    """True only if every path component matches the on-disk spelling exactly.

    `os.path.exists` is case-insensitive on Windows and case-sensitive on Linux, so a link
    written as `docs/Principles.md` passed the self-check on a Windows author's machine and
    failed CI on a byte-identical tree. Comparing each component against the real directory
    listing gives both platforms the same answer, which is the whole point of an invariant.
    """
    full_path = os.path.normpath(full_path)
    if not os.path.exists(full_path):
        return False
    current = full_path
    while True:
        parent, name = os.path.split(current)
        if not name or parent == current:
            return True
        if os.path.abspath(current) == os.path.abspath(ROOT):
            return True
        try:
            if name not in os.listdir(parent or "."):
                return False
        except OSError:
            return False
        current = parent


def check_links_resolve() -> None:
    link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    hits = []
    for path in markdown_files():
        base = os.path.dirname(path)
        for target in link.findall("".join(read_lines(path))):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            rel_target = target.split("#")[0]
            if not rel_target:
                continue
            resolved = os.path.normpath(os.path.join(base, rel_target))
            if not os.path.exists(resolved):
                hits.append(f"  {rel(path)} -> {target}")
            elif not resolves_with_exact_case(resolved):
                hits.append(f"  {rel(path)} -> {target} (wrong case: resolves here but not on Linux)")
    if hits:
        failures.append("Broken internal links:\n" + "\n".join(hits))


def check_adapters_generated() -> None:
    # The adapters are generated from AGENTS.md by scripts/build_adapters.py.
    # Verify the committed files match, so a hand-edit that forgets the rebuild fails here.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_adapters

    stale = build_adapters.build(check=True)
    if stale:
        failures.append(
            "Adapters are stale vs AGENTS.md. Run: python3 scripts/build_adapters.py\n  "
            + "\n  ".join(stale)
        )


def check_canonical_source_exists() -> None:
    for required in ["AGENTS.md", "README.md", "LICENSE"]:
        if not os.path.exists(os.path.join(ROOT, required)):
            failures.append(f"Missing required file: {required}")


def check_plugin_json_valid() -> None:
    # The Claude Code plugin manifests must be valid JSON or the install path breaks.
    d = os.path.join(ROOT, ".claude-plugin")
    if not os.path.isdir(d):
        return
    for name in sorted(os.listdir(d)):
        if name.endswith(".json"):
            try:
                json.load(open(os.path.join(d, name), encoding="utf-8"))
            except Exception as e:  # noqa: BLE001 - report any parse failure
                failures.append(f"Invalid JSON in .claude-plugin/{name}: {e}")


def main() -> int:
    check_canonical_source_exists()
    check_no_em_dashes()
    check_core_is_tool_neutral()
    check_links_resolve()
    check_adapters_generated()
    check_plugin_json_valid()

    if failures:
        print("AutoEvolve self-check FAILED:\n")
        print("\n\n".join(failures))
        print(f"\n{len(failures)} check(s) failed.")
        return 1
    print("AutoEvolve self-check passed: no em dashes, the mindset stays tool-neutral, links resolve, adapters generated from AGENTS.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
