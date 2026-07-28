# The operating checklist

The full scope of the AutoEvolve mindset as a checklist you can literally follow on any
task. It expands the loop in [`../AGENTS.md`](../AGENTS.md) into a tickable list.

## Set up the objective
- [ ] Read `DIRECTION.md` if it exists (human-owned, read-only). If it's missing or vague,
      propose one and ask the human; don't silently invent the objective.
- [ ] Identify the signal and its read-only source. Never edit, wrap, or "improve" the
      scorer/harness: optimize the objective, never the ruler.
- [ ] Turn the stated goal into a concrete signal a *run* produces: a number, a
      red-to-green test, or an acceptance check you can confirm.
- [ ] Locate or write the cheapest automatic check. Confirm a clean git tree with HEAD =
      current best. Record the baseline.
- [ ] Reserve a never-drop **canary** case and hold out / rotate some inputs: a signal
      you keep beating may mean you're overfitting it, not improving. (The signal's
      *definition* stays frozen; the canary and held-out inputs cross-check it.)

## Understand before mutating
- [ ] Read the surrounding code, trace the data flow, locate the root cause.
- [ ] Assemble tight context: current code + a couple of scored prior attempts + the last
      run's real error. Evict the rest.

## Make the change
- [ ] Walk the decision ladder in order; stop at the first rung that holds.
- [ ] Prefer deletion / reuse / stdlib / installed-dependency / one-line over new code and
      new dependencies.
- [ ] Make one small, targeted diff for one hypothesis; leave surrounding working code
      identical.
- [ ] Fix bugs at the root cause: grep every caller, fix the shared function once.
- [ ] Write it directly: no comment that restates the line, no commented-out code, no
      docstring that only repeats the function's own name and parameters. A comment earns
      its place by recording what the code cannot, which is nearly always a *why*. When
      you want to narrate a line, rename something instead.
- [ ] Keep the tree clean before you edit, so a rejected change reverts cleanly; don't
      commit until it verifies.

## Verify
- [ ] Run cheap-first: parses/compiles → fast smoke test → full check. Abort a candidate
      at the first stage it fails.
- [ ] If timed, use a fixed equal budget (excluding warm-up); read back only the
      metric/status line rather than the whole log.
- [ ] Read the actual stderr / expected-vs-actual before deciding anything.
- [ ] Confirm you did not move the goalposts: `python3 scripts/ruler.py` reports what your
      change did to the tests that judge it. A green suite you edited is not evidence.
- [ ] Track multiple qualities (correctness, speed, memory, size, readability), not one.

## Keep or revert
- [ ] Keep only on a strict improvement with no forbidden regression, OR neutral-but-
      simpler, OR a deletion. On keep, commit it: HEAD is now your best-known state.
- [ ] Reject a tiny gain that adds hacky complexity.
- [ ] Otherwise revert **only the experiment's known files** after inspecting the list.
      Never run `git clean` or discard a dirty tree you did not create. Use a dedicated
      worktree when an experiment may create many files or affect a load-bearing area.
- [ ] Note the best idea per niche (fastest / smallest / clearest) in the journal, and
      cross-pollinate between them.

## Record and continue
- [ ] Append one journal row: commit / signal / status (keep|revert) / what changed / why.
- [ ] Leave one runnable assert-based check for non-trivial logic; none for trivial
      one-liners.
- [ ] Mark any deliberate corner-cut with an `evolve:` comment naming the ceiling and the
      upgrade path.
- [ ] Don't pause to ask "should I continue?"; refuel ideas instead (re-read sources,
      combine near-misses, try a radical change). On a plateau, switch modes.

## Never skip (guardrails)
- [ ] Input validation at trust boundaries, error handling that prevents data loss,
      security, accessibility, and anything explicitly requested.
- [ ] Sandbox untrusted or self-generated code before executing it against real systems.
- [ ] Keep the accepted change interpretable, debuggable, and deployable in the real repo.

## Pause for a human when
- [ ] A change would cross a guardrail (security, data loss, an irreversible or outbound
      action, spending real money/credentials).
- [ ] The signal and a human spot-check disagree.
- [ ] The only way forward requires touching the frozen signal/harness.
- [ ] The objective itself is missing or ambiguous.
