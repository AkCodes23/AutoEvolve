"""Deep Innovation Gate (DIG) & Staged Evidence Validator for AutoEvolve."""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple


def validate_contract_text(text: str) -> Tuple[bool, List[str]]:
    errors = []
    required_tags = ['hypothesis', 'surface', 'intent', 'expected_evidence']
    lowered = text.lower()
    for tag in required_tags:
        if tag not in lowered:
            errors.append(f"Missing required DIG contract field: '{tag}'")
    return len(errors) == 0, errors


def validate_stage_ladder(stage: str) -> bool:
    valid_stages = {'smoke', 'scout', 'complete', 'audit'}
    return stage.lower().strip() in valid_stages


def main():
    parser = argparse.ArgumentParser(description="Validate AutoEvolve DIG Contracts and Stages")
    parser.add_argument('--contract-file', help="Path to contract snippet or plan file")
    parser.add_argument('--stage', help="Evidence stage name (smoke, scout, complete, audit)")
    args = parser.parse_args()

    if args.stage:
        if not validate_stage_ladder(args.stage):
            print(f"[FAIL] Invalid evidence stage: {args.stage}. Allowed: smoke, scout, complete, audit")
            sys.exit(1)
        print(f"[PASS] Valid evidence stage: {args.stage}")

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
        print("[PASS] DIG Pre-Edit Contract conforms to AutoEvolve-Core v3.0")


if __name__ == '__main__':
    main()
