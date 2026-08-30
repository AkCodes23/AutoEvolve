"""Dependency resolution graph algorithms."""
from __future__ import annotations

from typing import Dict, List


class CyclicDependencyError(Exception):
    """Raised when a circular dependency cycle is detected."""

    def __init__(self, cycle: List[str]):
        super().__init__(f"Cyclic dependency detected: {' -> '.join(cycle)}")
        self.cycle = cycle


def resolve_build_order(dependencies: Dict[str, List[str]]) -> List[str]:
    """Compute a valid build order for modules with dependency relationships.
    
    Parameters:
        dependencies: A mapping of module_name -> list of modules it directly depends on.
        
    Returns:
        A list of module names in valid topological compilation order.
        
    Raises:
        CyclicDependencyError: If a dependency cycle is detected.
    """
    raise NotImplementedError("resolve_build_order is not implemented")
