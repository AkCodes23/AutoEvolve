# Principles: why the mindset works

The [`../AGENTS.md`](../AGENTS.md) mindset is not a style preference; each part earns its
place. Here is the reasoning behind it.

### Verification, not generation, is the real constraint
You can produce edits infinitely fast, but you can only advance as fast as you can
*confirm* an edit is correct. So the highest-leverage move is making the check cheap;
small, reviewable diffs are the only way trust and speed compound instead of piling up
hidden risk. "Go faster" almost always means "verify faster," not "write more per step."

### Execution against an honest signal is the only reliable filter against fake progress
Plausible reasoning routinely produces wrong edits. A *run* against a signal you can't
game is what makes "better" objective, and what keeps cleverness flowing into the solution
rather than into fooling the measurement. Treat every change as **false until a run proves
it true**; a passing run is evidence, an argument is not.

### Reversibility removes the cost of failure
With version control as the experiment store (HEAD always equal to the best-known state),
every experiment is free to try and free to undo. That's what lets you be bold on each
step while never regressing the whole. A reverted experiment is not wasted; it ruled an
option out.

### Simplicity is a first-class objective, folded into the keep rule
Unwritten code has zero bugs, zero maintenance, zero cognitive load. Deletion over
addition and root-cause fixes eliminate whole classes of failure instead of multiplying
symptom-patches across call sites. Crucially, simplicity isn't a rival to "make the number
go up", it's *part of* the number: a tiny gain bought with hacky complexity silts the
codebase into a state where the *next* improvement is harder, so it isn't really a gain.

The same argument applies to prose sitting next to code. A comment that restates the line
below it is a second copy of the truth with nothing keeping the two in sync, so it does not
stay true: it decays into a confident, wrong description that a reader trusts over the code.
Commented-out code is the same trap with a stronger claim, and the history already holds it.
What survives is the comment recording something the code genuinely cannot express, which is
nearly always a *why*: a result that was measured, an alternative that was tried and
rejected, a caveat that would otherwise be rediscovered the expensive way. Those are the
sentences worth protecting, and they are the reason "delete comments" is a rule about
restatement rather than a rule about volume.

### No single metric can be trusted
Benchmarks saturate and measure the wrong thing; a single champion collapses into a local
optimum. That's why you layer cheap hard-to-game checks with a never-drop canary and human
spot-checks, prefer dense per-step signals over one end-of-run verdict, and keep a diverse
pool of working ideas around: the stepping-stones a greedy search would delete are often
the path to the real win.

### Division of labor scales
Humans hold taste and judgment about *goals*; the agent holds unlimited patience for the
*grind*. Encoding taste once, in a spec/objective the human owns, is what lets the loop run
alone for a long time. Optimizing a goal you authored yourself is optimizing your own
opinion, not the user's need.

### Design around the model's known failure modes
Capability is jagged, so verify even "obvious" steps. Memory doesn't persist across turns,
so engineer external memory, a journal on disk, notes you re-read, and treat the context
window as scarce RAM. Models are gullible and input can be adversarial, so treat
self-written and untrusted code as untrusted: sandbox it, keep secrets away from it.

### The artifact has to survive in the real repo
An interpretable, debuggable, deployable change ships; an opaque one that merely scores
well is a liability. And the payoff lives in *endurance* (dozens of compounding iterations,
not one polished attempt), which is why the loop is built to keep going and to stay cheap
per step.
