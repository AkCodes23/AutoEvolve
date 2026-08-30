import pytest
from benchmarks.scenarios.s6_anti_comment.src.graph.dependency_resolver import (
    CyclicDependencyError,
    resolve_build_order,
)


def _validate_order(dependencies: dict[str, list[str]], order: list[str]) -> None:
    assert set(order) == set(dependencies.keys())
    pos = {node: idx for idx, node in enumerate(order)}
    for node, deps in dependencies.items():
        for dep in deps:
            assert pos[dep] < pos[node], f"Dependency {dep} must be built before {node}"


def test_linear_dependency_chain():
    # a depends on b, b depends on c, c has no deps
    deps = {
        "a": ["b"],
        "b": ["c"],
        "c": [],
    }
    order = resolve_build_order(deps)
    _validate_order(deps, order)
    assert order == ["c", "b", "a"]


def test_independent_modules():
    deps = {
        "mod1": [],
        "mod2": [],
        "mod3": [],
    }
    order = resolve_build_order(deps)
    assert len(order) == 3
    assert set(order) == {"mod1", "mod2", "mod3"}


def test_diamond_dependency_graph():
    # d depends on b and c; b and c depend on a; a has no deps
    deps = {
        "d": ["b", "c"],
        "b": ["a"],
        "c": ["a"],
        "a": [],
    }
    order = resolve_build_order(deps)
    _validate_order(deps, order)
    assert order[0] == "a"
    assert order[-1] == "d"


def test_disconnected_subgraphs():
    deps = {
        "x": ["y"],
        "y": [],
        "1": ["2"],
        "2": [],
    }
    order = resolve_build_order(deps)
    _validate_order(deps, order)


def test_self_dependency_cycle():
    deps = {
        "self_loop": ["self_loop"]
    }
    with pytest.raises(CyclicDependencyError) as exc_info:
        resolve_build_order(deps)
    assert "self_loop" in str(exc_info.value)


def test_three_node_cycle():
    deps = {
        "a": ["b"],
        "b": ["c"],
        "c": ["a"],
    }
    with pytest.raises(CyclicDependencyError) as exc_info:
        resolve_build_order(deps)
    assert any(n in str(exc_info.value) for n in ["a", "b", "c"])


def test_complex_dag():
    deps = {
        "app": ["core", "ui", "net"],
        "ui": ["core", "theme"],
        "theme": ["core"],
        "net": ["core", "crypto"],
        "crypto": ["core"],
        "core": [],
    }
    order = resolve_build_order(deps)
    _validate_order(deps, order)
    assert order[0] == "core"
    assert order[-1] == "app"
