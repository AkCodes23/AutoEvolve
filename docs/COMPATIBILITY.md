# Compatibility and adoption

AutoEvolve is an instruction artifact, so installation success and behavior success are
different checks. Validate each supported tool/version before claiming compatibility.

| Integration | Install surface | Validation |
| --- | --- | --- |
| Root-instruction tools | `AGENTS.md` | Ask for the operating loop, then run a disposable eval task. |
| Claude Code plugin | `.claude-plugin/`, `skills/`, `commands/` | Confirm the skill and each command appear, then complete a disposable eval task. |
| Claude Code rules | `CLAUDE.md` | Confirm the file loads without replacing existing project rules. |
| Cursor | `.cursor/rules/autoevolve.mdc` | Confirm the rule is always applied and run a disposable eval task. |
| Windsurf | `.windsurf/rules/autoevolve.md` | Confirm the rule path for the installed version and run a disposable eval task. |
| GitHub Copilot | `.github/copilot-instructions.md` | Confirm repository instructions are read in the target experience. |

For every release, record tool name, exact version, operating system, install method,
instruction discovery result, and one functional benchmark result. Unsupported or unverified
tools should be described as manual `AGENTS.md` installations, not as native integrations.

## Recommended operating modes

- **Quick:** a small, low-risk fix with one verification step.
- **Default:** normal product work, with a defined signal and journaled result.
- **Deep:** experiments or load-bearing work, in a dedicated worktree with an explicit
  budget and a human-owned direction file.

Do not use autonomous iteration for incident response, production data repair, security
remediation, spending actions, or a task whose objective and guardrails remain ambiguous.
