# Install: add AutoEvolve to your repo

AutoEvolve is Markdown, not software. "Installing" it means putting the mindset where your
AI coding tool will read it. Pick whichever applies; you can use more than one.

## 1. The universal way: `AGENTS.md`
Copy [`../AGENTS.md`](../AGENTS.md) into your repository root. Most agentic coding tools
read a root `AGENTS.md` automatically. If yours doesn't, keep the file there anyway and add
a one-liner to your tool's own instructions: *"Follow the operating mindset in `AGENTS.md`."*

```bash
# from your repo root
curl -O https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/AGENTS.md
```

If your repo already has an `AGENTS.md`, append AutoEvolve's contents under a clear heading
rather than overwriting your existing instructions.

## 2. As tool-native rules
Copy the thin adapter for your tool from [`../adapters/`](../adapters/) to the path your
tool expects:

| Tool | Copy | To |
| --- | --- | --- |
| Cursor | `adapters/cursor.mdc` | `.cursor/rules/autoevolve.mdc` |
| Windsurf | `adapters/windsurf.md` | `.windsurf/rules/autoevolve.md` |
| GitHub Copilot | `adapters/copilot-instructions.md` | `.github/copilot-instructions.md` |

Each adapter is a short pointer to `AGENTS.md` plus the condensed core, so it's safe to
drop in even alongside your own rules. (On newer Windsurf, `.windsurf/rules/` still works
but `.devin/rules/` is the preferred location.)

## 3. As a loadable skill
If your agent supports a skills directory, copy
[`../skills/autoevolve/SKILL.md`](../skills/autoevolve/SKILL.md) into it (keeping the
`skills/autoevolve/SKILL.md` layout). The frontmatter tells the agent when to load it:
essentially, whenever it's about to change code in an existing repo.

## 4. As commands
The templates in [`../commands/`](../commands/) are concrete actions: `baseline`,
`evolve`, `simplify`, `review`, `journal`. Copy them into your tool's commands/prompts
directory, or just paste one into a chat when you want that specific step.

## Using it
Once it's in place, tell your assistant to work "the AutoEvolve way," or run `/baseline`
then `/evolve` on a task. Keep a `JOURNAL.md` (or local notes) as you go; the mindset
leans on that external memory. The one file to keep current is `AGENTS.md`; the adapters
just point at it.
