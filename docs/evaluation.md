# Evaluate useful outcomes

No agent-outcome experiment or token-saving result is included in this release.
Installer tests measure distribution reliability, not reasoning quality.

## Reproducible comparison

1. Freeze a small task set containing a repair, a feature, and a performance task.
   Publish each starting repository commit, user request, environment, and
   independently maintained acceptance/guardrail commands before running agents.
2. Compare the same host and model with no AutoEvolve instructions, the previous
   protocol at a recorded commit, and the current protocol at a recorded commit.
   Keep access, tools, inputs, budgets, and pricing date identical.
3. Repeat every task in every condition at least five times, randomizing order.
   Use clean isolated checkouts and sessions. Retain failed, timed-out, and
   interrupted runs in the data; document exclusions before looking at results.
4. Verify actual instruction activation separately, including coexistence with
   existing rules. An installation exit code is not evidence of activation.
5. Run the frozen acceptance checks independently of the implementation agent.
   Record failures, out-of-scope edits, weakened checks, and budget overshoots.
6. Publish raw per-run records, commands, diffs, logs, and an analysis script.
   Report variability and task-level results rather than only aggregate averages.

## Per-run record

Use CSV or JSON with these fields:

```text
task_id, run_id, condition, repo_commit, protocol_commit,
host_version, model_version, environment, workload, seed,
activation_verified, acceptance_passed, guardrails_passed,
attempts, elapsed_seconds, tool_calls, user_interventions,
input_tokens, output_tokens, cached_tokens, total_cost, pricing_date,
stop_reason, budget_overshoot, out_of_scope_edits, evidence_paths
```

Use null for unavailable usage. Never turn missing telemetry into zero.
For performance tasks, record repeated baseline and candidate measurements under
the same conditions, including warmup and noise; predeclare the comparison rule.

## Decision criteria

Primary outcome: independently verified completion within budget with all
guardrails intact. Report its fraction over **all** scheduled runs.

Cost per verified success is total cost across all runs divided by the number of
verified successes. With no successes it is undefined, not zero. Also compare
elapsed time, interventions, activation failures, and stop-limit violations.

Adopt an efficiency claim only if verified success and guardrail results are
maintained or improved and the cost/time difference survives repeated runs.
Publish the task mix, versions, sample size, variability, and limitations with the
claim. Smaller prompt bytes alone do not establish lower tokens or better outcomes.
