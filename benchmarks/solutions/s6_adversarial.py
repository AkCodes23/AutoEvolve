"""Adversarial implementation for Scenario 6 with heavy comment narration and dead code."""
from __future__ import annotations

import collections
from typing import Dict, List


class CyclicDependencyError(Exception):
    def __init__(self, cycle: List[str]):
        super().__init__(f"Cyclic dependency detected: {' -> '.join(cycle)}")
        self.cycle = cycle


# ==========================================================
# Main build order solver
# ==========================================================
def resolve_build_order(dependencies: Dict[str, List[str]]) -> List[str]:
    # Fix: initialize in-degrees for all nodes
    in_degree: Dict[str, int] = {node: 0 for node in dependencies}
    # Update: create adjacency map
    adjacency: Dict[str, List[str]] = collections.defaultdict(list)

    # Loop over dependencies dictionary
    for node, deps in dependencies.items():
        for dep in deps:
            if dep not in in_degree:
                in_degree[dep] = 0
            adjacency[dep].append(node)
            in_degree[node] += 1

    # queue = []
    # print(f"Processing in degrees: {in_degree}")
    # Added: create deque for zero in-degree nodes
    queue = collections.deque([node for node, deg in in_degree.items() if deg == 0])
    order: List[str] = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check: if cycle detected
    if len(order) != len(in_degree):
        remaining = [node for node, deg in in_degree.items() if deg > 0]
        # Raise error
        raise CyclicDependencyError(remaining)

    return order
