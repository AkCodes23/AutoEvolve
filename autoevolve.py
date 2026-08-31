#!/usr/bin/env python3
"""Unified AutoEvolve CLI Dispatcher & Toolkit.

Provides a unified interface for all AutoEvolve capabilities:
- check: Run full invariant and adapter audit
- map: View or manipulate Wayfinder decision maps
- build: Rebuild and synchronize all 12 IDE adapters
- bench: Execute strict non-saturated physical SWE benchmarks
- contract: Validate DIG pre-edit contracts
- tree: Run LATS Monte Carlo Tree Search across orthogonal coordinates
- swarm: Orchestrate multi-island parallel genetic evolution
"""
from __future__ import annotations

import argparse
import os
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def main():
    parser = argparse.ArgumentParser(
        prog="autoevolve",
        description="AutoEvolve v5.0 Autonomous Software Evolution & Wayfinding Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # check
    p_check = subparsers.add_parser("check", help="Run full invariant and adapter checks")

    # map
    p_map = subparsers.add_parser("map", help="Manage Wayfinder decision map")
    p_map.add_argument("--direction", default="DIRECTION.md", help="Path to DIRECTION.md")
    p_map.add_argument("--unblocked", action="store_true", help="List unblocked frontier tickets")
    p_map.add_argument("--claim", help="Claim a ticket by ID")
    p_map.add_argument("--resolve", help="Resolve a ticket by ID")
    p_map.add_argument("--gist", default="", help="Decision gist for resolved ticket")

    # build
    p_build = subparsers.add_parser("build", help="Rebuild all 12 IDE adapters from AGENTS.md")
    p_build.add_argument("--check", action="store_true", help="Check only, do not write")

    # bench
    p_bench = subparsers.add_parser("bench", help="Run strict physical SWE benchmarks")
    p_bench.add_argument("--suite", choices=["real", "blind", "multi"], default="real", help="Benchmark suite")
    p_bench.add_argument("--iterations", type=int, default=5, help="Number of benchmark iterations")

    # contract
    p_contract = subparsers.add_parser("contract", help="Validate or register DIG contract")
    p_contract.add_argument("contract_file", nargs="?", default=".autoevolve/CONTRACT.md", help="Contract file path")

    args = parser.parse_args()

    if args.command == "check":
        from scripts.check import run_all_checks
        success = run_all_checks(REPO_ROOT)
        sys.exit(0 if success else 1)

    elif args.command == "map":
        from scripts.wayfinder_map import WayfinderMap
        dpath = os.path.join(REPO_ROOT, args.direction)
        if not os.path.exists(dpath):
            print(f"Error: {dpath} not found")
            sys.exit(1)
        with open(dpath, "r", encoding="utf-8") as f:
            wmap = WayfinderMap.parse_markdown(f.read())

        if args.unblocked:
            unblocked = wmap.get_unblocked_frontier()
            print(f"Unblocked Active Frontier Tickets ({len(unblocked)}):")
            for t in unblocked:
                print(f"  [{t.mode.upper()}] {t.ticket_id}: {t.title}")
        elif args.claim:
            success = wmap.claim_ticket(args.claim, "AutoEvolveAgent")
            if success:
                with open(dpath, "w", encoding="utf-8") as f:
                    f.write(wmap.to_markdown())
                print(f"Claimed ticket {args.claim}")
            else:
                print(f"Failed to claim ticket {args.claim}")
                sys.exit(1)
        elif args.resolve:
            success = wmap.resolve_ticket(args.resolve, decision_gist=args.gist or "Resolved via AutoEvolve")
            if success:
                with open(dpath, "w", encoding="utf-8") as f:
                    f.write(wmap.to_markdown())
                print(f"Resolved ticket {args.resolve}")
            else:
                print(f"Failed to resolve ticket {args.resolve}")
                sys.exit(1)
        else:
            print(wmap.to_markdown())

    elif args.command == "build":
        from scripts.build_adapters import build_adapters
        success = build_adapters(REPO_ROOT, check_only=args.check)
        sys.exit(0 if success else 1)

    elif args.command == "bench":
        if args.suite == "real":
            from benchmarks.real_systems_benchmark import run_live_systems_benchmark
            run_live_systems_benchmark(iterations=args.iterations)
        elif args.suite == "blind":
            from benchmarks.blind_unbiased_benchmark import run_blind_unbiased_evaluation
            run_blind_unbiased_evaluation()
        elif args.suite == "multi":
            from benchmarks.multi_benchmark_matrix import run_multi_benchmark_matrix
            run_multi_benchmark_matrix()

    elif args.command == "contract":
        from scripts.validate_contract import validate_contract
        success, errors = validate_contract(args.contract_file)
        if success:
            print("Contract valid!")
        else:
            print("Contract invalid:")
            for e in errors:
                print(f"  --> {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
