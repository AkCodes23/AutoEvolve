# Compatibility and adoption

> Status: install surfaces verified, tool behavior not yet verified. Every row below has a
> real, tested install path (the file lands where the tool expects it), but "the tool then
> actually applied the instructions" has not been measured on any specific version. Treat the
> Status column as the source of truth: copying a file is not the same as the tool obeying it.

AutoEvolve is an instruction artifact, so installation success and behavior success are
different checks. Validate each supported tool/version before claiming compatibility.

| Integration | Install surface | Status | How to validate behavior |
| --- | --- | --- | --- |
| Root-instruction tools | `AGENTS.md` | Install surface verified; behavior unverified | Ask for the operating loop, then run a disposable eval task. |
| Claude Code plugin | `.claude-plugin/`, `skills/`, `commands/` | Install surface verified; behavior unverified | Confirm the skill and each command appear, then complete a disposable eval task. |
| Claude Code rules | `CLAUDE.md` | Install surface verified; behavior unverified | Confirm the file loads without replacing existing project rules. |
| Cursor | `.cursor/rules/autoevolve.mdc` | Install surface verified; behavior unverified | Confirm the rule is always applied and run a disposable eval task. |
| Windsurf | `.windsurf/rules/autoevolve.md` | Install surface verified; behavior unverified | Confirm the rule path for the installed version and run a disposable eval task. |
| GitHub Copilot | `.github/copilot-instructions.md` | Install surface verified; behavior unverified | Confirm repository instructions are read in the target experience. |

When a tool's behavior is actually tested, replace its Status with the tool version, operating
system, and date it was verified. For every release, record tool name, exact version, operating
system, install method, instruction discovery result, and one functional benchmark result.
Unsupported or unverified tools should be described as manual `AGENTS.md` installations, not as
native integrations.

## Recommended operating modes

- **Quick:** a small, low-risk fix with one verification step.
- **Default:** normal product work, with a defined signal and journaled result.
- **Deep:** experiments or load-bearing work, in a dedicated worktree with an explicit
  budget and a human-owned direction file.

Do not use autonomous iteration for incident response, production data repair, security
remediation, spending actions, or a task whose objective and guardrails remain ambiguous.
