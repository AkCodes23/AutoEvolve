---
trigger: always_on
description: AutoEvolve operating mindset, small, verified, kept-if-better changes; simplify relentlessly.
---

<!-- AutoEvolve-Core -->
# AutoEvolve mindset (condensed)

<autoevolve_mindset>
  <role>Work in small, verified steps: evolve the code, don't just write it. Max 10 loops per session before human check-in.</role>
  
  <loop>
    0. Explore & Understand scope/codebase -> 1. Define frozen signal -> 2. Baseline HEAD -> 3. Smallest diff hypothesis -> 4. Verify cheapest check first -> 5. Keep if better/simpler/deletion, else revert (delete untracked experiment files) -> 6. Journal 1-line -> 7. Simplify -> 8. Repeat. In deep mode, use `scripts/branch.py` for population branches.
  </loop>

  <minimalism_ladder>
    1. Need it at all? (YAGNI) -> 2. Reuse in codebase -> 3. Use Stdlib -> 4. Native platform feature -> 5. Existing dependency -> 6. Single line -> 7. Minimum production code.
  </minimalism_ladder>

  <guardrails>
    - Context verification before editing.
    - Input validation at trust boundaries.
    - Categorized error handling with timeouts.
    - Architectural isolation & async/concurrency safety.
    - Testing obligations (unit/integration/negative).
    - Security: Guard against injection, path traversal, authz flaws.
    - Save context: Use `python scripts/run_quiet.py -- <cmd>` for verbose command output.
    - Optimize objective, never the scorer. Gate correctness before brevity.
  </guardrails>

  <autonomy>
    Proceed on reversible in-scope changes. Pause for human on data deletion, force-push, outbound actions, load-bearing architecture, or 10 loops.
  </autonomy>
</autoevolve_mindset>
