# AutoEvolve

> **Evolve the code, don't just write it: small steps, each verified.**

AutoEvolve is a minimal, zero-dependency, prompt-first engineering mindset for AI coding assistants (Claude Code, Cursor, Windsurf, Copilot, Cline, Aider, Continue, Gemini, Zed, JetBrains, Cody, and OpenHands).

It synthesizes the core principles of **DeepMind AlphaEvolve** (grounded verification), **Karpathy's autoresearch** (keep-or-revert hypothesis loop), and **Dietrich Gebert's Ponytail** (YAGNI minimalism ladder) into a single dense, drop-in ruleset.

---

## ⚡ 1-Line Quick Install

Install the mindset and matching editor rules in any repository in 1 second:

* **macOS / Linux / POSIX**:
  ```bash
  curl -fsSL https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.sh | sh
  ```

* **Windows (PowerShell)**:
  ```powershell
  irm https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.ps1 | iex
  ```

---

## 🎯 The Problem AutoEvolve Solves

Without explicit evolutionary guardrails, AI coding agents default to common failure patterns:

| Without AutoEvolve (Default AI Behavior) | With AutoEvolve Mindset |
|:---|:---|
| ❌ Modifies test assertions or weakens thresholds to fake a passing score | ✅ **Frozen Signal**: Optimizes the objective, never the scorer |
| ❌ Changes shared function signatures, breaking downstream callers | ✅ **Blast-Radius Awareness**: Audits all repository callers before editing shared contracts |
| ❌ Dumps 10,000 lines of unformatted test stdout, burning 60k+ tokens | ✅ **Context Frugality**: Executes in quiet mode (`pytest -q`), preserving >98% of context window |
| ❌ Pollutes Git history with change narration comments (`# Fix: updated loop`) | ✅ **Direct Code**: Rejects narration; comments only uncodeable rationale and caveats |
| ❌ Trapped in local minima, micro-tweaking the same failing regex for 5 turns | ✅ **Orthogonal Pivoting**: If 2 loops fail, forces a fundamental strategy pivot |
| ❌ Introduces path traversals, `shell=True` injection, or leaked secrets | ✅ **Enterprise Invariants**: Enforces array subprocesses, path bounds, and log sanitization |

---

## 🔄 The 9-Step Evolutionary Loop

```text
0. Understand scope and reproduce
1. Freeze the signal (define the test/metric before editing; never edit the scorer)
2. Baseline HEAD
3. Smallest diff (change only what the task needs)
4. Verify cheapest first (compiles -> correct -> speed and memory)
5. Keep if better, simpler, or a deletion; if 2 consecutive loops fail, pivot orthogonally;
   else restore only changes introduced relative to pre-loop snapshot (preserve user dirty tree)
6. Journal one line with measured metric delta
7. Simplify relentlessly
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
5. Installed dependency    --> Already in package.json/pyproject.toml? Use it.
6. One line                --> Can it be expressed in one clean line? One line.
7. Minimum code            --> Only then, write the minimal working implementation.
```

---

## 🛡️ Core Guardrails

- **Surgical Scope**: Change only what the task needs. Leave adjacent formatting, comments, and structure intact.
- **Contract-Aware**: Know all callers before modifying a shared signature; fix the shared contract, not just the one reporting call site.
- **Trust Boundaries**: Validate external inputs without silent coercion. Categorize errors (client vs server vs dependency), time out all I/O, and keep locks non-blocking across network calls.
- **Subprocess Safety**: Pass array arguments (`subprocess.run(['cmd', 'arg'])`), never concatenated strings with `shell=True`. Keep commands cross-platform.
- **Idempotency**: Ensure retried database writes, event handlers, and webhooks are safe to run multiple times.
- **Asymptotic Scaling**: Test critical paths across scales (\(N=10\) vs \(N=10{,}000\)) against deterministic, seeded signals.
- **Log Sanitization**: Redact secrets, Authorization tokens, and PII before writing to console or journals.
- **Direct Code**: Code explains what; comments explain why. Never commit change narration or dead code.
- **Tree Safety**: Never bulk-discard a dirty tree. Revert only specific paths and untracked files created during the task.

---

## ⚙️ 1-Click Drop-In Matrix (12 Platforms)

AutoEvolve automatically detects your active IDE and writes the appropriate native rules file:

| Tool / IDE | Adapter File | Target Location | Installer Mode |
|:---|:---|:---|:---|
| **Claude Code / AGENTS.md** | [`AGENTS.md`](./AGENTS.md) | `AGENTS.md` (or `CLAUDE.md`) | Default fallback |
| **Cursor IDE** | [`adapters/cursor.mdc`](./adapters/cursor.mdc) | `.cursor/rules/autoevolve.mdc` | Auto-detected (`.cursor`) |
| **Windsurf (Cascade)** | [`adapters/windsurf.md`](./adapters/windsurf.md) | `.windsurfrules` | Auto-detected (`.windsurfrules`) |
| **GitHub Copilot** | [`adapters/copilot-instructions.md`](./adapters/copilot-instructions.md) | `.github/copilot-instructions.md` | Auto-detected (`.github`) |
| **Cline & Roo Code** | [`adapters/cline.md`](./adapters/cline.md) | `.clinerules` | Auto-detected (`.clinerules`) |
| **Aider CLI** | [`adapters/aider.md`](./adapters/aider.md) | `CONVENTIONS.md` | Auto-detected (`.aider*`) |
| **Continue.dev** | [`adapters/continue.md`](./adapters/continue.md) | `.continue/prompts/autoevolve.prompt` | Auto-detected (`.continue`) |
| **Google Gemini & Antigravity** | [`adapters/gemini.md`](./adapters/gemini.md) | `GEMINI.md` | Auto-detected (`.gemini`) |
| **Zed AI Assistant** | [`adapters/zed.md`](./adapters/zed.md) | `.zed/rules.md` | Auto-detected (`.zed`) |
| **JetBrains AI / Junie** | [`adapters/jetbrains.md`](./adapters/jetbrains.md) | `.jetbrains/ai-instructions.md` | Auto-detected (`.idea`) |
| **Sourcegraph Cody** | [`adapters/cody.md`](./adapters/cody.md) | `.cody/instructions.md` | Auto-detected (`.cody`) |
| **OpenHands & SWE-Agent** | [`adapters/openhands.md`](./adapters/openhands.md) | `.openhands/instructions.md` | Auto-detected (`.openhands`) |

---

## 🚦 GitHub Actions PR Guardrail

Protect your codebase against oversized AI diffs, test assertion weakening, and comment pollution in CI by adding `.github/workflows/ai-guardrails.yml`:

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

## 📁 Repository Conventions

- **[`DIRECTION.md`](./DIRECTION.md)** (Human-Owned): Specifies the objective, the frozen evaluation signal, active guardrails, and the iteration budget.
- **[`JOURNAL.md`](./JOURNAL.md)** (Append-Only): One-line log of each experiment: commit hash, measured signal delta, keep/revert decision, and rationale.

---

## 📄 License

[MIT](./LICENSE)
