"""Tests for AutoEvolve v4.0: Neurosymbolic Failure Graph and Swarm Orchestrator."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.smt_verify import verify_code_safety
from scripts.failure_graph import FailureKnowledgeGraph
from scripts.swarm_orchestrator import SwarmOrchestrator


class TestV40NeurosymbolicSwarm:
    def test_smt_safety_clean_code(self):
        clean_code = "def compute_sum(a: int, b: int) -> int:\n    return a + b\n"
        res = verify_code_safety(clean_code)
        assert res["valid"] is True
        assert res["safety_score"] == 1.0
        assert res["passed"] is True

    def test_smt_safety_global_mutation_flagged(self):
        dangerous_code = "global state_counter\nstate_counter += 1\n"
        res = verify_code_safety(dangerous_code)
        assert res["valid"] is True
        assert res["safety_score"] < 1.0
        assert res["passed"] is False
        assert any("Global variable" in v for v in res["violations"])

    def test_failure_knowledge_graph_mermaid(self):
        g = FailureKnowledgeGraph()
        g.add_constraint("Global Lock in Thread Loop", "GIL Contention", "Lock-free atomic CAS")
        g.add_constraint("Unbounded Stream Ingest", "Out of Memory", "Chunked Spill-to-Disk")

        mermaid = g.to_mermaid()
        assert "graph LR" in mermaid
        assert "Global Lock" in mermaid
        assert "GIL Contention" in mermaid
        assert "Lock-free" in mermaid
        assert "Out of Memory" in mermaid

    def test_swarm_orchestrator_islands(self):
        islands = SwarmOrchestrator.get_islands()
        assert len(islands) == 3
        ids = {i["id"] for i in islands}
        assert "island_simd" in ids
        assert "island_lockfree" in ids
        assert "island_cache" in ids

    def test_swarm_semantic_crossover(self):
        res = SwarmOrchestrator.semantic_crossover("streaming_simd_reader", "lockfree_ring_buffer")
        assert res["status"] == "crossover_synthesized"
        assert len(res["parents"]) == 2
