#!/bin/sh
# AutoEvolve installer. Run this script from a downloaded, reviewed release checkout:
#
#   git clone --depth 1 --branch V0 https://github.com/AkCodes23/AutoEvolve.git
#   cd AutoEvolve && ./install.sh --target /path/to/your/repo
#
# It never executes a remote script, never overwrites an existing file, and reports every
# skipped file so users do not mistake a partial installation for a completed one.
set -eu

usage() {
  cat <<'EOF'
Usage: ./install.sh [--target DIRECTORY] [--profile core|full] [--dry-run]

Run from a reviewed, immutable release checkout. `core` is the default context-efficient
profile; use `full` only when you intentionally want the longer operating manual.
Existing files are never overwritten.
If the target already has AGENTS.md, this command exits 2 after printing merge guidance.
EOF
}

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET_DIR=$(pwd)
DRY_RUN=0
PROFILE=core

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      [ "$#" -ge 2 ] || { echo "--target needs a directory" >&2; exit 64; }
      TARGET_DIR=$2
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --profile)
      [ "$#" -ge 2 ] || { echo "--profile needs core or full" >&2; exit 64; }
      PROFILE=$2
      case "$PROFILE" in core|full) ;; *) echo "--profile must be core or full" >&2; exit 64;; esac
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

[ -f "$SOURCE_DIR/AGENTS.md" ] && [ -f "$SOURCE_DIR/adapters/_core.md" ] || {
  echo "Installer source is incomplete. Download a release checkout; do not pipe this script from a URL." >&2
  exit 65
}
[ -d "$TARGET_DIR" ] || {
  echo "Target directory does not exist: $TARGET_DIR" >&2
  exit 66
}
TARGET_DIR=$(CDPATH= cd -- "$TARGET_DIR" && pwd)

CANONICAL_SKIPPED=0
OTHER_SKIPPED=0
WRITTEN=0

install_file() {
  source_rel=$1
  destination=$2
  canonical=${3:-0}
  source_file=$SOURCE_DIR/$source_rel
  destination_file=$TARGET_DIR/$destination

  [ -f "$source_file" ] || {
    echo "Missing installer source: $source_rel" >&2
    exit 65
  }
  if [ -e "$destination_file" ]; then
    echo "  skip $destination (already exists; no overwrite)"
    if [ "$canonical" -eq 1 ]; then CANONICAL_SKIPPED=1; else OTHER_SKIPPED=1; fi
    return 0
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "  would write $destination"
    return 0
  fi

  destination_dir=$(dirname -- "$destination_file")
  mkdir -p "$destination_dir"
  temporary_file=$destination_dir/.autoevolve-install-$$.tmp
  umask 077
  cp "$source_file" "$temporary_file"
  # `ln` fails rather than replacing a file if another process created the target meanwhile.
  if ln "$temporary_file" "$destination_file" 2>/dev/null; then
    rm -f "$temporary_file"
    echo "  wrote $destination"
    WRITTEN=1
  else
    rm -f "$temporary_file"
    echo "  skip $destination (created concurrently; no overwrite)"
    if [ "$canonical" -eq 1 ]; then CANONICAL_SKIPPED=1; else OTHER_SKIPPED=1; fi
  fi
}

echo "AutoEvolve: source=$SOURCE_DIR target=$TARGET_DIR"
if [ "$PROFILE" = full ]; then
  CANONICAL_SOURCE=AGENTS.md
else
  CANONICAL_SOURCE=adapters/_core.md
fi
echo "AutoEvolve profile: $PROFILE"
install_file "$CANONICAL_SOURCE" AGENTS.md 1

[ -d "$TARGET_DIR/.claude" ] || [ -f "$TARGET_DIR/CLAUDE.md" ] && install_file adapters/claude.md CLAUDE.md || true
[ -d "$TARGET_DIR/.cursor" ] && install_file adapters/cursor.mdc .cursor/rules/autoevolve.mdc || true
[ -d "$TARGET_DIR/.windsurf" ] && install_file adapters/windsurf.md .windsurf/rules/autoevolve.md || true
[ -d "$TARGET_DIR/.github" ] && install_file adapters/copilot-instructions.md .github/copilot-instructions.md || true

if [ "$DRY_RUN" -eq 1 ]; then
  echo "Dry run complete. No files changed."
  exit 0
fi
if [ "$CANONICAL_SKIPPED" -eq 1 ]; then
  echo "Manual merge required: AGENTS.md already exists in the target. AutoEvolve was not activated automatically." >&2
  echo "Review $SOURCE_DIR/$CANONICAL_SOURCE and merge it under a clear heading, then rerun --dry-run to inspect adapters." >&2
  exit 2
fi
if [ "$OTHER_SKIPPED" -eq 1 ]; then
  echo "Installed canonical AGENTS.md, but one or more tool adapters were skipped. Review the messages above."
fi
if [ "$WRITTEN" -eq 1 ]; then
  echo "Installation complete. Review the added files before relying on them in an agent session."
else
  echo "No files were written."
fi
