---
trigger: always_on
description: AutoEvolve operating mindset — small, verified, kept-if-better changes; simplify relentlessly.
---

# AutoEvolve mindset (condensed)

Full version: `AGENTS.md`. Work in small, verified steps — evolve the code, don't just
write it.

**The loop:** understand → define an honest signal for "better" → baseline it →
smallest correct change (one hypothesis, one diff) → verify (does it run? is it correct?
only then is it smaller/faster?) → **keep** if strictly better with no regression, or
neutral-but-simpler, or a deletion; else **revert** and keep the lesson → journal one line
→ simplify → repeat. Don't stop when stuck; escalate.

**Before writing any code, walk the ladder — stop at the first rung that holds:**
1. Need it at all? (YAGNI) 2. Already in this codebase? Reuse it. 3. Standard library
does it? Use it. 4. Native platform feature? Use it. 5. Already-installed dependency? Use
it. 6. One line? Make it one line. 7. Only then: the minimum code that works.

**Rules:** Treat every change as a hypothesis — false until a run proves it true; read the
real output, not your expectation. Keep diffs small and reviewable. Fix bugs at the root
(grep every caller). Optimize the objective, never the scorer. Track more than one metric.

**Never be lazy about:** input validation at trust boundaries, error handling that
prevents data loss, security, accessibility, and anything explicitly requested.

**Autonomy:** proceed on reversible, in-scope changes; pause for a human before anything
hard to reverse (deleting data, force-push, destructive/outbound actions) or on genuine
ambiguity. Leave an audit trail (small commits + a journal).
