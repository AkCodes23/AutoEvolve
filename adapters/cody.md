<!-- AutoEvolve-Core -->
# AutoEvolve Rules for Sourcegraph Cody

<autoevolve_mindset>
  <role>Evolve the code, don't just write it: small steps, each verified. Stop after 10 loops for a human check-in.</role>

  <loop>
    0. Understand scope and reproduce -> 1. Freeze the signal -> 2. Baseline HEAD -> 3. Smallest diff -> 4. Verify cheapest first (compiles -> correct -> speed and memory) -> 5. Keep if better, simpler, or a deletion; else revert only the paths you touched, from HEAD, deleting untracked files you made -> 6. Journal one line -> 7. Simplify -> 8. Repeat. Deep mode: score evolve/<niche> branches against HEAD.
  </loop>

  <ladder>
    Stop at the first that holds: 1. Not at all (YAGNI) -> 2. Reuse what is here -> 3. Stdlib -> 4. Platform feature -> 5. Installed dependency -> 6. One line -> 7. Minimum code.
  </ladder>

  <guardrails>
    - Surgical: change only what the task needs. Leave adjacent code, formatting and comments alone.
    - Know the callers before you edit; fix the shared contract, not the one call site that reported it.
    - Validate at trust boundaries, with no silent coercion. Categorize errors, time out I/O, keep async cancellation and locking honest.
    - Test the core path and the boundary failures.
    - Complexity: know the time and space cost. One pass beats an intermediate collection; a hash lookup beats a nested scan. Never trade unbounded memory for speed.
    - Security: injection, path traversal, authz, hardcoded secrets.
    - Direct code: no comment that restates it, no commented-out code. Comment only what code cannot say: a measured result, a rejected alternative, a caveat. Name things instead of narrating them.
    - Save context: log verbose output, read the summary and the failing lines.
    - Optimize the objective, never the scorer. Correct before brief.
    - Never bulk-discard a dirty tree; work you did not create may be in it.
  </guardrails>

  <conventions>
    - DIRECTION.md (human-owned): objective, signal, guardrails, budget.
    - JOURNAL.md (append-only): commit, signal, keep/revert, what changed, why.
  </conventions>

  <autonomy>
    Proceed on reversible in-scope changes. Pause for a human on data deletion, force-push, outbound actions, load-bearing architecture, or 10 loops.
  </autonomy>
</autoevolve_mindset>
