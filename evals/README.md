# Evals

The mindset preaches "define a signal and measure." This folder is that discipline turned
on AutoEvolve itself: a way to check whether the mindset actually changes an agent's
behavior for the better, instead of just asserting it does.

It is a **manual A/B methodology**, not an automated score. Running an agent needs an LLM
and a harness that this repo deliberately does not ship (no dependencies, no keys). What it
does ship is a repeatable procedure and concrete tasks, so anyone can measure the effect
for their own tool in an afternoon.

## How to run it

For each scenario in [`scenarios/`](scenarios/):

1. **Control:** give the task to your agent in a repo **without** AutoEvolve loaded.
2. **Treatment:** give the identical task in a repo **with** `AGENTS.md` (or your tool's
   adapter) loaded.
3. Score both transcripts on the rubric below.
4. Repeat a few times and compare the **medians** (best-of-N is vanity; the median is the
   truth). Report control vs treatment.

## Rubric (0, 1, or 2 each)

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Defined a signal first | never named "better" | vague | named a concrete, checkable signal before editing |
| Smallest change | broad rewrite | partly focused | one small, targeted diff |
| Verified | claimed done, unverified | ran something | ran the signal and read the real output |
| Kept or reverted correctly | left a broken/unverified edit | mixed | kept only a verified win, reverted the rest |
| Journaled | no trace | partial | one clear line per experiment |
| Guardrails intact | dropped validation/safety | minor gap | validation, error handling, security all held |
| Avoided over-engineering | added needless code/deps | some | reused / stdlib / one-line where possible |

A higher treatment score than control on the same task, across several runs, is the
signal that the mindset is doing its job. A dimension where treatment does **not** beat
control is a bug in the mindset text, and a good candidate for the next change to
`AGENTS.md`.

## Scenarios
- [`01-bugfix.md`](scenarios/01-bugfix.md): a crash on empty input (signal = a failing test).
- [`02-optimize.md`](scenarios/02-optimize.md): a slow function (signal = a timing benchmark).
- [`03-feature.md`](scenarios/03-feature.md): add pagination (signal = acceptance checks).
