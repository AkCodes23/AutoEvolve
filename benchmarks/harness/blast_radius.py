"""AST Caller & Blast Radius Integrity Analyzer."""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Add AutoEvolve scripts to path if available for callers detection
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "AutoEvolve", "scripts"))
if os.path.exists(SCRIPTS_DIR) and SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from callers import defined_symbols, find_callers, python_files, read_source
except ImportError:
    # Fallback AST caller parsing if script is moved or imported in isolation
    import ast
    import re
    import tokenize

    def read_source(path: str) -> Optional[str]:
        try:
            with tokenize.open(path) as handle:
                return handle.read()
        except Exception:
            return None

    def defined_symbols(path: str) -> List[tuple[str, int]]:
        source = read_source(path)
        if not source:
            return []
        try:
            tree = ast.parse(source, filename=path)
        except Exception:
            return []
        found = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.append((node.name, node.lineno))
                if isinstance(node, ast.ClassDef):
                    for child in node.body:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("_"):
                            found.append((child.name, child.lineno))
        return [(name, line) for name, line in found if not name.startswith("__")]

    def python_files(root: str) -> List[str]:
        out = []
        for dirpath, _, files in os.walk(root):
            out.extend(os.path.join(dirpath, f) for f in files if f.endswith(".py"))
        return out

    def find_callers(root: str, symbols: dict, corpus: List[str]) -> dict:
        hits = {name: [] for name in symbols}
        if not symbols:
            return hits
        scanner = re.compile(r"\b(" + "|".join(re.escape(n) for n in sorted(symbols)) + r")\b")
        for path in corpus:
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                if scanner.search(line) is None:
                    continue
                for match in scanner.finditer(line):
                    name = match.group(1)
                    rest = line[match.end():]
                    is_call = rest[:1] == "(" or rest.lstrip()[:1] == "("
                    info = symbols[name]
                    if info["file"] == rel and info["line"] == i:
                        continue
                    hits[name].append((rel, i, "call" if is_call else "text", line.strip()[:104]))
        return hits


def get_git_changed_files(repo_or_dir: str) -> List[str]:
    """Get list of modified/staged/untracked files relative to the directory."""
    changed: set[str] = set()
    for cmd in [
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]:
        try:
            res = subprocess.run(
                cmd,
                cwd=repo_or_dir,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if res.returncode == 0 and res.stdout:
                changed.update(line.strip() for line in res.stdout.splitlines() if line.strip())
        except Exception:
            pass
    return sorted(changed)


def audit_blast_radius(
    scenario_root: str,
    target_file: str,
    changed_files: Optional[List[str]] = None,
    allowed_files: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Verify that only the designated target file was modified and analyze callers.

    Parameters:
        scenario_root: Root directory of the scenario or git checkout.
        target_file: Relative or absolute path to the designated target file.
        changed_files: Optional explicit list of modified file paths. If None, queries git.
        allowed_files: Optional list of additional allowed files (e.g. documentation).

    Returns:
        Structured audit report dict containing:
            - blast_radius_clean (bool): True if only allowed files were modified.
            - non_target_modifications (list[str]): Unexpected modified files.
            - caller_sites (dict): Call sites of symbols in target_file across the corpus.
            - blast_radius_score (float): 1.0 if perfectly clean, decreasing with non-target modifications.
    """
    abs_root = os.path.abspath(scenario_root)
    abs_target = target_file if os.path.isabs(target_file) else os.path.abspath(os.path.join(abs_root, target_file))
    rel_target = os.path.relpath(abs_target, abs_root).replace(os.sep, "/")

    if changed_files is None:
        changed_files = get_git_changed_files(abs_root)

    norm_changed = [os.path.normpath(f).replace(os.sep, "/") for f in changed_files]
    norm_allowed = {os.path.normpath(rel_target).replace(os.sep, "/")}
    if allowed_files:
        for af in allowed_files:
            norm_allowed.add(os.path.normpath(af).replace(os.sep, "/"))

    non_target_mods = [f for f in norm_changed if f not in norm_allowed]

    # Analyze defined symbols and callers in target file
    symbols_dict = {}
    if os.path.exists(abs_target):
        for sym_name, line_no in defined_symbols(abs_target):
            symbols_dict[sym_name] = {"file": rel_target, "line": line_no}

    corpus = python_files(abs_root)
    callers = find_callers(abs_root, symbols_dict, corpus)

    caller_summary = []
    for sym_name, sites in callers.items():
        calls = [s for s in sites if s[2] == "call"]
        caller_summary.append({
            "symbol": sym_name,
            "total_references": len(sites),
            "call_sites_count": len(calls),
            "call_sites": [{"file": s[0], "line": s[1], "snippet": s[3]} for s in calls],
        })

    is_clean = len(non_target_mods) == 0
    # Blast radius score penalty: 0.5 deduction per unauthorized file touched
    penalty = len(non_target_mods) * 0.5
    score = max(0.0, 1.0 - penalty)

    return {
        "blast_radius_clean": is_clean,
        "target_file": rel_target,
        "changed_files": norm_changed,
        "non_target_modifications": non_target_mods,
        "defined_symbols": list(symbols_dict.keys()),
        "caller_summary": caller_summary,
        "blast_radius_score": score,
    }
