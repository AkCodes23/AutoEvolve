# Evals

The mindset preaches "define a signal and measure." This folder turns that on AutoEvolve
itself. It contains a compact smoke harness, a prompt ablation profiler, and a protocol for
measuring real tool-using agents without mistaking a one-shot completion for the product.

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
4. Repeat using randomized order and report every attempted trial. See
   [`../docs/BENCHMARK.md`](../docs/BENCHMARK.md) for the release-grade protocol.

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
- [`01_bugfix`](scenarios/01_bugfix/) - a crash on empty input (signal: the fix must be in the shared function, not per caller).
- [`02_optimize`](scenarios/02_optimize/) - a slow O(n^2) function (signal: correctness plus a counted comparison budget).
- [`03_feature`](scenarios/03_feature/) - add pagination (signal: acceptance checks, including input validation).
- [`04_refactor`](scenarios/04_refactor/) - extract a helper (signal: the caller must actually delegate to it).
- [`05_security`](scenarios/05_security/) - four vulnerabilities (signal: behavioral, with valid inputs still working).
- [`06_errorhandling`](scenarios/06_errorhandling/) - a fragile pipeline (signal: failures handled AND success paths intact).
- [`07_yagni`](scenarios/07_yagni/) - a tiny parser (signal: correct behavior at low surface area).
- [`08_reuse`](scenarios/08_reuse/) - a helper for this already exists in the file (signal: does the fix call it, or reimplement it).
- [`09_collateral`](scenarios/09_collateral/) - one reported symptom, several callers with documented contracts (signal: is the shared contract fixed, or only the call site that complained).
- [`10_scope`](scenarios/10_scope/) - a one-line fix in a file full of invitations to do more (signal: correct fix at unchanged surface area, adjacent behavior untouched).
- [`11_complexity`](scenarios/11_complexity/) - two wasteful functions, one quadratic and one that allocates a list it never needed (signal: counted operations AND peak allocation, so a fix that improves time and ignores memory is caught).

### Two kinds of scenario, and why both exist

Scenarios 01 to 07 ask **can the model do the task**. They are calibrated so the broken starter
fails, and a capable model solves most of them from the task description alone. That makes them
good regression tests and poor discriminators: a 70-trial run found five of seven scoring 100
percent under every instruction condition, so most trials carried no information about the
conditions at all.

Scenarios 08 to 10 ask a different question: **does the instruction text change what the model
does when it already knows how to make the code work.** Each is built so that a functionally
correct but undisciplined answer still loses checks, because it reimplemented a helper that was
already there, fixed only the symptom that was reported, or added configurability nobody asked
for. Those are disciplines the competitor rulesets state explicitly too, so the scenarios are
not written to favor AutoEvolve: `10_scope` in particular tests karpathy's most specific claim
("no flexibility or configurability that wasn't requested", "don't improve adjacent code"), and
`08_reuse` tests a ladder rung that karpathy does not have. An instrument that only contains
tests one competitor wins is not an instrument.

Scenarios 01 to 04 have their own README stating the task, the signal, and what a good run looks
like. Every scenario's grader is the authoritative statement of its contract.

Each grader is designed against two failure modes, and a change to one should be checked against
both. A grader is **gameable** if a solution that does not really solve the task scores full
marks, and it commits a **false failure** if a correct, idiomatic solution is rejected for
over-specified reasons (an exact message string, a required helper name, counting docstring lines
as code). The second is easy to miss and matters here, because a project that preaches minimalism
must not ship a ruler that punishes the minimal correct answer.

## Benchmark a tool-using agent

`agent_benchmark.py` gives an external agent a disposable repository checkout, the same
task file, and one randomized condition at a time. It writes `AGENTS.md` only for the `autoevolve` condition, keeps the grader outside the agent workspace, and grades the resulting
code in the Docker sandbox. The runner command is executed without a shell and is your
explicit authorization to invoke that agent locally.

```bash
export AUTOEVOLVE_EVAL_IMAGE='python:3.12-alpine@sha256:<verified-digest>'
python3 evals/agent_benchmark.py \
  --manifest evals/agent_manifest.example.json \
  --runner 'your-agent-command --task TASK.md' \
  --runs 10 \
  --output evals/results/local-agent-benchmark.jsonl
```

The example manifest uses a public starter task only to prove the runner works. Do not use it
to support a product-performance claim. Define held-out tasks and reporting thresholds using
[`../docs/BENCHMARK.md`](../docs/BENCHMARK.md).

## Profile the context: does the mindset help, or just add tokens?

A long always-on prompt can make a model *worse*, not better, by diluting its attention. To
check that on real models, `evals/profile.py` runs the same scenarios under four conditions that
differ only in what instruction text is in the system prompt: **control** (none), **karpathy**
and **ponytail** (the two competitor rulesets in [`competitors/`](competitors/)), and
**autoevolve** (the whole of `AGENTS.md`, which is the only profile). It grades each output and
reports two rates, the work done, and the average prompt-token cost per condition.

The two competitor arms are the interesting ones: AutoEvolve describes itself as a synthesis of
those sources, so "does the synthesis beat either source alone" is the claim worth testing, and
it is a harder bar than beating an unguided control.

### Measure work, not price

Tokens are what a condition costs you. Checks passed are what it scored. Neither is the work, and
the work is the claim: smallest correct diff, deletion over addition. Every trial records `churn`
(lines added plus removed against the starter), `lines_added`, `lines_removed` and
`starter_lines_kept`, all computed from the produced source with no extra model calls:

```bash
python3 evals/work_report.py --model <model> evals/results/*.jsonl
```

Always pass `--model` unless every model finished every cell. A mean pooled across models is not a
comparison: a condition whose rows happen to come from the weakest model looks worse for that
reason alone, and the tool prints a warning rather than letting it pass quietly.

`profile.py --regrade <file>` backfills the work axis onto datasets recorded before it existed.

Read the **graded checks** column, not only **strict pass**. Strict pass requires every check in
a scenario to hold, which throws away most of what a trial measured: a scenario with 15 checks
carries far more information than one bit. Run `--tokens` for the exact context cost of each
condition.

```bash
# Pull and independently verify an immutable Python image digest first.
export AUTOEVOLVE_EVAL_IMAGE='python:3.12-alpine@sha256:<verified-digest>'
export GROQ_API_KEY=...        # your key, read from the environment, never committed
python3 evals/profile.py --selftest                     # offline: check the pipeline
python3 evals/profile.py --runs 5                        # a small model (effect shows most here)
python3 evals/profile.py --model llama-3.3-70b-versatile --runs 10 --output results.jsonl
```

Read the result as a signal: if **autoevolve** does not beat **control**, the instruction text is
not earning its tokens, and if it trails **control** the context is hurting, which is the thing worth knowing before you ship a big
instruction file. Model output is evaluated only in a no-network Docker sandbox with a read-only
mount, no inherited environment, no Linux capabilities, and strict resource limits. There is no
flag that turns this off: the local grading path is reachable only for the repository's own
starter files, via a parameter named for that purpose. The profiler fails closed if Docker or the
digest-pinned image is missing.
It randomizes trial order, records a seed and prompt hash, and includes API/grader failures
in the denominator. Uses Groq's OpenAI-compatible API and never runs in CI because it costs
API calls. It remains a prompt ablation, not evidence that an interactive coding agent has
followed the full loop; use the benchmark protocol for that claim.

