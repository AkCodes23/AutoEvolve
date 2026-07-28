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
Usage: ./install.sh [--target DIRECTORY] [--dry-run]

Run from a reviewed, immutable release checkout. There is one mindset profile: AGENTS.md.
Existing files are never overwritten.
If the target already has AGENTS.md, this command exits 2 after printing merge guidance.
EOF
}

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET_DIR=$(pwd)
DRY_RUN=0

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

[ -f "$SOURCE_DIR/AGENTS.md" ] || {
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

# A re-run, or a target where the mindset was already merged by hand, is a finished install and
# must not be reported as a failure. Anchor on the AutoEvolve-Core marker or the heading, at any
# depth so a file merged under a sub-heading still counts. Prose that merely mentions the name
# does not match.
CANONICAL_PRESENT=0
if [ -e "$TARGET_DIR/AGENTS.md" ] && (grep -qE 'AutoEvolve-Core' "$TARGET_DIR/AGENTS.md" 2>/dev/null || grep -qE '^#+[[:space:]]+AutoEvolve' "$TARGET_DIR/AGENTS.md" 2>/dev/null); then
  CANONICAL_PRESENT=1
fi

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
  # Tighten only while the half-written temp file exists, then restore. Setting `umask 077` and
  # never restoring it left every installed instruction file mode 0600 and every directory the
  # installer created mode 0700, regardless of the user's umask, while install.ps1 produced
  # ordinary readable files. These are documentation, not secrets, and the two installers must
  # not hand the same project different permissions.
  previous_umask=$(umask)
  umask 077
  cp "$source_file" "$temporary_file"
  umask "$previous_umask"
  chmod a+r "$temporary_file" 2>/dev/null || true
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
CANONICAL_SOURCE=AGENTS.md
install_file "$CANONICAL_SOURCE" AGENTS.md 1

[ -d "$TARGET_DIR/.claude" ] || [ -f "$TARGET_DIR/CLAUDE.md" ] && install_file adapters/claude.md CLAUDE.md || true
[ -d "$TARGET_DIR/.cursor" ] && install_file adapters/cursor.mdc .cursor/rules/autoevolve.mdc || true
[ -d "$TARGET_DIR/.windsurf" ] && install_file adapters/windsurf.md .windsurf/rules/autoevolve.md || true
[ -d "$TARGET_DIR/.github" ] && install_file adapters/copilot-instructions.md .github/copilot-instructions.md || true

if [ "$DRY_RUN" -eq 1 ]; then
  echo "Dry run complete. No files changed."
  exit 0
fi
if [ "$CANONICAL_SKIPPED" -eq 1 ] && [ "$CANONICAL_PRESENT" -eq 1 ]; then
  echo "AGENTS.md already carries AutoEvolve; left untouched."
  if [ "$WRITTEN" -eq 1 ]; then
    echo "Tool adapters listed above were added alongside it."
  fi
  echo "Already installed. Nothing to merge."
  exit 0
fi
if [ "$CANONICAL_SKIPPED" -eq 1 ]; then
  echo "Manual merge required: AGENTS.md already exists in the target and does not carry AutoEvolve." >&2
  echo "Review $SOURCE_DIR/$CANONICAL_SOURCE and merge it under a clear heading, then rerun --dry-run to inspect adapters." >&2
  if [ "$WRITTEN" -eq 1 ]; then
    # Say this plainly: the adapters above are live, so the mindset is already partly in effect
    # for those tools even though AGENTS.md was not touched.
    echo "Note: the tool adapters listed above WERE written and are already active for those tools." >&2
    echo "Only AGENTS.md still needs merging." >&2
  else
    echo "Nothing was written; AutoEvolve is not active in this target." >&2
  fi
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
