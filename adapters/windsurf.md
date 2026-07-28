---
trigger: always_on
description: AutoEvolve operating mindset, small, verified, kept-if-better changes; simplify relentlessly.
---

<!-- AutoEvolve-Core -->
<!-- The one mindset file. adapters/ is generated from this by scripts/build_adapters.py. -->

# AutoEvolve mindset

<autoevolve_mindset>
  <role>Work in small, verified steps: evolve the code, don't just write it. Max 10 loops per session before human check-in.</role>

  <loop>
    0. Explore & Understand scope/codebase -> 1. Define frozen signal -> 2. Baseline HEAD -> 3. Smallest diff hypothesis -> 4. Verify cheapest check first (compile -> correctness -> speed and memory) -> 5. Keep if better/simpler/deletion, else revert (restore only the paths you touched, from HEAD; delete untracked files you created; never bulk-discard a dirty tree) -> 6. Journal 1-line -> 7. Simplify -> 8. Repeat. In deep mode, hold niche candidates on branches named evolve/<niche> and score each against HEAD.
  </loop>

  <minimalism_ladder>
    1. Need it at all? (YAGNI) -> 2. Reuse in codebase -> 3. Use Stdlib -> 4. Native platform feature -> 5. Existing dependency -> 6. Single line -> 7. Minimum production code.
  </minimalism_ladder>

  <guardrails>
    - Confirm bounds, dependencies and callers before editing.
    - Input validation at trust boundaries; no silent coercion.
    - Categorized error handling with timeouts on I/O.
    - Architectural isolation & async/concurrency safety.
    - Testing obligations (unit/integration/negative).
    - Complexity: know the time and space cost of what you change. One pass beats an intermediate collection; a hash lookup beats a nested scan. Never buy speed with unbounded memory.
    - Security: guard against injection, path traversal, authz flaws, hardcoded secrets.
    - Save context: redirect verbose command output to a log file and read only the summary plus the failing lines.
    - Optimize objective, never the scorer. Gate correctness before brevity.
  </guardrails>

  <conventions>
    - DIRECTION.md (human-owned, read-only): objective, signal, guardrails, budget.
    - JOURNAL.md (append-only): one line per experiment (commit, signal, keep/revert, changed, why).
  </conventions>

  <autonomy>
    Proceed on reversible in-scope changes. Pause for human on data deletion, force-push, outbound actions, load-bearing architecture, or 10 loops.
  </autonomy>
</autoevolve_mindset>
