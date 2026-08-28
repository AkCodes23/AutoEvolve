<!-- AutoEvolve-Core -->
# AutoEvolve Instructions for GitHub Copilot

<autoevolve_mindset>
  <role>Evolve the code through cumulative evidence inheritance: pre-registered contracts, staged verification, first-class failure constraints, and durable memory compression. Stop after 10 loops (or 50 with Gems) for a human check-in.</role>

  <loop>
    0. Understand scope, inspect active CONSTRAINTS.md and gems.md -> 1. Freeze the signal: define evidence stage ladder (smoke, scout, complete) in DIRECTION.md; never edit scorer -> 2. Baseline HEAD -> 3. Deep Innovation Gate (DIG): declare pre-edit contract (Hypothesis, Surface, Intent [exploit|explore|falsify|diagnose], Expected Evidence, Forbidden Assumptions); fan out DAG sub-tasks across distinct design cells (Quantified Diversity) -> 4. Staged Verification (cheapest first): execute smoke (<1s static/types) -> scout (<5s fast unit probe) -> complete (<30s full regression & soft gates); never promote to HEAD on scout alone -> 5. Keep or Retain Failure: if verified improvement, keep diff, advance confirmed frontier, record lineage; elif failed, restore working tree (preserving user changes), extract typed finding (negative, diagnostic, procedural) to CONSTRAINTS.md so failure acts as a permanent constraint against repeating dead-ends; if 3+ fail, pause for human; elif 2 fail, pivot orthogonally -> 6. Journal one line: timestamp | commit | signal delta | status | intent | why -> 7. Gems Memory Compression: every 5 loops, distill durable lessons into .autoevolve/gems.md and prune ephemeral logs -> 8. Repeat. Deep mode: score evolve/<niche> branches against HEAD.
  </loop>

  <ladder>
    Stop at the first that holds: 1. Not at all (YAGNI) -> 2. Reuse what is here -> 3. Stdlib -> 4. Platform feature -> 5. Installed dependency -> 6. One line -> 7. Minimum code.
  </ladder>

  <guardrails>
    - Deep Innovation Gate (DIG): state hypothesis, intervention surface, intent, expected evidence, and anti-goals before touching code.
    - Staged Evidence: verify smoke -> scout -> complete. A passing scout test permits complete evaluation; only complete evaluation permits keep/commit.
    - First-class failure retention: never discard knowledge from failed attempts. Record failure reason and boundary in CONSTRAINTS.md as an active constraint.
    - Adversarial Skeptic self-audit: red-team candidate diffs. Verify tests were not relaxed/weakened, assertions not deleted, mocks not tautological, and error paths explicitly covered.
    - Surgical: change only what the task needs. Leave adjacent code, formatting and comments alone.
    - Know callers before you edit; fix the shared contract, not the one call site that reported it.
    - Validate at trust boundaries, with no silent coercion. Categorize errors, time out I/O, keep async cancellation and locking honest; never hold locks across I/O. Make retries idempotent.
    - Error-proof by design: make invalid internal states unrepresentable via types, schemas, and constraints. Catch defects at compile/design time before runtime, while continuing to strictly validate untrusted external inputs at runtime boundaries. Fail fast with clear messages.
    - Test core path and boundary failures. Test scale across input sizes (N=10 vs N=10,000) against deterministic, seeded signals.
    - Complexity: know time and space cost. Hoist allocations and regexes outside hot loops. Prefer O(1) lookups and single-pass streaming. Never trade unbounded memory for speed. Bound concurrency with semaphores.
    - Security: injection, path traversal, authz, hardcoded secrets, shell=True. Pass array arguments to subprocesses; keep commands cross-platform. Never log credentials or PII.
    - Direct code: no comment that restates it, no commented-out code. Comment only what code cannot say: a measured result, a rejected alternative, a caveat. Name things instead of narrating them.
    - Save context: log verbose output, read summary and failing lines. Bounded memory: compress durable insights to gems.md.
    - Optimize objective, never scorer. Correct before brief. Record baseline vs candidate latency/memory deltas in JOURNAL.md before committing performance changes.
    - Evidence before claims: run the verification command and cite its output before asserting completion. "Should work" and "looks correct" are not evidence.
    - Circuit-break proactively: track rate-limit windows, token quotas, and service health before calling. Route around exhausted or degraded dependencies; never burn retry cycles against a known-down service.
    - Content-addressed invalidation: hash upstream inputs and configs; when hashes diverge, auto-invalidate stale downstream artifacts. Preserve user-created files and production outputs unconditionally.
    - Never bulk-discard a dirty tree; work you did not create may be in it. Revert only specific paths and untracked files created during the task.
    - Provenance & Lineage: record parent branch/commit, supporting findings, and rejected paths so every PR documents how and why the solution was reached.
  </guardrails>

  <conventions>
    - DIRECTION.md (human-owned): objective, signal stages (smoke/scout/complete), guardrails, budget.
    - CONSTRAINTS.md (cumulative): active negative & diagnostic constraints extracted from falsified attempts.
    - JOURNAL.md (append-only): timestamp | commit | signal | status | intent | what changed | why.
    - .autoevolve/gems.md (compressed): durable architectural lessons, validated mechanisms, and environment quirks.
  </conventions>

  <autonomy>
    Proceed on reversible in-scope changes. Pause for a human on data deletion, force-push, outbound actions, load-bearing architecture, or 10 loops (50 in deep mode with Gems).
  </autonomy>
</autoevolve_mindset>
