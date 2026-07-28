# Install: add AutoEvolve to your repo

AutoEvolve is Markdown, not software. "Installing" it means putting the mindset where your
AI coding tool will read it. Pick whichever applies; you can use more than one.

## 0. Reviewed release installer (recommended)

Do not pipe a moving remote script into a shell. Download a specific release, review it, then
run the installer against the target repository:

```bash
git clone --depth 1 --branch V0 https://github.com/AkCodes23/AutoEvolve.git
cd AutoEvolve
./install.sh --target /path/to/your/repo --dry-run
./install.sh --target /path/to/your/repo
```

The installer defaults to the compact **core** profile in `AGENTS.md`; use
`--profile full` only when you deliberately want the longer operating manual. It also writes
tool adapters for detected config directories. It never overwrites existing files. If
`AGENTS.md` already exists, it exits with manual merge guidance rather than claiming
installation completed. Use the release tag shown on the project's releases page instead of a
moving branch; this checkout's published tag is `V0`.

The manual options below are appropriate when you need to merge with an existing rules file.

## Claude Code: install as a plugin (recommended for Claude Code)
Claude Code can install AutoEvolve as a proper plugin, no file copying. The repo is its own
plugin marketplace, so from inside Claude Code:

```
/plugin marketplace add AkCodes23/AutoEvolve
/plugin install autoevolve@autoevolve
```

That registers the skill (as `/autoevolve:autoevolve`) and the commands (`/autoevolve:baseline`,
`/autoevolve:evolve`, and so on). Run `/plugin` for the interactive UI, or `/reload-plugins`
to pick it up without restarting. Pin the plugin to an immutable release tag when your tool
supports that capability.
If you would rather not use the plugin system, the `CLAUDE.md` adapter in option 2 still works.

## 1. The universal way: `AGENTS.md`
Copy the compact core into your repository root. Many agentic coding tools read a root
`AGENTS.md` automatically, including **Codex** and **Antigravity** (Antigravity reads it
natively as of v1.20.3), so for those tools this single file is the whole install. If your
tool doesn't read `AGENTS.md`, keep the file there anyway and add a one-liner to your tool's
own instructions: *"Follow the operating mindset in `AGENTS.md`."*

```bash
# from your repo root, after reviewing a release checkout
cp /path/to/AutoEvolve/AGENTS.md ./AGENTS.md
```

Use `AGENTS.md` from the release checkout instead only when you deliberately want the full
manual on every agent turn. If your repo already has an `AGENTS.md`, append the selected
profile under a clear heading rather than overwriting your existing instructions.

## 2. As tool-native rules
Some tools read their own instruction file rather than `AGENTS.md`. Copy the thin adapter
for your tool from [`../adapters/`](../adapters/) to the path it expects:

| Tool | Copy | To |
| --- | --- | --- |
| Claude Code | `adapters/claude.md` | `CLAUDE.md` (repo root) |
| Cursor | `adapters/cursor.mdc` | `.cursor/rules/autoevolve.mdc` |
| Windsurf | `adapters/windsurf.md` | `.windsurf/rules/autoevolve.md` |
| GitHub Copilot | `adapters/copilot-instructions.md` | `.github/copilot-instructions.md` |

Each adapter carries the condensed core and points back at `AGENTS.md`, so it's safe to
drop in even alongside your own rules. Notes:

- **Claude Code** does not read `AGENTS.md`, which is why it gets its own `CLAUDE.md`. If
  you also keep `AGENTS.md`, you can instead make `CLAUDE.md` a single line, `@AGENTS.md`,
  to import it and avoid a second copy.
- **Codex** and **Antigravity** read root `AGENTS.md` natively, so they need no file here
  (see option 1).
- On newer Windsurf, `.windsurf/rules/` still works but `.devin/rules/` is preferred.

## 3. As a loadable skill
If your agent supports a skills directory, copy
[`../skills/autoevolve/SKILL.md`](../skills/autoevolve/SKILL.md) into it (keeping the
`skills/autoevolve/SKILL.md` layout; for Claude Code that path is
`.claude/skills/autoevolve/SKILL.md`). The frontmatter tells the agent when to load it:
essentially, whenever it's about to change code in an existing repo.

## 4. As commands
The templates in [`../commands/`](../commands/) are concrete actions: `baseline`,
`evolve`, `simplify`, `review`, `journal`. Copy them into your tool's commands/prompts
directory, or just paste one into a chat when you want that specific step.

## Using it
Once it's in place, tell your assistant to work "the AutoEvolve way," or run `/baseline`
then `/evolve` on a task. Keep a `JOURNAL.md` (or local notes) as you go; the mindset
leans on that external memory. Copy-paste starters for `DIRECTION.md` and `JOURNAL.md` are
in [`../templates/`](../templates/). The one file to keep current is `AGENTS.md`; the
adapters just point at it.

To confirm the mindset loaded, ask your agent "what is your operating loop?" It should
describe the understand, signal, baseline, smallest-change, verify, keep-or-revert cycle.

## Which surfaces are verified

Installation success and behaviour success are different checks. Every row below has a tested
install path, meaning the file lands where the tool expects it. **"The tool then actually applied
the instructions" has not been measured on any specific version.** Copying a file is not the same
as the tool obeying it, so validate before claiming compatibility: ask the assistant to state the
operating loop, then give it a disposable task and watch whether it defines a signal and reverts
a failed attempt.

| Integration | Install surface | Status | How to validate behavior |
| --- | --- | --- | --- |
| Root-instruction tools | `AGENTS.md` | Install surface verified; behavior unverified | Ask for the operating loop, then run a disposable eval task. |
| Claude Code plugin | `.claude-plugin/`, `skills/`, `commands/` | Install surface verified; behavior unverified | Confirm the skill and each command appear, then complete a disposable eval task. |
| Claude Code rules | `CLAUDE.md` | Install surface verified; behavior unverified | Confirm the file loads without replacing existing project rules. |
| Cursor | `.cursor/rules/autoevolve.mdc` | Install surface verified; behavior unverified | Confirm the rule is always applied and run a disposable eval task. |
| Windsurf | `.windsurf/rules/autoevolve.md` | Install surface verified; behavior unverified | Confirm the rule path for the installed version and run a disposable eval task. |
| GitHub Copilot | `.github/copilot-instructions.md` | Install surface verified; behavior unverified | Confirm repository instructions are read in the target experience. |

When a tool's behaviour is actually tested, replace its Status with the tool version and the date.
