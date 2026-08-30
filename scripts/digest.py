"""Gems memory compression and failure constraint extractor for AutoEvolve."""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple


def parse_journal(journal_path: str) -> List[Dict[str, str]]:
    if not os.path.exists(journal_path):
        return []

    entries = []
    with open(journal_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line.startswith('|') or 'Commit' in line or '---' in line:
            continue
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if len(parts) >= 4:
            # Format: Commit | Signal | Stage | Intent | Decision | What Changed & Why
            # or legacy: Commit | Signal | Decision | What Changed & Why
            if len(parts) >= 6:
                entries.append({
                    'commit': parts[0],
                    'signal': parts[1],
                    'stage': parts[2],
                    'intent': parts[3],
                    'decision': parts[4],
                    'description': parts[5],
                })
            else:
                entries.append({
                    'commit': parts[0],
                    'signal': parts[1],
                    'stage': 'complete',
                    'intent': 'exploit',
                    'decision': parts[2],
                    'description': parts[3],
                })
    return entries


def extract_constraints(entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    constraints = []
    c_idx = 1
    for e in entries:
        decision = e.get('decision', '').upper()
        if 'REVERT' in decision or 'FAIL' in decision or 'DROP' in decision:
            desc = e.get('description', '')
            surface = 'unspecified'
            mechanism = desc
            root_cause = desc
            if ':' in desc:
                parts = desc.split(':', 1)
                surface = parts[0].strip()
                root_cause = parts[1].strip()
            constraints.append({
                'id': f'C-{c_idx:03d}',
                'type': 'negative_constraint',
                'surface': surface,
                'mechanism': mechanism,
                'root_cause': root_cause,
                'action': 'avoid',
            })
            c_idx += 1
    return constraints


def update_constraints_file(constraints_path: str, new_constraints: List[Dict[str, str]]) -> None:
    header = """# Active Constraints (Cumulative Evidence Store)

<!--
AutoEvolve inherits failure knowledge as first-class constraints.
When an experiment fails or is reverted, append a typed finding below.
Subsequent loops and agent sessions MUST read and satisfy these active constraints.
-->

| ID | Type | Surface | Attempted Mechanism | Failure Outcome & Root Cause | Action |
|---|---|---|---|---|---|
"""
    rows = []
    for c in new_constraints:
        rows.append(f"| {c['id']} | {c['type']} | `{c['surface']}` | {c['mechanism']} | {c['root_cause']} | {c['action']} |")

    content = header + "\n".join(rows) + "\n"
    with open(constraints_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


def compress_gems(entries: List[Dict[str, str]], gems_path: str) -> None:
    os.makedirs(os.path.dirname(gems_path), exist_ok=True)
    keeps = [e for e in entries if 'KEEP' in e.get('decision', '').upper()]
    reverts = [e for e in entries if 'REVERT' in e.get('decision', '').upper() or 'FAIL' in e.get('decision', '').upper()]

    gems_content = f"""# AutoEvolve Durable Gems (Compressed Architectural Memory)

<!--
Distilled memory of validated mechanisms and proven negative boundaries.
Active across long-horizon campaigns without prompt bloat.
-->

## Validated Mechanisms (Keep Patterns)
"""
    if keeps:
        for k in keeps[-6:]:
            gems_content += f"- **{k.get('commit', 'HEAD')}** ({k.get('signal', '')}): {k.get('description', '')}\n"
    else:
        gems_content += "- *None established yet.*\n"

    gems_content += "\n## Falsified Hypotheses & Active Constraints\n"
    if reverts:
        for r in reverts[-6:]:
            gems_content += f"- **DO NOT ATTEMPT**: {r.get('description', '')}\n"
    else:
        gems_content += "- *No negative constraints recorded.*\n"

    with open(gems_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(gems_content)


def main():
    parser = argparse.ArgumentParser(description="AutoEvolve Gems & Constraint Digest")
    parser.add_argument('--repo-root', default='.', help="Path to target repository")
    args = parser.parse_args()

    root = os.path.abspath(args.repo_root)
    journal_path = os.path.join(root, 'JOURNAL.md')
    constraints_path = os.path.join(root, 'CONSTRAINTS.md')
    gems_path = os.path.join(root, '.autoevolve', 'gems.md')

    entries = parse_journal(journal_path)
    constraints = extract_constraints(entries)
    update_constraints_file(constraints_path, constraints)
    compress_gems(entries, gems_path)
    print(f"[DIGEST] Processed {len(entries)} journal entries: extracted {len(constraints)} constraints, updated {gems_path}")


if __name__ == '__main__':
    main()
