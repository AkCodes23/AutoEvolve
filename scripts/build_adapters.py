"""Adapter synchronizer for AutoEvolve across 12 IDEs and Agent environments."""
from __future__ import annotations

import os
import re
import sys

ADAPTER_HEADERS = {
    'aider.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Conventions for Aider

When working in this repository with Aider, follow these core conventions:
""",
    'claude.md': """<!-- AutoEvolve-Core -->
# AutoEvolve mindset
""",
    'cline.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Rules for Cline & Roo Code

You are Cline / Roo Code operating under the **AutoEvolve** engineering mindset.
""",
    'cody.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Rules for Sourcegraph Cody
""",
    'continue.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Rules for Continue.dev
""",
    'copilot-instructions.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Instructions for GitHub Copilot
""",
    'cursor.mdc': """<!-- AutoEvolve-Core -->
---
description: AutoEvolve operating mindset, small, verified, kept-if-better changes; simplify relentlessly.
globs:
alwaysApply: true
---
""",
    'gemini.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Rules for Gemini Code Assist
""",
    'jetbrains.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Rules for JetBrains AI Assistant
""",
    'openhands.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Microagent for OpenHands
""",
    'windsurf.md': """<!-- AutoEvolve-Core -->
---
description: AutoEvolve operating mindset, small, verified, kept-if-better changes; simplify relentlessly.
globs:
---
""",
    'zed.md': """<!-- AutoEvolve-Core -->
# AutoEvolve Rules for Zed Assistant
""",
}


def extract_core_mindset(agents_md_path: str) -> str:
    with open(agents_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'(<autoevolve_mindset>.*?</autoevolve_mindset>)', content, re.DOTALL)
    if not match:
        raise ValueError(f'Could not find <autoevolve_mindset> block in {agents_md_path}')
    return match.group(1).strip()


def build_adapters(repo_root: str, check_only: bool = False) -> bool:
    agents_path = os.path.join(repo_root, 'AGENTS.md')
    target_dirs = [os.path.join(repo_root, 'adapters')]
    nested_adapters = os.path.join(repo_root, 'AutoEvolve', 'adapters')
    if os.path.isdir(os.path.join(repo_root, 'AutoEvolve')):
        target_dirs.append(nested_adapters)

    core_mindset = extract_core_mindset(agents_path)
    all_synced = True

    for adapters_dir in target_dirs:
        os.makedirs(adapters_dir, exist_ok=True)
        for filename, header in ADAPTER_HEADERS.items():
            adapter_path = os.path.join(adapters_dir, filename)
            expected_content = f'{header.strip()}\n\n{core_mindset}\n'

            if check_only:
                if not os.path.exists(adapter_path):
                    print(f'[FAIL] Missing adapter: {adapter_path}')
                    all_synced = False
                    continue
                with open(adapter_path, 'r', encoding='utf-8') as f:
                    actual = f.read()
                if actual.strip() != expected_content.strip():
                    print(f'[FAIL] Drift detected in adapter: {adapter_path}')
                    all_synced = False
                else:
                    print(f'[OK] Adapter in sync: {filename}')
            else:
                with open(adapter_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(expected_content)
                print(f'[BUILT] Updated adapter: {adapter_path}')

    return all_synced


if __name__ == '__main__':
    check = '--check' in sys.argv
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ok = build_adapters(root, check_only=check)
    if check and not ok:
        sys.exit(1)
