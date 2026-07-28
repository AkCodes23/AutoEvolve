# Changelog

All notable changes to AutoEvolve are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions aim to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Pin a version when you install
so a moving `main` never changes the mindset under you.

## [Unreleased]

### Removed (BREAKING): the second profile
- **There is now exactly one mindset profile, `AGENTS.md`.** `adapters/_core.md` is deleted and the
  per-tool adapters are generated from `AGENTS.md` instead, so there is one place to edit the
  mindset and nothing to keep in sync. Maintaining two copies of the same rules is how they drift,
  and this repository had already drifted: the 10-loop cap and the deep-mode branch guidance existed
  in only one of them.
- The decision was measured, not stylistic. On the discriminating suite the condensed profile scored
  **74.4 percent at 489 tokens** against the longer profile's **69.4 percent at 913**: lower score,
  87 percent more context on every turn. See `docs/RESULTS.md`.
- `--profile core|full` is removed from `install.sh`, `install.ps1` and `autoevolve.py`
  (`install` and `setup`). Installing now copies `AGENTS.md`, full stop.
- The benchmark arm is `autoevolve`; `core` and `full` are gone. Committed datasets still carry the
  old labels, and `docs/RESULTS.md` says so where the numbers appear.
- What shipped is not byte-identical to what was measured: the surviving `AGENTS.md` is about **77
  tokens larger** than the measured winner, because the retired profile held the only definition of
  `DIRECTION.md` and `JOURNAL.md`, which `commands/`, `templates/` and the CLI depend on. That
  increment is a conventions block rather than a behavioural rule, and it is untested. Stated in
  `docs/RESULTS.md` rather than glossed over.
- Two tests pin the collapse: exactly one AutoEvolve arm exists in both harnesses, and
  `adapters/_core.md` must not reappear.

### Fixed
- `scripts/build_adapters.py` compares and writes **bytes**, always LF. Text mode normalizes
  newlines on both read and write, so `--check` reported adapters "up to date" when a rebuild would
  change every line ending in them: the committed adapters were CRLF while the source was LF, and
  the invariant could not see it. Verified by corrupting an adapter's line endings and confirming
  `--check` now fails.
- `.claude-plugin/plugin.json` and `marketplace.json` declare `3.0.0`, matching this entry. The
  manifest previously said `0.1.0` while the changelog claimed `2.0.0` and the only tag was `V0`, so
  the README's instruction to pin a version had no valid answer. Tag the release to finish this.


### Fixed (safety)
- `autoevolve.py loop` no longer runs `git checkout -- .` on a failed signal or `git add .` on a
  passing one. Both were verified to destroy a user's unrelated uncommitted edits with no reflog
  entry and no recoverable object. The loop now requires `--paths` naming what the experiment
  touched, restores those from `HEAD`, removes only untracked files it created, and refuses to
  touch the tree at all when no paths are declared.
- `autoevolve.py hooks` no longer overwrites an existing `.git/hooks/pre-commit`. Git cannot
  restore a hook it never tracked. It now skips with exit 2, or backs up with `--force`. The
  generated hook resolves an interpreter instead of hardcoding `python3`.
- `scripts/branch.py clean` no longer force-deletes every `evolve/*` branch. It uses
  `git branch -d` (which refuses unmerged work), requires `--force` to discard commits not in
  `HEAD`, has a `--dry-run`, honors `--target`, and stops instead of continuing when the
  preceding checkout fails.
- `scripts/run_quiet.py` no longer re-splits an already-parsed command. The previous
  `shlex.split(..., posix=(sys.platform != "win32"))` reported a failing command as `SUCCESS` on
  Windows and a valid `pytest -k "not slow"` as failed. Since this script's exit code decides
  keep-or-revert, that could revert a passing experiment or commit a failing one. It also now has
  a timeout, shows both output streams on failure, and maps a signal death to `128 + n`.
- `evals/sandbox.py` could never actually run for any host user other than root. `--cap-drop ALL`
  removes `CAP_DAC_OVERRIDE`, so container root could not traverse the `0700` directory
  `mkdtemp` creates, and every sandboxed grade failed with `PermissionError`. The mount is now
  readable and the container runs as the invoking user, with all capabilities still dropped.
- `evals/agent_loop_sim.py` graded raw model output on the host with no flag and no gate. It now
  grades in the sandbox and requires the same digest-pinned image the profiler does.
- `evals/profile.py` lost its `--no-sandbox` escape hatch. `grade_code`'s parameter is now
  `trusted_repo_starter=False`, named for the only input allowed to skip the container, so a
  caller passing model output gets isolation without having to ask for it.
- `evals/agent_benchmark.py` no longer forwards the entire host environment to the user-supplied
  runner. It passes an allowlist plus whatever `--env-passthrough` names, so an API key reaches a
  runner only deliberately.

### Fixed (measurement)
- Every scenario grader was repaired. Before this, `02_optimize` passed the untouched O(n^2)
  starter it exists to fail (its `sys.settrace` line counter cannot see the comparisons inside
  `x not in out`, and the clause was or-joined with the timing check that correctly failed);
  `05_security` scored a module still vulnerable in all four advertised ways at 5/5;
  `06_errorhandling` gave full marks to a module whose every function returned `None`; and
  `03_feature` gave full marks for hardcoding `per_page=10`. Graders now assert behavior rather
  than source text, and each is calibrated so the starter fails, a reference solution reaches
  full marks, a plausible cheat fails, and a stylistically different correct solution passes.
- `02_optimize` now gates on a counted comparison budget using probe elements that expose no
  readable payload. Wall-clock scaling is reported as advisory only: measured over 100 trials it
  false-failed correct code and false-passed the quadratic starter often enough that no threshold
  separated them, and a grader whose verdict depends on machine load is not a frozen signal.
- `evals/profile.py` records `checks_passed`/`checks_total` and reports a graded per-check score
  next to strict pass. Collapsing a 15-check scenario into one pass/fail bit discards most of what
  each trial measured and multiplies the trials needed to detect the same effect.
- Runs now store the graded source, and `--regrade` re-scores a stored run against the current
  graders with no model calls, so fixing a ruler no longer means paying for every inference again.
- Rows record `sandbox_image` and `max_tokens`, and `--max-tokens` is configurable so a long
  corrected file is not truncated into a failure the model did not make.
- `docs/RESULTS.md` is retracted. It published an "Empirical Benchmark Results" table while
  `docs/BENCHMARK.md` said no suite had been run: the single-turn figures were n=1 per cell, one
  of the two datasets was 12/30 `api_error` plus 5/30 `grader_error`, neither dataset was tracked
  in git, and the 86% multi-turn headline came from a runner that fed the grader's check names
  back into its own prompt.
- `evals/manifest.json` covers all 7 scenarios (it silently omitted `07_yagni`), and
  `agent_benchmark.py` gained the `karpathy` and `ponytail` arms, so both harnesses score the same
  set under the same condition names.

### Changed
- `scripts/check.py` scans the installed mindset for tool neutrality. It originally skipped the
  file the installers actually write into a target, which was the single most important file the
  invariant should have covered; with one profile that file is `AGENTS.md` and it is covered. The walk also prunes vendored directories, and a
  non-UTF-8 file is reported by name instead of aborting the other five checks.
- CI compiles every module, validates the task manifest against the scenarios on disk, parses
  `install.ps1`, and exercises the loop simulator's CLI. Previously `agent_loop_sim.py` was never
  imported by any CI step, which is where the host-execution regression lived.
- The installed core no longer instructs agents to run `scripts/branch.py` or
  `scripts/run_quiet.py`: no installer copies `scripts/` into a target, so those paths never
  resolved. The behavior is described tool-neutrally instead, and the adapters now carry a pointer
  back to `AGENTS.md`, which four documents claimed they already had.
- `scripts/check_target.py` reports readiness as a conjunction (git, `AGENTS.md`, and the
  `AutoEvolve-Core` fingerprint) rather than a 60-point total. A repository with none of the
  mindset installed used to score 65 and be reported ready, and the fingerprint test was satisfied
  by an `AGENTS.md` that said the project does *not* use AutoEvolve.
- `autoevolve.py journal` creates only `JOURNAL.md`. It previously also wrote `DIRECTION.md`,
  which every document describes as human-owned: the agent must not author its own objective.

### Added (a work axis, so the benchmark measures work rather than price)
- Every trial now records `churn` (lines added plus removed against the starter), `lines_added`,
  `lines_removed` and `starter_lines_kept`, computed from the produced source with no extra model
  calls. Tokens are an input price and checks passed are an output score; neither could see how much
  of the file a change disturbed, which is the only thing this project actually claims. "Smallest
  correct diff" and "deletion over addition" were unmeasured until now.
- `evals/work_report.py` compares conditions on work: churn, lines removed, and graded checks gained
  ABOVE THE STARTER per 10 lines changed. Credit goes only to the improvement, because scoring the
  raw total would rank a submission that changed nothing as maximally efficient.
- `profile.py --regrade` backfills the work axis onto datasets recorded before it existed, and the
  three current datasets were enriched this way with zero score changes.
- The work axis separated the conditions more cleanly than the score did on its first run, and
  produced this project's first confidence interval to exclude zero on any axis: karpathy writes
  smaller diffs than control by 1.9 lines (95% CI -3.3 to -0.5), which is what its "Surgical
  Changes" section claims. Unguided control was the least efficient worker by a wide margin, at 0.60
  checks gained per 10 lines against roughly 0.92 to 1.01 for every guided condition.
- `docs/BENCHMARK.md` gains the work metrics, plus the list of signals a real tool-using agent run
  should report instead of tokens: tool calls by kind, whether a test ever ran, turns to first green,
  reverts performed, files touched outside scope, journal lines written.

### Fixed
- `profile.py --regrade ""` silently fell through to a full paid benchmark run, because an empty
  string is falsy. An empty or missing path now fails loudly, and a nonexistent file is rejected
  before any sandbox work starts.
- The client honored Groq's `Retry-After` but clamped it to 30 seconds, so one honest wait became
  six useless retries and then an `api_error`. Measured on an 8k-TPM model at six conditions, that
  clamp produced a **50 percent** api_error rate and silently halved the usable sample. The clamp is
  now a runaway guard at 300 seconds, and `--min-interval` paces requests to stay UNDER the
  allowance rather than discovering it: the same run then recorded **zero** API failures.

### Added (the suite can now detect what it is supposed to measure)
- Four scenarios that separate instruction conditions instead of measuring raw capability. The
  existing seven are calibrated so the broken STARTER fails, which is right for "did the agent fix
  it" and useless for "did the instruction text change the outcome": a 70-trial run found five of
  the seven scoring 100 percent under every condition, so most trials carried no information. Each
  new scenario is built so a FUNCTIONALLY CORRECT but undisciplined answer still loses checks, and
  each was calibrated by scoring an independently written naive solution against a guided one:
  - `08_reuse` (starter 3/8, naive 5/8, guided 8/8): the helper the task needs already exists in
    the file and three sibling functions already call it. Tests ladder rung 2, which ponytail and
    AutoEvolve state and karpathy does not.
  - `09_collateral` (3/9, 5/9, 9/9): one reported symptom, four callers whose docstrings state
    contracts the obvious local fix leaves broken. Reproduces the strongest measured failure in
    this project's history, where 63 of 64 agents fixed the reported symptom and ignored five
    other real violations in the same file.
  - `10_scope` (0/9, 6/9, 9/9): a one-line fix in a file salted with invitations to do more.
    Written to favour karpathy, whose sections 2 and 3 state this discipline most precisely. An
    instrument that only contains tests AutoEvolve wins is an advertisement, not an instrument.
  - `11_complexity` (starter 4/7, time-only fix 6/7, both-axes fix 7/7): the first scenario to
    grade TIME and SPACE together. Counted operations for time, `tracemalloc` peak allocation for
    space. A solution that kills the obvious quadratic but still builds an intermediate list it
    never needed is caught, which no previous scenario could do.
- `evals/profile.py --condition NAME=PATH` and a `variants/` directory, so a candidate revision of
  the mindset can be A/B tested against the shipped one before it is adopted, and reverted if it
  does not win. The loop this project describes, applied to the project's own text.
- An `Algorithmic Cost` guardrail in the mindset. It previously
  said nothing about time or space complexity anywhere: the only trace was the word "size" in loop
  step 4, which meant code size. For a product whose own eval suite contains an optimisation
  scenario, that was a hole in the guidance rather than a wording preference. Step 4 now reads
  "speed and memory".

### Fixed (measurement, second pass)
- `07_yagni` priced statement count, so the scenario named for avoiding speculative generality gave
  full marks to a solution carrying a five-option `DEFAULTS` dict, an injected `config` parameter
  and a widened signature. It now prices SURFACE AREA (parameters on the entry point, module-level
  names) as well as size, and a widened signature that is only five statements long now fails.
- `02_optimize` gave full marks to a solution that deduplicates on `hash()` alone (`hash(-1) ==
  hash(-2)` in CPython, so `[-1, -2]` collapsed to `[-1]`), and was effectively binary because its
  scaling gate cannot pass while correctness fails. It gained a colliding input and an independent
  no-mutation probe.
- `05_security` gave full marks to a `build_query` that ignores its `table` argument, because both
  call sites passed the same table name.
- `04_refactor` reported a genuine cheat and a legitimate aliasing solution with the SAME score and
  the same detail text. It now falls back to a code-object swap, so `_stats = calculate_stats` and
  a captured default argument are recognised as reuse while the non-delegating cheat gets an
  unambiguous verdict.
- All eleven graders now remove their `sys.path` entry AND their cached module. A leaked module
  would shadow a later scenario sharing a filename and grade the wrong file with a plausible score.
- `scripts/check.py` compares link targets against the real on-disk spelling. `os.path.exists` is
  case-insensitive on Windows, so `docs/Principles.md` passed locally and failed Linux CI on a
  byte-identical tree.
- `scripts/callers.py` skipped the file a symbol was defined in, so every same-module caller was
  invisible: it reported "no references found" and suggested the symbol might be dead code, on
  exactly the single-file shape it exists to serve. Found by running it against `09_collateral`.

### Changed (measurement)
- Task text lives only in `evals/manifest.json`. `evals/profile.py` reads it from there instead of
  keeping a second copy, and a test fails if the manifest and `evals/scenarios/` disagree.

### Fixed (installers and cross-platform)
- `install.sh` and `install.ps1` no longer disagree about whether a hand-merged `AGENTS.md`
  counts as installed. The POSIX heading test was `^#+ AutoEvolve` (one literal space) against
  PowerShell's `^#+\s+AutoEvolve`, so `#  AutoEvolve` produced opposite verdicts, and the Windows
  path reported the unsafe "Already installed".
- `install.sh` restores the caller's umask. Setting `umask 077` inside `install_file` and never
  restoring it left installed files mode 0600 and installer-created directories 0700 regardless
  of the user's umask, while `install.ps1` wrote ordinary readable files.
- `autoevolve.py install` resolves `pwsh` then `powershell` instead of hardcoding `powershell`,
  passes `-NoProfile`, and reports a clear error when neither exists.
- `autoevolve.py setup` no longer prints "Setup complete!" when the install refused. The exit
  code was already correct; only the message claimed success, in exactly the case where the user
  most needs to know that `AGENTS.md` still needs a manual merge and nothing is active yet.
- Added `.gitattributes` (`* text=auto eol=lf`, `*.sh` LF, `*.ps1` CRLF). Without it the same
  edit produced different bytes depending on who made it, `install.sh` exited 2 on a CRLF
  checkout without installing anything, and `build_adapters.py --check` compared newline-
  normalized text so it could report the adapters up to date for a file a rebuild would change.
  Run `git add --renormalize .` once when committing so this takes effect.

### Documentation
- `skills/autoevolve/SKILL.md` now agrees with `AGENTS.md`: it states the 10-loop check-in cap
  that its "keep going when stuck" line contradicted, defines the `quick|default|deep` modes it
  advertises in `argument-hint` but never described, and carries the same revert rule.
- `evals/results/README.md` documents every dataset, marks the two pre-repair datasets VOID with
  the reason, and explains `--regrade`.

### Removed
- `evals/profile.py --no-sandbox`. The only Docker-free path that was ever legitimate is
  `--selftest`, which grades repository starter files and needs no flag.

## [2.0.0] - 2026-07-24

Multi-mode mindset plugin, universal CLI, and an expanded evaluation suite.

### Added
- Universal cross-platform CLI (`autoevolve.py`) with `install`, `init`, `check`, `setup`,
  `journal`, `hooks`, and `loop`, across Windows, Linux, and macOS.
- Pre-flight repository checker (`scripts/check_target.py`).
- Population Branch Manager (`scripts/branch.py`) for quality-diversity niche branches
  (`evolve/fast`, `evolve/small`).
- Native Windows PowerShell installer (`install.ps1`) with dry-run, core profile, and idempotency.
- Competitor evaluation instruction sets (`evals/competitors/karpathy.md`,
  `evals/competitors/ponytail.md`).
- Expanded eval scenario suite: 7 scenarios (bugfix, optimize, feature, refactor, security, error
  handling, yagni).
- A deterministic regression suite for the profiler and the sandbox controls
  (`evals/test_profile.py`, run with `unittest`).

### Changed
- `scripts/run_quiet.py` runs commands with `subprocess.run(shell=False)`.
- `scripts/build_adapters.py` verifies all four generated IDE adapters against
  `adapters/_core.md` (`claude.md`, `copilot-instructions.md`, `cursor.mdc`, `windsurf.md`).
- Installer no longer runs a remote script. `install.sh` runs only from a reviewed release
  checkout (`--target`, `--dry-run`, `--profile core|full`), defaults to the compact core
  profile, and never overwrites an existing file.
- The revert step no longer recommends `git clean`. Destructive tree cleanup was removed from
  `AGENTS.md` and the docs; a dirty tree you did not create is left untouched.
- Installer reporting is accurate. A repeat install or a hand-merged file now reports "already
  installed" and exits 0, and when adapters are written while `AGENTS.md` still needs a manual
  merge, it says the adapters are already active instead of claiming nothing was activated.

### Added
- `evals/sandbox.py`, a fail-closed Docker boundary (no network, read-only mount, dropped
  capabilities, no environment forwarding) for grading model-generated code. `evals/profile.py`
  refuses to execute model output unless a digest-pinned sandbox image is configured.
- Experimental Proof-tier scaffolding: `evals/agent_benchmark.py`, `docs/BENCHMARK.md`, and
  `docs/COMPATIBILITY.md`. These describe and run toward a real agent benchmark; no held-out
  suite has been run and no tool behavior has been verified yet.

## [0.1.0] - 2026-07-19

Initial public release: a drop-in mindset plugin for AI coding agents.

### Added
- `AGENTS.md`, the lean operating core (the loop, the ladder, the keep rule, guardrails,
  autonomy and intensity, conventions).
- `README.md`, the full explanation, and `docs/` (`PRINCIPLES`, `EXAMPLE`, `CHECKLIST`,
  `INSTALL`, `SOURCES`).
- The mindset as a loadable skill (`skills/autoevolve/SKILL.md`) and as invocable commands
  (`commands/`: `baseline`, `evolve`, `simplify`, `review`, `journal`).
- Tool adapters: Claude Code, Cursor, Windsurf, and GitHub Copilot. Codex and Antigravity
  read root `AGENTS.md` natively.
- A Claude Code plugin install path: the repo is its own plugin marketplace
  (`.claude-plugin/`), so users can `/plugin marketplace add AkCodes23/AutoEvolve` then
  `/plugin install autoevolve@autoevolve` instead of copying files.
- One source of truth for the adapters (`adapters/_core.md`) plus a generator
  (`scripts/build_adapters.py`) so they cannot drift.
- A one-command installer (`install.sh`) that auto-detects your tools, and starter
  templates (`templates/DIRECTION.md`, `templates/JOURNAL.md`).
- A runnable eval harness (`evals/run.py`) and a context profiler (`evals/profile.py`) for
  measuring the mindset's real effect on a model, including its token cost per turn.
- A self-check (`scripts/check.py`) and CI that enforce the repo's own invariants (no em
  dashes, tool-neutral core, links resolve, adapters generated, plugin JSON valid) and keep
  the eval harness wired.

[2.0.0]: https://github.com/AkCodes23/AutoEvolve/releases/tag/v2.0.0
[0.1.0]: https://github.com/AkCodes23/AutoEvolve/releases/tag/V0

> **Version note.** These entries are ahead of what is actually taggable. `.claude-plugin/plugin.json`
> declares `0.1.0`, the only git tag is `V0`, and both documented clone commands pin `V0`, so the
> `v2.0.0` link above does not resolve. Before publishing another release, make the manifest
> version, the git tag, and the install instructions agree: the README tells users to pin a
> version, and today no value satisfies that instruction.
