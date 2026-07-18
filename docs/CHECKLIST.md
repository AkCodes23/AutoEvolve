# The operating checklist

The full scope of the AutoEvolve mindset as a checklist you can literally follow on any
task. This is the standalone version of the "what all to do" section in
[`../AGENTS.md`](../AGENTS.md).

## Set up the objective
- [ ] Find the human-owned goal/spec that defines "better." If it's missing or vague,
      propose one and ask the human — don't silently invent it.
- [ ] Identify the signal and its read-only source. Never edit, wrap, or "improve" the
      scorer/harness — optimize the objective, never the ruler.
- [ ] Turn the stated goal into one or more numbers a *run* produces.
- [ ] Locate or write the cheapest automatic check. Confirm a clean git tree with HEAD =
      current best. Record the baseline.

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
- [ ] Commit before running, so the experiment is a discrete revertible unit.

## Verify
- [ ] Run cheap-first: parses/compiles → fast smoke test → full check. Abort a candidate
      at the first stage it fails.
- [ ] If timed, use a fixed equal budget (excluding warm-up); read back only the
      metric/status line rather than the whole log.
- [ ] Read the actual stderr / expected-vs-actual before deciding anything.
- [ ] Track multiple qualities (correctness, speed, memory, size, readability), not one.

## Keep or revert
- [ ] Keep only on a strict improvement with no forbidden regression — OR neutral-but-
      simpler — OR a deletion.
- [ ] Reject a tiny gain that adds hacky complexity.
- [ ] Otherwise hard-revert to the last accepted state; never leave an unverified edit in
      the tree.
- [ ] Note the best idea per niche (fastest / smallest / clearest) in the journal, and
      cross-pollinate between them.

## Record and continue
- [ ] Append one journal row: commit / signal / status / what you tried.
- [ ] Leave one runnable assert-based check for non-trivial logic; none for trivial
      one-liners.
- [ ] Mark any deliberate corner-cut with an `evolve:` comment naming the ceiling and the
      upgrade path.
- [ ] Don't pause to ask "should I continue?" — refuel ideas (re-read sources, combine
      near-misses, try a radical change). On a plateau, switch modes.

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
