"""Mermaid Solution Lineage DAG generator for AutoEvolve."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Dict


def parse_journal_entries(journal_path: str) -> List[Dict[str, str]]:
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


def generate_lineage_mermaid(entries: List[Dict[str, str]]) -> str:
    lines = ["```mermaid", "graph TD"]
    lines.append('    Base["Baseline HEAD"]')

    last_keep = 'Base'
    for i, e in enumerate(entries):
        decision = e.get('decision', '').upper()
        desc = e.get('description', '').replace('"', "'")
        node_id = f"Step_{i+1}"
        commit = e.get('commit', f's{i+1}')
        signal = e.get('signal', '')

        if 'BASELINE' in decision:
            continue
        elif 'KEEP' in decision:
            lines.append(f'    {node_id}["✅ {commit}: {desc}<br/><i>{signal}</i>"]')
            lines.append(f'    {last_keep} --> {node_id}')
            last_keep = node_id
        else:
            lines.append(f'    {node_id}["❌ {desc}<br/><i>Constraint Extracted</i>"]')
            lines.append(f'    {last_keep} -.->|Falsified| {node_id}')

    lines.append("```")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AutoEvolve Lineage DAG Generator")
    parser.add_argument('--repo-root', default='.', help="Target repo root")
    parser.add_argument('--out', default='LINEAGE.md', help="Output markdown file")
    args = parser.parse_args()

    root = os.path.abspath(args.repo_root)
    journal_path = os.path.join(root, 'JOURNAL.md')
    entries = parse_journal_entries(journal_path)
    mermaid_chart = generate_lineage_mermaid(entries)

    output_content = f"""# Solution Lineage & Provenance Graph

AutoEvolve records the complete evolutionary trajectory of this solution, documenting
not only the final kept diffs, but also the falsified hypotheses and active constraints
that shaped the architecture.

{mermaid_chart}
"""
    out_path = os.path.join(root, args.out)
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(output_content)
    print(f"[LINEAGE] Generated solution provenance graph at {out_path}")


if __name__ == '__main__':
    main()
