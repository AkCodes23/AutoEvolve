# AutoEvolve Direction & Wayfinding Protocols

## Objective
Define architectural evolution goals, wayfinding decision frontiers, and hard verification constraints.

## Destination
Optimize system performance and reliability through neurosymbolic wayfinding and evolutionary mutations.

## Active Frontier
- [ ] [F-01] Design and verify AST invariant fuzzer (mode: mutate, blocked_by: [], claim: none, signal: pytest tests/test_v35_tree_search_and_prm.py)
- [ ] [F-02] SMT concurrency safety verification (mode: mutate, blocked_by: [F-01], claim: none, signal: pytest tests/test_v40_neurosymbolic_swarm.py)

## Fog of War
- Distributed cross-node worktree synchronization protocol (blocked on F-02)
- Multi-provider real-time LLM cost auctioneer

## Out of Scope
- No runtime daemons or external service dependencies
- No breaking changes to existing 12 IDE adapter contracts

## Decisions So Far
- [F-00 Mindset Synchronization](file:///LINEAGE.md#F-00): Upgraded to AutoEvolve v5.0 with full Wayfinding & Fog of War decomposition

## Signal
- Primary Signal: Invariant pass rate + p99 latency reduction + memory RSS efficiency.
- Secondary Signal: AST cyclomatic complexity, test coverage integrity, zero assertion degradation.

## Hard Gates (must pass: binary)
1. **Zero Test Regressions**: All existing unit, integration, and invariant tests must pass 100%.
2. **Adversarial Skeptic Audit**: Zero assertion weakening (`assert True`), zero empty test bodies, zero hash tampering.
3. **SMT Safety Invariants**: Zero unbounded global state mutations, correct lock pairing, zero unhandled recursion.
4. **Failure Constraint Adherence**: Candidate diff must not repeat patterns listed in `CONSTRAINTS.md`.

## Soft Gates (should meet: proportional)
- Latency improvement >= 15% on target benchmark.
- Memory RSS reduction or zero allocation overhead in hot paths.
- Code brevity: minimal diff complexity, no dead code.

## Resource Quotas
- Maximum wall-clock time per test stage: smoke (<1s), scout (<5s), complete (<30s).
- Maximum memory RSS footprint: <= 512KB for stream joins, <= 2MB total heap.

## Budget
- Active context memory: <= 500 tokens for `.autoevolve/gems.md`.
- Exploration budget: 70% exploitation of proven families, 30% orthogonal coordinates.
