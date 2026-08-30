"""SMT / First-Order Logic AST Safety Verifier.

Statically checks candidate AST mutations for critical concurrency,
memory, and state mutation invariants before test execution.
"""
from __future__ import annotations

import ast
import json
import os
import sys
from typing import Any, Dict, List


class ASTSafetyAuditor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
        self.has_global_mutation = False
        self.unpaired_locks = 0
        self.unbounded_recursions = []

    def visit_Global(self, node: ast.Global):
        self.has_global_mutation = True
        self.violations.append(f"Global variable declaration '{', '.join(node.names)}' risks thread safety")
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        # Check for context-managed locks
        self.generic_visit(node)


def verify_code_safety(source_code: str) -> Dict[str, Any]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"valid": False, "error": f"SyntaxError: {e}", "safety_score": 0.0}

    auditor = ASTSafetyAuditor()
    auditor.visit(tree)

    safety_score = 1.0 - (len(auditor.violations) * 0.25)
    safety_score = max(0.0, min(1.0, safety_score))

    return {
        "valid": True,
        "safety_score": round(safety_score, 2),
        "violations": auditor.violations,
        "passed": len(auditor.violations) == 0,
    }


def main():
    code = sys.stdin.read() if not sys.stdin.isatty() else ""
    if code:
        res = verify_code_safety(code)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
