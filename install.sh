#!/bin/sh
# AutoEvolve 1-Line Zero-Dependency Installer (POSIX / macOS / Linux)
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/AkCodes23/AutoEvolve/lean/mindset-only/install.sh | sh
#   ./install.sh [TARGET_DIR] [--force]

set -e

REPO_URL="https://raw.githubusercontent.com/AkCodes23/AutoEvolve/lean/mindset-only"
TARGET_DIR="."
FORCE=0

for arg in "$@"; do
    case "$arg" in
        --force|-f)
            FORCE=1
            ;;
        *)
            TARGET_DIR="$arg"
            ;;
    esac
done

cd "$TARGET_DIR"

echo "=== AutoEvolve Installer ==="
echo "Target directory: $(pwd)"

fetch_or_copy() {
    file_rel="$1"
    dst="$2"

    if [ -f "$dst" ] && [ "$FORCE" -eq 0 ]; then
        echo "  [skip] $dst already exists (use --force to overwrite)"
        return
    fi

    mkdir -p "$(dirname "$dst")"

    if [ -f "$file_rel" ]; then
        cp "$file_rel" "$dst"
    else
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "$REPO_URL/$file_rel" -o "$dst"
        elif command -v wget >/dev/null 2>&1; then
            wget -qO "$dst" "$REPO_URL/$file_rel"
        else
            echo "  [error] curl or wget required to download $file_rel" >&2
            exit 1
        fi
    fi
    echo "  [+] Installed $dst"
}

# 1. Core Mindset & Conventions
fetch_or_copy "AGENTS.md" "AGENTS.md"
fetch_or_copy "DIRECTION.md" "DIRECTION.md"
fetch_or_copy "JOURNAL.md" "JOURNAL.md"

# 2. Detect IDEs and Install Matching Adapters
installed_adapter=0

if [ -d ".cursor" ] || [ -f ".cursorrules" ]; then
    fetch_or_copy "adapters/cursor.mdc" ".cursor/rules/autoevolve.mdc"
    installed_adapter=1
fi

if [ -f ".windsurfrules" ] || [ -d ".windsurf" ]; then
    fetch_or_copy "adapters/windsurf.md" ".windsurfrules"
    installed_adapter=1
fi

if [ -d ".github" ]; then
    fetch_or_copy "adapters/copilot-instructions.md" ".github/copilot-instructions.md"
    installed_adapter=1
fi

if [ -f ".clinerules" ]; then
    fetch_or_copy "adapters/cline.md" ".clinerules"
    installed_adapter=1
fi

if [ -d ".continue" ]; then
    fetch_or_copy "adapters/continue.md" ".continue/prompts/autoevolve.prompt"
    installed_adapter=1
fi

if [ -d ".zed" ]; then
    fetch_or_copy "adapters/zed.md" ".zed/rules.md"
    installed_adapter=1
fi

if [ -d ".idea" ] || [ -d ".jetbrains" ]; then
    fetch_or_copy "adapters/jetbrains.md" ".jetbrains/ai-instructions.md"
    installed_adapter=1
fi

if [ -d ".cody" ]; then
    fetch_or_copy "adapters/cody.md" ".cody/instructions.md"
    installed_adapter=1
fi

if [ -d ".openhands" ]; then
    fetch_or_copy "adapters/openhands.md" ".openhands/instructions.md"
    installed_adapter=1
fi

if [ -d ".gemini" ]; then
    fetch_or_copy "adapters/gemini.md" "GEMINI.md"
    installed_adapter=1
fi

if [ "$installed_adapter" -eq 0 ]; then
    # Default: install Claude/generic adapter as CLAUDE.md
    fetch_or_copy "adapters/claude.md" "CLAUDE.md"
fi

echo "----------------------------------------"
echo "✅ AutoEvolve mindset installed successfully."
echo "   Next steps:"
echo "   1. Set your goal and verification command in DIRECTION.md"
echo "   2. Prompt your AI coding agent to start evolving!"
