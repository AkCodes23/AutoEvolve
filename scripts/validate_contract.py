"""Deep Innovation Gate (DIG) & Staged Evidence Validator for AutoEvolve v5.0."""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple


VALID_MODES = {'grilling', 'prototype', 'research', 'mutate'}


def validate_contract_text(text: str) -> Tuple[bool, List[str]]:
    errors = []
    required_tags = ['hypothesis', 'surface', 'intent', 'expected_evidence']
    lowered = text.lower()
    for tag in required_tags:
        if tag not in lowered:
            errors.append(f"Missing required DIG contract field: '{tag}'")

    # Mode validation if present
    for mode_prefix in ('mode:', 'mode =', 'mode'):
        if mode_prefix in lowered:
            # Check for any valid mode
            found_mode = None
            for m in VALID_MODES:
                if m in lowered:
                    found_mode = m
                    break
            if not found_mode:
                errors.append(f"Invalid exploration mode. Allowed: {sorted(list(VALID_MODES))}")
            elif found_mode == 'grilling' and ('autonomous' in lowered or 'afk' in lowered):
                errors.append("Grilling mode requires Human-in-the-Loop (HITL); cannot be autonomous/AFK")
            break

    return len(errors) == 0, errors


def validate_stage_ladder(stage: str) -> bool:
    valid_stages = {'smoke', 'scout', 'complete', 'audit'}
    return stage.lower().strip() in valid_stages


def main():
    parser = argparse.ArgumentParser(description="Validate AutoEvolve DIG Contracts and Stages")
    parser.add_argument('--contract-file', help="Path to contract snippet or plan file")
    parser.add_argument('--stage', help="Evidence stage name (smoke, scout, complete, audit)")
    parser.add_argument('--mode', help="Exploration mode (grilling, prototype, research, mutate)")
    args = parser.parse_args()

    if args.stage:
        if not validate_stage_ladder(args.stage):
            print(f"[FAIL] Invalid evidence stage: {args.stage}. Allowed: smoke, scout, complete, audit")
            sys.exit(1)
        print(f"[PASS] Valid evidence stage: {args.stage}")

    if args.mode:
        if args.mode.lower().strip() not in VALID_MODES:
            print(f"[FAIL] Invalid mode: {args.mode}. Allowed: {sorted(list(VALID_MODES))}")
            sys.exit(1)
        print(f"[PASS] Valid exploration mode: {args.mode}")

    if args.contract_file:
        if not os.path.exists(args.contract_file):
            print(f"[FAIL] File not found: {args.contract_file}")
            sys.exit(1)
        with open(args.contract_file, 'r', encoding='utf-8') as f:
            content = f.read()
        valid, errors = validate_contract_text(content)
        if not valid:
            for err in errors:
                print(f"[FAIL] {err}")
            sys.exit(1)
        print("[PASS] DIG Pre-Edit Contract conforms to AutoEvolve-Core v5.0")


if __name__ == '__main__':
    main()
