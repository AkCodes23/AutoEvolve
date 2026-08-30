# Scenario 6: Direct Code & Anti-Comment Narration

## Task Description
In `src/graph/dependency_resolver.py`, implement Kahn's topological sort algorithm to resolve the build order of components with dependency constraints:
- `resolve_build_order(dependencies: dict[str, list[str]]) -> list[str]`
- When a dependency cycle is encountered, raise `CyclicDependencyError(cycle: list[str])`.

Write clean, concise, idiomatic Python. Do NOT narrate diffs or changes with comments (`# Fix: ...`, `# Added: ...`, `# Update: ...`), do NOT leave commented-out code, and do NOT write trivial restatements of code lines.

## Constraints
- Modify ONLY `src/graph/dependency_resolver.py`.
- Must pass `tests/test_dependency_resolver.py`.
- AST comment auditor enforces zero narration comments, zero commented-out code, and zero comment noise.
