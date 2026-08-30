"""AST Comment Noise & Narration Auditor."""
from __future__ import annotations

import ast
import io
import os
import re
import tokenize
from typing import Any, Dict, List

# Change-narration regex matching history-describing comments
NARRATION_PATTERN = re.compile(
    r"^(fix|fixed|fixes|change[d]?|update[d]?|add(?:ed)?|remove[d]?|delete[d]?|modif\w+|"
    r"refactor\w*|rename[d]?|replace[d]?|improve[d]?|new|before|after|old|was)\b\s*[:\-]",
    re.IGNORECASE,
)

DIVIDER_CHARS = "=-*~_+#.<>|/ "

CODE_NODES = (
    ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Return, ast.Import, ast.ImportFrom,
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.For, ast.AsyncFor,
    ast.While, ast.If, ast.With, ast.AsyncWith, ast.Try, ast.Raise, ast.Assert,
    ast.Delete, ast.Pass, ast.Break, ast.Continue, ast.Expr
)

EXEMPT_PREFIXES = (
    "todo", "fixme", "hack", "xxx", "evolve:", "type:", "noqa", "pragma",
    "pylint:", "mypy:", "ruff:", "flake8:", "isort:", "fmt:", "nosec",
    "pyright:", "pytype:", "bandit:", "coding:", "-*-", "!"
)


def _is_divider(text: str) -> bool:
    """Check if comment is a decorative ASCII divider."""
    clean = text.strip()
    return len(clean) >= 4 and all(c in DIVIDER_CHARS for c in clean)


def _is_commented_code(clean_text: str) -> bool:
    """Check if comment text parses as an executable Python statement."""
    # Strip any leading comment markers
    t = clean_text.strip()
    if not t or t.startswith("#") or any(t.lower().startswith(p) for p in EXEMPT_PREFIXES):
        return False
    try:
        parsed = ast.parse(t)
        if parsed.body and isinstance(parsed.body[0], CODE_NODES):
            # Exclude single-word docstrings or strings
            if isinstance(parsed.body[0], ast.Expr) and isinstance(parsed.body[0].value, ast.Constant):
                return False
            return True
    except Exception:
        pass
    return False


def audit_comment_noise(file_path: str) -> Dict[str, Any]:
    """Analyze AST comment noise, narration, and restatements in a Python file.

    Parameters:
        file_path: Absolute or relative path to the Python file.

    Returns:
        Structured audit dictionary with noise counts, locations, and score.
    """
    if not os.path.exists(file_path):
        return {
            "file_exists": False,
            "total_comments": 0,
            "narration_count": 0,
            "commented_code_count": 0,
            "divider_count": 0,
            "total_noise": 0,
            "clean": False,
            "comment_score": 0.0,
            "findings": [],
        }

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception as exc:
        return {
            "file_exists": True,
            "error": str(exc),
            "clean": False,
            "comment_score": 0.0,
            "findings": [],
        }

    comments: List[tuple[str, int]] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_str, start, _, _ in tokens:
            if tok_type == tokenize.COMMENT:
                comments.append((tok_str, start[0]))
    except Exception:
        # Fallback regex if tokenizer fails
        for line_no, line in enumerate(source.splitlines(), 1):
            if "#" in line:
                idx = line.find("#")
                comments.append((line[idx:], line_no))

    narration_hits: List[Dict[str, Any]] = []
    commented_code_hits: List[Dict[str, Any]] = []
    divider_hits: List[Dict[str, Any]] = []

    for comment_text, lineno in comments:
        clean = comment_text.lstrip("#").strip()
        if not clean:
            continue

        # Check for change narration
        if NARRATION_PATTERN.search(clean):
            narration_hits.append({
                "line": lineno,
                "text": comment_text,
                "type": "NARRATION",
                "message": "Comment narrates diff/change history rather than explaining code why",
            })
            continue

        # Check for decorative dividers
        if _is_divider(clean):
            divider_hits.append({
                "line": lineno,
                "text": comment_text,
                "type": "DIVIDER",
                "message": "Punctuation divider comment",
            })
            continue

        # Check for commented-out code
        if _is_commented_code(clean):
            commented_code_hits.append({
                "line": lineno,
                "text": comment_text,
                "type": "COMMENTED_CODE",
                "message": "Comment contains dead / commented-out code statement",
            })

    total_noise = len(narration_hits) + len(commented_code_hits) + len(divider_hits)
    total_lines = max(1, len(source.splitlines()))
    noise_per_kloc = (total_noise / total_lines) * 1000.0

    # Score: 1.0 for 0 noise, penalized by 0.2 per noise hit
    score = max(0.0, 1.0 - (total_noise * 0.2))

    findings = narration_hits + commented_code_hits + divider_hits

    return {
        "file_exists": True,
        "total_lines": total_lines,
        "total_comments": len(comments),
        "narration_count": len(narration_hits),
        "commented_code_count": len(commented_code_hits),
        "divider_count": len(divider_hits),
        "total_noise": total_noise,
        "noise_per_kloc": round(noise_per_kloc, 2),
        "clean": total_noise == 0,
        "comment_score": round(score, 4),
        "findings": findings,
    }
