<div align="center">

# AutoEvolve

**Evolve the code, don't just write it: small steps, each verified.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)]()
[![Supported Platforms](https://img.shields.io/badge/platforms-12%20IDEs%20%26%20Agents-purple.svg)]()
[![CI Guardrails](https://img.shields.io/badge/CI-AI%20PR%20Guardrail-orange.svg)]()

*A minimal, zero-dependency, prompt-first engineering mindset for AI coding assistants.*
</div>

---

## ⚡ 1-Line Quick Install

Install the mindset and native editor rules in any repository in 1 second:

* **macOS / Linux / POSIX**:
  ```bash
  curl -fsSL https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.sh | sh
  ```

* **Windows (PowerShell)**:
  ```powershell
  irm https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.ps1 | iex
  ```

*AutoEvolve auto-detects your IDE (`.cursor`, `.windsurfrules`, `.github`, `.clinerules`, `.continue`, `.zed`, `.idea`, `.cody`, `.openhands`, or `.gemini`) and configures the exact native rules file.*

---

## 🎯 The Problem AutoEvolve Solves

Without strict evolutionary invariants, AI coding assistants (Claude Code, Cursor, Windsurf, Copilot) frequently default to disastrous failure patterns:

```
┌───────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────┐
│              UNSUPERVISED AI CODE CHURN                   │                   AUTOEVOLVE MINDSET                      │
├───────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
│ ❌ Weakens test assertions or edits mocks to fake passes  │ ✅ FROZEN SIGNAL: Optimizes the objective, never scorer   │
│ ❌ Changes public signatures, breaking downstream callers │ ✅ BLAST RADIUS: Audits all repo callers before editing   │
│ ❌ Dumps 10,000 lines of pytest stdout, burning 60k tokens│ ✅ CONTEXT FRUGALITY: Runs in quiet mode (-q), saves >98% │
│ ❌ Pollutes Git history with "# Fix: updated loop" noise  │ ✅ DIRECT CODE: Code shows what; comments explain why     │
│ ❌ Stuck in local minima, tweaking 1 regex for 5 turns    │ ✅ ORTHOGONAL PIVOT: If 2 loops fail, forces strategy shift│
│ ❌ Introduces path traversals or shell=True injections    │ ✅ ENTERPRISE SAFETY: Array subprocesses, path bounds     │
│ ❌ Bulk-discards git trees, destroying your dirty edits   │ ✅ TREE PRESERVATION: Restores only agent-created diffs   │
└───────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────┘
```

---

## 🔄 How It Works

AutoEvolve synthesizes **DeepMind AlphaEvolve** (grounded verification), **Andrej Karpathy's autoresearch** (keep-or-revert hypothesis loop), and **Dietrich Gebert's Ponytail** (YAGNI minimalism ladder) into a self-contained 36-line system prompt.

```
       ┌───────────────────────────────┐
       │   Human defines DIRECTION.md  │
       │   (Goal, Signal, Budget)      │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
  ┌───►│ 0. Reproduce & Freeze Signal  │
  │    └──────────────┬────────────────┘
  │                   │
  │                   ▼
  │    ┌───────────────────────────────┐
  │    │ 3. Smallest Diff (YAGNI)      │
  │    └──────────────┬────────────────┘
  │                   │
  │                   ▼
  │    ┌───────────────────────────────┐
  │    │ 4. Verify Cheapest First      │
  │    │    (Compile -> Pass -> Perf)  │
  │    └──────────────┬────────────────┘
  │                   │
  │         Improved? ├─────────────────────────┐
  │        (YES)      │                         │ (NO)
  │                   ▼                         ▼
  │      ┌─────────────────────────┐ ┌─────────────────────────┐
  │      │ 5. Keep & Commit Step   │ │ 5. Restore Pre-Loop Snap│
  │      └────────────┬────────────┘ └───────────┬─────────────┘
  │                   │                         │
  │                   ▼                         ▼
  │      ┌─────────────────────────────────────────┐
  │      │ 6. Append 1 Line to JOURNAL.md          │
  │      └────────────────────┬────────────────────┘
  │                           │
  └───────────────────────────┴─ Repeat (Max 10 loops)
```

---

## 📖 Developer Walkthrough

### 1. Human defines the goal in `DIRECTION.md`:
```markdown
# Objective
Optimize p99 latency on `/api/v1/search` without changing the JSON schema.

# Frozen Signal
pytest tests/perf/test_search.py -q

# Guardrails
- Memory peak must stay <= 15MB
- Must pass all existing unit tests: pytest tests/unit/ -q
- Budget: 5 loops
```

### 2. AI automatically runs the loop and self-documents `JOURNAL.md`:
```markdown
# JOURNAL.md
2026-08-16T11:00Z | e4f1a2 | p99: 142ms -> 88ms  | KEEP   | Added compound index on (tenant_id, created_at)
2026-08-16T11:02Z | ------ | p99: 88ms  -> 110ms | REVERT | In-memory cache caused lock contention across 50 threads
2026-08-16T11:04Z | a8c9d1 | p99: 88ms  -> 42ms  | KEEP   | Hoisted compiled regex outside search loop (Target hit!)
```

---

## 🔁 The 9-Step Evolutionary Loop

```text
0. Understand scope and reproduce
1. Freeze the signal (define test/metric before editing; never edit scorer)
2. Baseline HEAD
3. Smallest diff; identify independent sub-tasks and fan them out as a DAG
4. Verify at the join barrier: hard gates (compiles, tests pass, schema intact) must all hold;
   then evaluate soft gates (latency budgets, memory ceilings, drift thresholds) defined in DIRECTION.md proportionally
5. Keep if better, simpler, or a deletion; if 3+ consecutive loops fail, question the architecture and pause for human;
   elif 2 fail, pivot orthogonally;
   else restore only changes introduced relative to pre-loop snapshot (preserve user dirty tree)
6. Journal one line with measured metric delta
7. Simplify: prune superseded rules, enforce token budgets on guidance files, consolidate
8. Repeat (stop after 10 loops for a human check-in)
```

---

## 🪜 The 7-Rung Minimalism Ladder

Stop at the first rung that holds:

```text
1. Not at all (YAGNI)      --> Speculative requirement? Reject it.
2. Reuse what is here      --> Helper or pattern in codebase? Reuse it.
3. Stdlib                  --> Standard library has it? Use it.
4. Platform feature        --> Language/runtime primitive covers it? Use it.
5. Installed dependency    --> Already in dependencies? Use it. Never add new packages.
6. One line                --> Can it be expressed in one clean line? One line.
7. Minimum code            --> Only then, write the minimal working implementation.
```

---

## 🛡️ Core Engineering Invariants

- **Surgical Blast Radius**: Know all callers before modifying a shared signature; fix the shared contract, not just the one reporting call site.
- **Trust Boundaries & Non-Blocking Locks**: Validate external inputs without silent coercion. Categorize errors (client vs server vs dependency), time out all I/O, and never hold locks across network calls.
- **Subprocess Safety**: Pass array arguments (`subprocess.run(['cmd', 'arg'])`), never concatenated strings with `shell=True`. Keep commands cross-platform (PowerShell & POSIX).
- **Idempotency by Design**: Ensure retried database writes, event handlers, and webhooks are safe to run multiple times without duplicate side effects.
- **Asymptotic Scaling**: Test critical paths across scales (\(N=10\) vs \(N=10{,}000\)) against deterministic, seeded signals.
- **Log Sanitization**: Redact secrets, Authorization tokens, and PII before writing to console or journals.
- **Direct Code**: Code explains what; comments explain why. Never commit change narration or dead code.
- **Error-Proof by Design (Poka-Yoke)**: Make invalid internal states unrepresentable via types, schemas, and constraints. Catch defects at compile/design time before runtime, while continuing to strictly validate untrusted external inputs at runtime boundaries. Fail fast with clear, actionable messages.
- **Evidence Before Claims**: Run the verification command and cite its output before asserting completion. "Should work" and "looks correct" are not evidence; only fresh command output is.
- **Proactive Circuit Breaking**: Track rate-limit windows, token quotas, and service health before calling downstream services. Route around exhausted or degraded dependencies instead of burning retry cycles.
- **Content-Addressed Invalidation**: Hash upstream inputs and configs; when hashes diverge, auto-invalidate stale downstream artifacts while unconditionally preserving user-created files and production outputs.

---

## 🚀 Next-Gen Capabilities (v3.0 - Cumulative Evidence Inheritance)

AutoEvolve v3.0 integrates the breakthrough principles of **PRAXIST** (*"From Experimental Artifacts to Solution Lineages"*, arXiv:2608.25955), moving beyond simple winner-takes-all keep/revert loops into a cumulative, evidence-inheriting system:

| Dimension | Legacy AI Assistants | AutoEvolve (v1/v2) | AutoEvolve v3.0 (PRAXIST Core) |
|---|---|---|---|
| **Pre-Edit Governance** | Edit blindly without plan | "Smallest diff" heuristic | **Deep Innovation Gate (DIG)**: Pre-registered hypothesis, surface, intent, and anti-goals |
| **Failed Experiments** | Repeatedly tried / forgotten | Reverted & discarded | **First-Class Failure Retention**: Extracted as active constraints into `CONSTRAINTS.md` |
| **Evaluation Depth** | Single unstructured run | Binary command test | **Multi-Stage Evidence Ladder**: `smoke` (<1s) $\to$ `scout` (<5s) $\to$ `complete` (<30s) |
| **Multi-Branching** | Random greedy edits | Heuristic `evolve/<niche>` | **Quantified Diversity (QD)**: Coordinate caps across $(family, surface, intent)$ |
| **Memory / Context** | Prompt bloat / context limit | Hard stop at 10 loops | **Gems Memory Compression**: Periodic bounded distillation into `.autoevolve/gems.md` (50+ loops) |
| **Adversarial Rigor** | Agent self-approval | Single pass metric | **Adversarial Skeptic Audit**: Red-teams for assertion weakening, mock relaxing, silent regressions |
| **Deliverable** | Modified files only | Git commit + 1-line log | **Solution Lineage DAG**: Complete provenance graph (`LINEAGE.md`) proving why solution won |

---

## 🧭 The Generational Evidence Loop

```
       ┌───────────────────────────────┐
       │   Human defines DIRECTION.md  │
       │   (Goal, Staged Signal, Budget)│
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │ 0. Inspect CONSTRAINTS.md &   │
       │    Gems for Active Boundaries │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │ 3. Deep Innovation Gate (DIG) │
       │    (Pre-Register Contract)    │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │ 4. Staged Verification Ladder │
       │    Smoke -> Scout -> Complete │
       └──────────────┬────────────────┘
                      │
            Improved? ├─────────────────────────┐
           (YES)      │                         │ (NO)
                      ▼                         ▼
         ┌─────────────────────────┐ ┌─────────────────────────┐
         │ 5. Keep & Advance       │ │ 5. Extract Negative/    │
         │    Confirmed Frontier   │ │    Diagnostic Constraint │
         └────────────┬────────────┘ └───────────┬─────────────┘
                      │                         │
                      │                         ▼
                      │              ┌─────────────────────────┐
                      │              │ Update CONSTRAINTS.md   │
                      │              └───────────┬─────────────┘
                      │                         │
                      └────────────┬────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────────────┐
         │ 6. Append Typed Finding to JOURNAL.md               │
         │    (Commit, Signal, Stage, Intent, Decision, Why)   │
         └─────────────────────────┬───────────────────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────────────┐
         │ 7. Gems Memory Compression & Lineage DAG Generation │
         │    (Every 5 loops, distill into .autoevolve/gems.md)│
         └─────────────────────────┬───────────────────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────────────┐
         │ 8. Repeat (Safe up to 50 loops with active Gems)    │
         └─────────────────────────────────────────────────────┘
```

---

## ⚙️ 1-Click Drop-In Matrix (12 Platforms)

| Tool / IDE | Adapter File | Target Rules Location | Auto-Detection Trigger |
|:---|:---|:---|:---|
| **Claude Code / AGENTS.md** | [`AGENTS.md`](./AGENTS.md) | `AGENTS.md` (or `CLAUDE.md`) | Default fallback |
| **Cursor IDE** | [`adapters/cursor.mdc`](./adapters/cursor.mdc) | `.cursor/rules/autoevolve.mdc` | `.cursor/` or `.cursorrules` |
| **Windsurf (Cascade)** | [`adapters/windsurf.md`](./adapters/windsurf.md) | `.windsurfrules` | `.windsurfrules` or `.windsurf/` |
| **GitHub Copilot** | [`adapters/copilot-instructions.md`](./adapters/copilot-instructions.md) | `.github/copilot-instructions.md` | `.github/` |
| **Cline & Roo Code** | [`adapters/cline.md`](./adapters/cline.md) | `.clinerules` | `.clinerules` |
| **Aider CLI** | [`adapters/aider.md`](./adapters/aider.md) | `CONVENTIONS.md` | `.aider*` config |
| **Continue.dev** | [`adapters/continue.md`](./adapters/continue.md) | `.continue/prompts/autoevolve.prompt` | `.continue/` |
| **Google Gemini & Antigravity** | [`adapters/gemini.md`](./adapters/gemini.md) | `GEMINI.md` | `.gemini/` |
| **Zed AI Assistant** | [`adapters/zed.md`](./adapters/zed.md) | `.zed/rules.md` | `.zed/` |
| **JetBrains AI / Junie** | [`adapters/jetbrains.md`](./adapters/jetbrains.md) | `.jetbrains/ai-instructions.md` | `.idea/` |
| **Sourcegraph Cody** | [`adapters/cody.md`](./adapters/cody.md) | `.cody/instructions.md` | `.cody/` |
| **OpenHands & SWE-Agent** | [`adapters/openhands.md`](./adapters/openhands.md) | `.openhands/instructions.md` | `.openhands/` |

---

## 🚦 GitHub Actions CI PR Guardrail

Block oversized AI PRs, test assertion weakening, and comment pollution in CI by adding `.github/workflows/ai-guardrails.yml`:

```yaml
name: AutoEvolve AI Guardrails
on: [pull_request]

permissions:
  contents: read

jobs:
  guardrails:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python .github/scripts/check_pr.py
```

---

## 💡 Why "Mindset-Only"? (Zero Dependencies)

Many AI frameworks try to build heavyweight CLI wrappers, daemon processes, or proprietary Python runtimes that intercept your tools. These tools frequently break cross-platform, get stale, conflict with existing virtual environments, and add unnecessary friction.

**AutoEvolve is pure prompt architecture.** By injecting exact evolutionary engineering rules natively into your assistant's system instructions, your agent acts like a disciplined senior engineer without requiring a single external package or dependency.

---

## 📄 License

[MIT](./LICENSE) © 2026 AutoEvolve
