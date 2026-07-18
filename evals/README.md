# Evals

The mindset preaches "define a signal and measure." This folder turns that on AutoEvolve
itself: a **runnable** way to check whether the mindset actually changes an agent's behavior
for the better, instead of just asserting it does.

Each scenario in [`scenarios/`](scenarios/) ships **broken starter code** plus a grader that
is kept **separate** from the code under test (the ruler stays out of the thing it measures).
The starter fails on purpose. That gap is what a good run should close. There is no LLM in
here and no dependencies: the "agent" is whatever tool you drive with the mindset loaded,
and the grader is the honest signal.

## Run it

```bash
python3 evals/run.py                 # list scenarios
python3 evals/run.py 01_bugfix       # grade one (FAIL on the untouched starter)
python3 evals/run.py --all           # grade every scenario
```

The A/B for each scenario:

1. **Baseline:** run the grader on the untouched starter. It fails. That is the gap.
2. **Treatment:** point your agent (with `AGENTS.md` or your tool's adapter loaded) at the
   scenario's code and let it work. Re-run the grader. It should pass.
3. **Control (optional):** do the same in a repo **without** AutoEvolve loaded, and compare
   how the two runs behaved on the rubric below.
4. Repeat a few times and compare the **medians**: best-of-N is vanity, the median is the
   truth.

## Rubric (score each run 0, 1, or 2)

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Defined a signal first | never named "better" | vague | named a concrete, checkable signal before editing |
| Smallest change | broad rewrite | partly focused | one small, targeted diff |
| Verified | claimed done, unverified | ran something | ran the grader and read the real output |
| Kept or reverted correctly | left a broken/unverified edit | mixed | kept only a verified win, reverted the rest |
| Journaled | no trace | partial | one clear line per experiment |
| Guardrails intact | dropped validation/safety | minor gap | validation, error handling, security all held |
| Avoided over-engineering | added needless code/deps | some | reused / stdlib / one-line where possible |

The grader tells you **whether** the task got solved. The rubric tells you **how** it got
solved. A treatment run that beats control across several tries is the mindset doing its
job. A dimension where it does not is a bug in the mindset text, and a good candidate for the
next change to `AGENTS.md`.

## Scenarios
- [`01_bugfix`](scenarios/01_bugfix/) - a crash on empty input (signal: a failing grader).
- [`02_optimize`](scenarios/02_optimize/) - a slow O(n^2) function (signal: correctness plus a scaling ratio).
- [`03_feature`](scenarios/03_feature/) - add pagination (signal: acceptance checks, including input validation).

Each scenario's own README states its task, its signal, and what a good run looks like.
