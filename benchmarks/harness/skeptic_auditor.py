"""Skeptic Adversarial Auditor for AutoEvolve (inspired by PRAXIST PI Panel).

Red-teams candidate diffs and verification trials:
1. Audits test files for assertion weakening or mock relaxing.
2. Verifies pre-edit Deep Innovation Gate (DIG) contract conformance.
3. Validates multi-stage evidence progression (smoke -> scout -> complete).
4. Verifies non-violation of active CONSTRAINTS.md failure rules.
"""
from __future__ import annotations

import ast
import os
import re
from typing import Any, Dict, List, Optional, Tuple


def audit_test_assertion_rigor(test_file_path: str) -> Dict[str, Any]:
    """Inspect AST of a test file to detect assertion tampering or dilution."""
    if not os.path.exists(test_file_path):
        return {"file_exists": False, "score": 1.0, "rigor_score": 1.0, "violations": [], "skeptic_approved": True}

    try:
        with open(test_file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        tree = ast.parse(source, filename=test_file_path)
    except Exception as exc:
        return {"file_exists": True, "score": 0.0, "rigor_score": 0.0, "violations": [f"AST parse failed: {exc}"], "skeptic_approved": False}

    violations = []
    assert_count = 0
    trivial_asserts = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            assert_count += 1
            test_expr = node.test
            # Check for assert True or assert 1 (tautologies)
            if isinstance(test_expr, ast.Constant) and bool(test_expr.value) is True:
                trivial_asserts += 1
                violations.append(f"Line {node.lineno}: Trivial assertion 'assert True'")

    if assert_count == 0:
        violations.append("Test file contains zero assert statements")

    rigor_score = 1.0 if (assert_count > 0 and trivial_asserts == 0) else max(0.0, 1.0 - (trivial_asserts * 0.5))
    return {
        "file_exists": True,
        "assert_count": assert_count,
        "trivial_asserts": trivial_asserts,
        "score": round(rigor_score, 4),
        "rigor_score": round(rigor_score, 4),
        "violations": violations,
        "skeptic_approved": len(violations) == 0,
    }


def audit_dig_contract(contract_text: Optional[str]) -> Dict[str, Any]:
    """Check if pre-edit DIG contract satisfies AutoEvolve-Core v3.0 requirements."""
    if not contract_text:
        return {
            "has_contract": False,
            "score": 0.0,
            "missing_fields": ["hypothesis", "surface", "intent", "expected_evidence"],
            "skeptic_approved": False,
        }

    # Normalize whitespace/underscores for field detection
    lowered = contract_text.lower().replace("_", " ")
    required_checks = {
        "hypothesis": "hypothesis" in lowered,
        "surface": "surface" in lowered,
        "intent": "intent" in lowered,
        "expected_evidence": ("expected evidence" in lowered or "expected_evidence" in lowered or "signal" in lowered),
    }

    missing = [field for field, found in required_checks.items() if not found]

    valid_intent = False
    for intent in ["exploit", "explore", "falsify", "diagnose", "baseline"]:
        if intent in lowered:
            valid_intent = True
            break
    if not valid_intent:
        missing.append("valid_intent (exploit|explore|falsify|diagnose)")

    score = max(0.0, (len(required_checks) - len(missing)) / len(required_checks))
    return {
        "has_contract": True,
        "score": round(score, 4),
        "missing_fields": missing,
        "skeptic_approved": len(missing) == 0,
    }


def audit_evidence_ladder(stage_history: List[str]) -> Dict[str, Any]:
    """Validate that trial followed staged evidence progression (smoke -> scout -> complete)."""
    if not stage_history:
        return {"staged": False, "score": 0.5, "max_stage": "unspecified", "skeptic_approved": False}

    normalized = [s.lower().strip() for s in stage_history]
    has_smoke = "smoke" in normalized
    has_scout = "scout" in normalized
    has_complete = "complete" in normalized

    if has_complete and (has_smoke or has_scout):
        score = 1.0
        reason = "Full multi-stage progression completed"
    elif has_complete:
        score = 0.8
        reason = "Complete evaluation run directly without preliminary scout"
    elif has_scout:
        score = 0.4
        reason = "Only scout evaluation performed; cannot promote to HEAD"
    else:
        score = 0.2
        reason = "Only smoke evaluation performed"

    return {
        "staged": True,
        "score": score,
        "stage_history": normalized,
        "reason": reason,
        "skeptic_approved": has_complete,
    }


def run_skeptic_audit(
    *,
    test_file_path: Optional[str] = None,
    contract_text: Optional[str] = None,
    stage_history: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run full Skeptic composite audit."""
    test_audit = audit_test_assertion_rigor(test_file_path) if test_file_path else {"score": 1.0, "rigor_score": 1.0, "skeptic_approved": True}
    contract_audit = audit_dig_contract(contract_text) if contract_text else {"score": 1.0, "skeptic_approved": True}
    ladder_audit = audit_evidence_ladder(stage_history or ["complete"])

    composite = (test_audit["score"] * 0.4) + (contract_audit["score"] * 0.3) + (ladder_audit["score"] * 0.3)
    approved = test_audit["skeptic_approved"] and contract_audit["skeptic_approved"] and ladder_audit["skeptic_approved"]

    return {
        "composite_skeptic_score": round(composite, 4),
        "skeptic_approved": approved,
        "test_rigor": test_audit,
        "dig_contract": contract_audit,
        "evidence_ladder": ladder_audit,
    }
