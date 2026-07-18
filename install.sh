#!/bin/sh
# AutoEvolve installer. Run from the root of the repo you want to add the mindset to:
#
#   curl -fsSL https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.sh | sh
#
# It writes AGENTS.md (read natively by Codex, Antigravity, and many other tools) and, for
# every tool config directory it detects, that tool's adapter. It never overwrites a file
# you already have. Pin a released version with AUTOEVOLVE_REF=v0.1.0.
set -eu

REF="${AUTOEVOLVE_REF:-main}"
BASE="https://raw.githubusercontent.com/AkCodes23/AutoEvolve/${REF}"

fetch() {
  # fetch <source-path> <dest-path>
  if [ -e "$2" ]; then
    echo "  skip $2 (already exists)"
    return 0
  fi
  mkdir -p "$(dirname "$2")"
  curl -fsSL "${BASE}/$1" -o "$2"
  echo "  wrote $2"
}

echo "AutoEvolve: installing from ${REF}"

# Universal source of truth. Codex and Antigravity read this natively.
fetch AGENTS.md AGENTS.md

# Tool-specific adapters, only where the tool's config is present.
[ -d .claude ] || [ -f CLAUDE.md ] && fetch adapters/claude.md CLAUDE.md || true
[ -d .cursor ] && fetch adapters/cursor.mdc .cursor/rules/autoevolve.mdc || true
[ -d .windsurf ] && fetch adapters/windsurf.md .windsurf/rules/autoevolve.md || true
[ -d .github ] && fetch adapters/copilot-instructions.md .github/copilot-instructions.md || true

echo "Done. AGENTS.md is your source of truth."
echo "Tell your agent to work the AutoEvolve way, or run /baseline then /evolve on a task."
echo "Docs: https://github.com/AkCodes23/AutoEvolve"
