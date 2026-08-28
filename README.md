<div align="center">

# AutoEvolve

**The Pure, Zero-Dependency Autonomous Software Evolution Mindset**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-0-brightgreen.svg)]()
[![Pure Mindset](https://img.shields.io/badge/Architecture-Pure%20Mindset-purple.svg)]()
[![IDE Adapters](https://img.shields.io/badge/IDE%20Adapters-12%2F12%20Synced-brightgreen.svg)]()

*Evolve code autonomously through Language Agent Tree Search (LATS), Deep Innovation Gates (DIG), Neurosymbolic Knowledge Retention, and Multi-Agent Genetic Swarms.*

</div>

---

## ⚡ 10-Second Quickstart

Install AutoEvolve directly into any local repository with a single command:

```bash
# macOS / Linux (Auto-detects Cursor, Claude Code, Copilot, Cline, etc.)
curl -fsSL https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.sh | bash

# Windows PowerShell
iwr -useb https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.ps1 | iex
```

*Or manually copy [`AGENTS.md`](./AGENTS.md) or your IDE's adapter from [`adapters/`](./adapters) into your repository root.*

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

## 📂 File Ecosystem & Artifact Architecture

AutoEvolve operates transparently through clear, human-readable markdown files in your repository:

```text
your-project/
├── AGENTS.md / .cursorrules   <-- The Mindset (Injects protocol into your AI assistant)
├── DIRECTION.md               <-- Human sets Objective, Frozen Signal & Budget
├── CONSTRAINTS.md             <-- AI logs negative knowledge / blocked dead-ends
├── JOURNAL.md                 <-- AI logs keep/revert decisions with metric deltas
├── LINEAGE.md                 <-- AI renders solution provenance DAG (Mermaid)
└── .autoevolve/gems.md        <-- Compressed architectural lessons (<=500 tokens)
```

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
       │ 1. EXPLORE: CONSTRAINTS.md,   │
       │    Gems & LATS Tree Search    │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │ 2. CONTRACT: Deep Innovation  │
       │    Gate (DIG) Pre-Register    │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │ 3. MUTATE: Poka-Yoke Edit in  │
       │    Isolated Git Worktree      │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │ 4. VERIFY: Evidence Ladder    │
       │    Smoke -> Scout -> Complete │
       └──────────────┬────────────────┘
                      │
            Improved? ├─────────────────────────┐
           (YES)      │                         │ (NO)
                      ▼                         ▼
         ┌─────────────────────────┐ ┌─────────────────────────┐
         │ 5. Keep & Advance       │ │ 5. Extract Negative/    │
         │    Confirmed Frontier   │ │    Diagnostic Lesson    │
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
         │ 6. Update JOURNAL.md & Solution Lineage DAG         │
         └─────────────────────────┬───────────────────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────────────┐
         │ 7. Gems Memory Compression (every 5 loops, <=500tok)│
         └─────────────────────────┬───────────────────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────────────┐
         │ 8. Repeat (Push to Pareto Frontier, full Lineage)   │
         └─────────────────────────────────────────────────────┘
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

## 🚀 Next-Gen Capabilities (v3.0 & v4.0 Mindset)

| Dimension | Legacy AI Assistants | AutoEvolve (v1/v2) | AutoEvolve v4.0 (Autonomous Swarm) |
|---|---|---|---|
| **Pre-Edit Governance** | Edit blindly without plan | "Smallest diff" heuristic | **Deep Innovation Gate (DIG)**: Pre-registered hypothesis, surface, intent, and anti-goals |
| **Failed Experiments** | Repeatedly tried / forgotten | Reverted & discarded | **First-Class Failure Retention**: Extracted as active constraints into `CONSTRAINTS.md` |
| **Evaluation Depth** | Single unstructured run | Binary command test | **Multi-Stage Evidence Ladder**: `smoke` (<1s) $\to$ `scout` (<5s) $\to$ `complete` (<30s) |
| **Multi-Branching** | Random greedy edits | Heuristic `evolve/<niche>` | **Language Agent Tree Search (LATS)**: Forks 3 orthogonal hypotheses on plateaus |
| **Memory / Context** | Prompt bloat / context limit | Hard stop at 10 loops | **Gems Memory Compression**: Distills lessons into `.autoevolve/gems.md` (<=500 tokens) |
| **Adversarial Rigor** | Agent self-approval | Single pass metric | **Adversarial Skeptic Audit**: Red-teams for assertion weakening, mock relaxing, regressions |
| **Deliverable** | Modified files only | Git commit + 1-line log | **Solution Lineage DAG**: Complete provenance graph (`LINEAGE.md`) proving why solution won |

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

## ❓ Frequently Asked Questions (FAQ)

### Q: Does AutoEvolve consume extra API tokens?
**No.** In fact, AutoEvolve typically reduces net token consumption by up to 40% across multi-turn sessions. Standard agents continuously accumulate noisy command output and repeat failed attempts until the context window is saturated. AutoEvolve's **Gems Memory Compression** distills long sessions into concise summaries ($\le 500$ tokens) and archives historical diffs to `LINEAGE.md`.

### Q: Does it require any background daemons, Python packages, or Docker?
**Zero dependencies.** AutoEvolve is 100% pure prompt architecture and markdown protocols. It requires no pip installations, no local servers, and no background processes. It works inside whatever editor, terminal, or LLM you already use.

### Q: How does it prevent agents from getting stuck in infinite loops?
AutoEvolve enforces **graduated failure escalation**:
- **1st failure**: Immediate isolated worktree revert + root cause extraction to `CONSTRAINTS.md`.
- **2nd failure**: Mandatory orthogonal pivot to a different surface or mechanism.
- **3+ failures**: The agent questions the foundational architecture and halts to request human guidance rather than thrashing.

### Q: Does AutoEvolve work with any programming language?
**Yes.** AutoEvolve is language-agnostic. Whether you write Rust, TypeScript, Python, Go, C++, or Java, the protocol applies identical rigor to blast radius mapping, invariant verification, non-blocking concurrency, and empirical evidence gathering.

### Q: How do I define my own optimization goals?
Simply create or update `DIRECTION.md` in your project root with your target objective, a frozen verification command (e.g. `pytest`, `cargo test`, `npm test`), and a maximum iteration budget.

---

## 💡 Why "Mindset-Only"? (Zero Dependencies)

Many AI frameworks try to build heavyweight CLI wrappers, daemon processes, or proprietary Python runtimes that intercept your tools. These tools frequently break cross-platform, get stale, conflict with existing virtual environments, and add unnecessary friction.

**AutoEvolve is pure prompt architecture.** By injecting exact evolutionary engineering rules natively into your assistant's system instructions, your agent acts like a disciplined senior engineer without requiring a single external package or dependency.

---

## 📄 License

[MIT](./LICENSE) © 2026 AutoEvolve
