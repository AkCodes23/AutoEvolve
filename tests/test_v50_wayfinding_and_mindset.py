"""Tests for AutoEvolve v5.0: Wayfinding Decision Maps, Fog of War & Swarm Coordination."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.wayfinder_map import WayfinderMap, WayfinderTicket
from scripts.validate_contract import validate_contract_text, validate_stage_ladder
from scripts.swarm_orchestrator import SwarmOrchestrator


class TestV50WayfindingAndMindset:
    def test_wayfinder_ticket_basics(self):
        t = WayfinderTicket(
            ticket_id="F-01",
            title="Design zero-copy parser",
            mode="mutate",
            blocked_by=["F-00"],
            signal="pytest tests/test_parser.py",
        )
        assert t.ticket_id == "F-01"
        assert t.mode == "mutate"
        assert t.status == "OPEN"
        assert t.is_unblocked(set()) is False
        assert t.is_unblocked({"F-00"}) is True

    def test_parse_wayfinder_map(self):
        sample_md = """# AutoEvolve Direction & Wayfinding Map

## Destination
Build high-throughput zero-copy stream processing engine.

## Active Frontier
- [ ] [F-01] Create ring buffer (mode: mutate, blocked_by: [], claim: none, signal: pytest)
- [ ] [F-02] Parallel partition worker (mode: mutate, blocked_by: [F-01], claim: none, signal: pytest)

## Fog of War
- Dynamic backpressure auto-tuning algorithm

## Out of Scope
- No distributed RPC or multi-node clustering

## Decisions So Far
- [F-00 Storage Choice](file:///LINEAGE.md#F-00): Selected memory-mapped ring buffer
"""
        wmap = WayfinderMap.parse_markdown(sample_md)
        assert "zero-copy" in wmap.destination
        assert len(wmap.active_frontier) == 2
        assert len(wmap.fog_of_war) == 1
        assert len(wmap.out_of_scope) == 1
        assert len(wmap.decisions_so_far) == 1

        unblocked = wmap.get_unblocked_frontier()
        assert len(unblocked) == 1
        assert unblocked[0].ticket_id == "F-01"

    def test_frontier_claiming_and_resolution(self):
        sample_md = """# Direction Map
## Destination
Test initiative.
## Active Frontier
- [ ] [F-01] First step (mode: mutate, blocked_by: [], claim: none)
- [ ] [F-02] Second step (mode: mutate, blocked_by: [F-01], claim: none)
"""
        wmap = WayfinderMap.parse_markdown(sample_md)

        # Claim by agent 1
        assert wmap.claim_ticket("F-01", "agent_1") is True
        # Cannot claim already claimed ticket by agent 2
        assert wmap.claim_ticket("F-01", "agent_2") is False
        # Re-claiming by same agent is idempotent
        assert wmap.claim_ticket("F-01", "agent_1") is True

        # Unblocked query now excludes claimed ticket
        assert len(wmap.get_unblocked_frontier()) == 0

        # Resolve F-01
        assert wmap.resolve_ticket("F-01", "Implemented memory buffer", link="file:///diff_f01.patch") is True
        assert len(wmap.decisions_so_far) == 1

        # Now F-02 is unblocked
        unblocked = wmap.get_unblocked_frontier()
        assert len(unblocked) == 1
        assert unblocked[0].ticket_id == "F-02"

    def test_fog_of_war_graduation(self):
        sample_md = """# Direction Map
## Destination
Test destination.
## Active Frontier
- [ ] [F-01] Initial task (mode: research, blocked_by: [], claim: none)
## Fog of War
- Scalable concurrency model
"""
        wmap = WayfinderMap.parse_markdown(sample_md)
        assert len(wmap.fog_of_war) == 1

        new_t = WayfinderTicket(
            ticket_id="F-02",
            title="Implement Lock-Free Ring Buffer",
            mode="mutate",
            blocked_by=["F-01"],
            signal="pytest tests/test_ringbuf.py",
        )
        assert wmap.graduate_fog(0, new_t) is True
        assert len(wmap.fog_of_war) == 0
        assert len(wmap.active_frontier) == 2

    def test_wayfinder_invariant_validation(self):
        wmap = WayfinderMap(destination="")
        valid, errors = wmap.validate_invariants()
        assert valid is False
        assert any("Missing Destination" in e for e in errors)

        wmap.destination = "Valid Destination"
        invalid_ticket = WayfinderTicket("F-99", "Invalid mode ticket", mode="hacky_edit")
        wmap.active_frontier.append(invalid_ticket)
        valid, errors = wmap.validate_invariants()
        assert valid is False
        assert any("Invalid mode" in e for e in errors)

        # Test HITL enforcement on grilling
        grilling_ticket = WayfinderTicket("F-10", "Clarify requirements", mode="grilling", claimed_by="autonomous_afk_bot")
        wmap.active_frontier = [grilling_ticket]
        valid, errors = wmap.validate_invariants()
        assert valid is False
        assert any("Grilling ticket" in e and "HITL" in e for e in errors)

    def test_swarm_frontier_allocation(self):
        tickets = [
            {"id": "F-01", "title": "SIMD parser"},
            {"id": "F-02", "title": "CAS queue"},
            {"id": "F-03", "title": "Cache structure"},
            {"id": "F-04", "title": "Vector encoder"},
        ]
        alloc = SwarmOrchestrator.allocate_frontier_to_islands(tickets)
        assert len(alloc["island_simd"]) == 2
        assert len(alloc["island_lockfree"]) == 1
        assert len(alloc["island_cache"]) == 1

    def test_validate_contract_modes_and_stages(self):
        valid_contract = """
        HYPOTHESIS: Hoist compiled regex outside the loop
        SURFACE: search_engine.py
        INTENT: exploit
        MODE: mutate
        EXPECTED_EVIDENCE: p99 latency decreases from 120ms to 45ms
        """
        ok, errs = validate_contract_text(valid_contract)
        assert ok is True
        assert len(errs) == 0

        # Grilling with AFK should be rejected
        afk_grilling = """
        HYPOTHESIS: Clarify business requirements
        SURFACE: spec.md
        INTENT: explore
        MODE: grilling
        AUTONOMOUS: true
        EXPECTED_EVIDENCE: Complete spec
        """
        ok, errs = validate_contract_text(afk_grilling)
        assert ok is False
        assert any("Human-in-the-Loop" in e for e in errs)

        assert validate_stage_ladder("smoke") is True
        assert validate_stage_ladder("scout") is True
        assert validate_stage_ladder("complete") is True
        assert validate_stage_ladder("audit") is True
        assert validate_stage_ladder("invalid_stage") is False
