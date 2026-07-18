#!/usr/bin/env python3
"""AutoEvolve self-check: the repo's own signal.

Runs the invariants this repo promises. No dependencies, standard library only.
Exit code 0 if everything holds, 1 (with a report) otherwise. Run it before you
commit, and let CI run it on every change:

    python3 scripts/check.py
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADAPTERS = ["adapters/cursor.mdc", "adapters/windsurf.md", "adapters/copilot-instructions.md"]

failures: list[str] = []


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT)


def markdown_files() -> list[str]:
    out = []
    for dp, dirs, files in os.walk(ROOT):
        if os.sep + ".git" in dp:
            continue
        for f in files:
            if f.endswith((".md", ".mdc")):
                out.append(os.path.join(dp, f))
    return sorted(out)


def all_text_files() -> list[str]:
    out = []
    for dp, dirs, files in os.walk(ROOT):
        if os.sep + ".git" in dp:
            continue
        for f in files:
            if f.endswith((".md", ".mdc", ".py", ".yml", ".yaml", ".sh", ".toml", ".cff", ".txt")):
                out.append(os.path.join(dp, f))
    return sorted(out)


def check_no_em_dashes() -> None:
    hits = []
    for path in markdown_files():
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            if "—" in line or "–" in line:
                hits.append(f"  {rel(path)}:{i}")
    if hits:
        failures.append("Em/en dashes found (use commas, colons, or parentheses):\n" + "\n".join(hits))


def check_no_forbidden_word() -> None:
    # The mindset is tool-neutral: no specific assistant product name in the content.
    hits = []
    for path in all_text_files():
        if rel(path) == os.path.join("scripts", "check.py"):
            continue  # this file names the rule
        for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
            if re.search(r"claude", line, re.IGNORECASE):
                hits.append(f"  {rel(path)}:{i}")
    if hits:
        failures.append("Tool-specific product name found (keep the mindset tool-neutral):\n" + "\n".join(hits))


def check_links_resolve() -> None:
    link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    hits = []
    for path in markdown_files():
        base = os.path.dirname(path)
        for target in link.findall(open(path, encoding="utf-8").read()):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            rel_target = target.split("#")[0]
            if not rel_target:
                continue
            if not os.path.exists(os.path.normpath(os.path.join(base, rel_target))):
                hits.append(f"  {rel(path)} -> {target}")
    if hits:
        failures.append("Broken internal links:\n" + "\n".join(hits))


def _body_after_frontmatter(text: str) -> str:
    # Strip a leading YAML frontmatter block (--- ... ---) if present.
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            return text[nl + 1 :] if nl != -1 else ""
    return text


def check_adapters_in_sync() -> None:
    bodies = {}
    for path in ADAPTERS:
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            failures.append(f"Missing adapter: {path}")
            continue
        bodies[path] = _body_after_frontmatter(open(full, encoding="utf-8").read()).strip()
    uniq = set(bodies.values())
    if len(uniq) > 1:
        failures.append(
            "Adapter condensed cores have drifted apart (their bodies must be identical; "
            "edit AGENTS.md and re-sync all three):\n  " + "\n  ".join(bodies.keys())
        )


def check_canonical_source_exists() -> None:
    for required in ["AGENTS.md", "README.md", "LICENSE"]:
        if not os.path.exists(os.path.join(ROOT, required)):
            failures.append(f"Missing required file: {required}")


def main() -> int:
    check_canonical_source_exists()
    check_no_em_dashes()
    check_no_forbidden_word()
    check_links_resolve()
    check_adapters_in_sync()

    if failures:
        print("AutoEvolve self-check FAILED:\n")
        print("\n\n".join(failures))
        print(f"\n{len(failures)} check(s) failed.")
        return 1
    print("AutoEvolve self-check passed: no em dashes, tool-neutral, links resolve, adapters in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
