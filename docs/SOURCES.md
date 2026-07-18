# Sources & attribution

AutoEvolve is an independent synthesis of ideas from four bodies of work. It is not
affiliated with or endorsed by any of them. Each contributes a distinct layer of the
mindset.

### An evolutionary coding-agent approach: *AlphaEvolve* (Google DeepMind)
The execution-grounded core: every change is a hypothesis that is **false until a run
proves it**, judged as a delta against a recorded baseline. Minimal targeted diffs (so a
score change is attributable). The cheap-first evaluation cascade (parse → smoke test →
full check). Tracking several objectives at once. Keeping a **diverse pool** of good
solutions, the best per niche, with cross-pollination to escape local optima. Feeding the
last run's real errors and a few scored priors into the next change. Keeping the accepted
artifact interpretable, debuggable, and deployable.
*Reference: "AlphaEvolve: A Gemini-powered coding agent for designing advanced algorithms"
(arXiv:2506.13131).*

### An autonomous-research recipe: *autoresearch* (Andrej Karpathy)
The tight keep/discard experiment loop and its discipline: a human-owned, read-only
direction file; a **frozen, un-gameable metric** (optimize the objective, never the
scorer); git-as-experiment-store with HEAD = best-known state; **one small change per
experiment**; equal fixed run budgets; radical context frugality (redirect a run to a log,
read back one metric line); an append-only journal; the "**never stop mid-loop, refuel
ideas instead**" rule; and simplicity baked into the keep rule (deletions and
neutral-but-simpler changes are wins).
*Reference: github.com/karpathy/autoresearch.*

### A "laziest senior dev" minimalism ruleset: *ponytail* (DietrichGebert)
The verbatim decision **ladder** and its "understand fully first" precondition. Deletion
over addition, boring over clever, fewest files. Root-cause-not-symptom fixes (grep every
caller, fix the shared function once). The non-negotiable guardrails (validation, error
handling that prevents data loss, security, accessibility, explicit requests). One runnable
assert-based check for non-trivial logic. Marking deliberate corner-cuts with a comment
naming the ceiling and upgrade path. Gating correctness/safety before rewarding brevity,
intensity modes, and honest evaluation (source vs. test size, adversarial execution, a
model-judge only for catching dropped requirements, medians over N runs). Its distribution
shape, *one source of truth, many thin adapters*, is the shape of this repo.
*Reference: github.com/DietrichGebert/ponytail.*

### General guidelines for building with LLMs: *Andrej Karpathy*
The framing that **verification, not generation, is the bottleneck**, so shrink
verification time first and fear big diffs. Designing around model failure modes: jagged
competence (verify even "obvious" steps), no persistent memory (engineer external memory,
curate context like RAM), gullibility (sandbox untrusted and self-written code). The evals
crisis: distrust green benchmarks, layer cheap hard-to-game checks + rotating holdouts + a
never-drop canary + human spot-checks. Prompts-as-programs (version, review, debug them).
Resumable, revertible, interruptible runs. And the **autonomy slider**, build the
augmentation suit with a human on the leash, raising autonomy one notch at a time.
*References: "Software Is Changing Again" (Software 1.0/2.0/3.0), the LLM-OS framing, and
his talks/writing on agents and evals.*

---

## Further reading
- AlphaEvolve paper, arXiv:2506.13131
- `karpathy/autoresearch` on GitHub
- `DietrichGebert/ponytail` on GitHub
- Karpathy, "Software Is Changing Again" (YC AI Startup School, 2025)
