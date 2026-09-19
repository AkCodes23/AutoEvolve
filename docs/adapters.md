# Adapter compatibility

<!-- Generated from adapters/manifest.json; do not edit. -->

Documentation checked: 2026-09-19.

All integrations are **experimental** until a live product/version is tested.
The loader paths below follow documentation; fixture tests verify file placement,
not activation inside the products. Choose only the agents you use.
When multiple agents share AGENTS.md, only one copy is needed.

For each selected integration, test in a clean project and again with existing
user instructions. Verify both are loaded, ask the agent to identify the protocol
version and stopping limits, then run a small task with an independently checked
acceptance condition. Record product version, date, evidence, and precedence
before changing its status. Avoid loading duplicate copies into one host.

| ID | Product | Distribution source | Installed entrypoint | Format | Activation |
| --- | --- | --- | --- | --- | --- |
| `generic` | AGENTS.md-compatible assistants | [Source](../AGENTS.md) | `AGENTS.md` | Markdown | automatic |
| `claude` | Claude Code | [Source](../adapters/claude.md) | `CLAUDE.md` | Markdown | automatic |
| `cursor` | Cursor | [Source](../adapters/cursor.mdc) | `.cursor/rules/autoevolve.mdc` | MDC with YAML frontmatter | automatic |
| `copilot` | GitHub Copilot | [Source](../adapters/copilot-instructions.md) | `.github/instructions/autoevolve.instructions.md` | Markdown with YAML frontmatter | automatic |
| `cline` | Cline | [Source](../adapters/cline.md) | `.clinerules/autoevolve.md` | Markdown | automatic |
| `continue` | Continue | [Source](../adapters/continue.md) | `.continue/rules/autoevolve.md` | Markdown with YAML frontmatter | automatic |
| `windsurf` | Windsurf | [Source](../adapters/windsurf.md) | `.windsurf/rules/autoevolve.md` | Markdown with YAML frontmatter | automatic |
| `gemini` | Gemini CLI | [Source](../adapters/gemini.md) | `GEMINI.md` | Markdown | automatic |
| `aider` | Aider | [Source](../adapters/aider.md) | `CONVENTIONS.md` | Markdown | manual |
| `jetbrains` | JetBrains AI Assistant | [Source](../adapters/jetbrains.md) | `.aiassistant/rules/autoevolve.md` | Markdown | manual |
| `junie` | JetBrains Junie | [Source](../adapters/junie.md) | `AGENTS.md` | Markdown | automatic |
| `zed` | Zed | [Source](../adapters/zed.md) | `AGENTS.md` | Markdown | automatic |
| `openhands` | OpenHands | [Source](../adapters/openhands.md) | `AGENTS.md` | Markdown | automatic |
| `cody` | Sourcegraph Cody | [Source](../adapters/cody.md) | `AUTOEVOLVE.md` | Markdown | manual |

## AGENTS.md-compatible assistants (`generic`)

Status: **experimental**. Versions: Host-dependent; no live version certified.

Open the repository in an AGENTS.md-compatible host. Inspect its loaded instructions and confirm the AutoEvolve protocol version. Check host-specific precedence.

[Loader documentation](https://agents.md/)

## Claude Code (`claude`)

Status: **experimental**. Versions: Current documentation; no live version certified.

Start a new Claude Code session in the target repository. Use /memory to inspect project instructions and confirm CLAUDE.md includes AutoEvolve.

[Loader documentation](https://code.claude.com/docs/en/claude-md)

## Cursor (`cursor`)

Status: **experimental**. Versions: Project Rules documentation; no live version certified.

Open Cursor settings and verify the AutoEvolve project rule is enabled and always applied. Confirm it is included in a new agent conversation.

[Loader documentation](https://cursor.com/docs/rules)

## GitHub Copilot (`copilot`)

Status: **experimental**. Versions: Hosts supporting path-specific instructions; no live version certified.

Enable custom instructions in your Copilot host. Confirm this file appears in instruction references for a repository task. Older hosts may require a manual merge into .github/copilot-instructions.md.

[Loader documentation](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)

## Cline (`cline`)

Status: **experimental**. Versions: Directory rules documentation; no live version certified.

Enable AutoEvolve in Cline's rules panel and inspect the active rules. If .clinerules is a legacy file, migrate or merge it manually before installation; the installer will preserve it.

[Loader documentation](https://docs.cline.bot/features/cline-rules)

## Continue (`continue`)

Status: **experimental**. Versions: Rules documentation; no live version certified.

Open a new Continue conversation and inspect included rules. Confirm AutoEvolve is loaded as an always-applied rule.

[Loader documentation](https://docs.continue.dev/customize/deep-dives/rules)

## Windsurf (`windsurf`)

Status: **experimental**. Versions: Legacy Windsurf/Cascade workspace rules; no live version certified.

Inspect Cascade's workspace rules and confirm AutoEvolve is enabled as Always On. Check existing .windsurfrules for duplicates. Current documentation redirects to Devin Desktop, where .devin/rules takes precedence over the legacy .windsurf/rules fallback; verify which directory your version uses.

[Loader documentation](https://docs.windsurf.com/windsurf/cascade/memories)

## Gemini CLI (`gemini`)

Status: **experimental**. Versions: Gemini CLI context documentation; no live version certified.

Run /memory refresh and /memory show in Gemini CLI. Confirm project context includes AutoEvolve. This does not certify Antigravity.

[Loader documentation](https://geminicli.com/docs/cli/gemini-md/)

## Aider (`aider`)

Status: **experimental**. Versions: Conventions documentation; no live version certified.

Start with aider --read CONVENTIONS.md, or use /read CONVENTIONS.md in an existing session. Confirm it appears as a read-only context file.

[Loader documentation](https://aider.chat/docs/usage/conventions.html)

## JetBrains AI Assistant (`jetbrains`)

Status: **experimental**. Versions: Project Rules documentation; no live version certified.

In AI Assistant project rules, select AutoEvolve and configure the rule type as Always. Confirm it is attached to a new chat. Junie uses a separate entry.

[Loader documentation](https://www.jetbrains.com/help/ai-assistant/configure-project-rules.html)

## JetBrains Junie (`junie`)

Status: **experimental**. Versions: Guidelines documentation; no live version certified.

Start a new Junie task. Confirm repository AGENTS.md is used and check whether .junie/AGENTS.md or nested guidelines override it.

[Loader documentation](https://junie.jetbrains.com/docs/guidelines-and-memory.html)

## Zed (`zed`)

Status: **experimental**. Versions: Project instructions documentation; no live version certified.

Inspect a new Zed agent thread's project instructions. Zed chooses the first matching compatible file; check existing .rules, .cursorrules, and other legacy files for precedence.

[Loader documentation](https://zed.dev/docs/ai/instructions)

## OpenHands (`openhands`)

Status: **experimental**. Versions: Repository guidance documentation; no live version certified.

Start a repository task and confirm root AGENTS.md is loaded. This entry does not certify SWE-agent.

[Loader documentation](https://docs.openhands.dev/overview/skills)

## Sourcegraph Cody (`cody`)

Status: **experimental**. Versions: Manual context attachment only; no live version certified.

Explicitly attach AUTOEVOLVE.md as file context in the chat and confirm the attachment. No automatic Cody rules loader is claimed.

[Loader documentation](https://sourcegraph.com/docs/cody/capabilities/chat)
