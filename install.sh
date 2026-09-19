#!/bin/sh
set -eu

TARGET_DIR=.
AGENTS=generic,claude
FORCE=0
REF=${AUTOEVOLVE_REF:-}
SOURCE_DIR=
if [ -z "$REF" ] && [ -f "$0" ]; then
    candidate=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
    if [ -f "$candidate/adapters/manifest.txt" ]; then SOURCE_DIR=$candidate; fi
fi

usage() {
    echo "Usage: sh install.sh [TARGET_DIR] [--agents generic,claude,...] [--force] [--ref COMMIT]"
    echo "Default agents: generic,claude. Use --list-agents for available integrations."
    echo "--force upgrades only unchanged files recorded by a previous install."
    echo "Existing goals, journals, constraints, and edited instructions are always preserved."
}
die() { echo "[error] $*" >&2; exit 1; }
LIST=0
target_set=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --help|-h) usage; exit 0 ;;
        --force|-f) FORCE=1; shift ;;
        --list-agents) LIST=1; shift ;;
        --agents|--ref)
            [ "$#" -ge 2 ] || { usage >&2; exit 1; }
            case "$1" in
                --agents) AGENTS=$2 ;;
                --ref) REF=$2; SOURCE_DIR= ;;
            esac
            shift 2 ;;
        -*) die "Unknown option: $1" ;;
        *)
            [ "$target_set" -eq 0 ] || die "Only one target is allowed."
            TARGET_DIR=$1; target_set=1; shift ;;
    esac
done

valid_path() {
    case "$1" in ""|/*|*\\*|*[!a-zA-Z0-9_./-]*) return 1 ;; esac
    case "/$1/" in */../*|*/./*|*//* ) return 1 ;; esac
}
hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}
download() {
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL --connect-timeout 10 --max-time 60 -H "Accept: ${3:-text/plain}" "$1" -o "$2"
    elif command -v wget >/dev/null 2>&1; then
        wget -q --timeout=30 --tries=1 --header="Accept: ${3:-text/plain}" -O "$2" "$1"
    else
        die "curl or wget is required for remote installation."
    fi
}
safe_target() {
    remaining=$1
    current=$TARGET_DIR
    while [ -n "$remaining" ]; do
        part=${remaining%%/*}
        current=$current/$part
        [ ! -L "$current" ] || die "Refusing symbolic link: $current"
        if [ "$remaining" = "$part" ]; then break; fi
        remaining=${remaining#*/}
    done
}

command -v sha256sum >/dev/null 2>&1 || command -v shasum >/dev/null 2>&1 ||
    die "sha256sum or shasum is required to verify distribution files."
[ -d "$TARGET_DIR" ] || die "Target directory does not exist: $TARGET_DIR"
TARGET_DIR=$(CDPATH='' cd -- "$TARGET_DIR" && pwd)
safe_target .autoevolve
mkdir -p "$TARGET_DIR/.autoevolve"
LOCK=$TARGET_DIR/.autoevolve/install.lock
mkdir "$LOCK" 2>/dev/null || die "Another install is active, or a stale lock exists: $LOCK"
STAGE=
TEMPORARY=
cleanup() {
    if [ -n "$TEMPORARY" ]; then rm -f "$TEMPORARY"; fi
    if [ -n "$STAGE" ]; then rm -rf "$STAGE"; fi
    rmdir "$LOCK"
}
trap cleanup 0
trap 'exit 130' INT
trap 'exit 143' TERM HUP
STAGE=$(mktemp -d "$TARGET_DIR/.autoevolve/staging.XXXXXX")
if [ -z "$SOURCE_DIR" ]; then
    if [ -z "$REF" ]; then
        if ! download "https://api.github.com/repos/AkCodes23/AutoEvolve/commits/main" "$STAGE/ref" application/vnd.github.sha; then
            die "Could not resolve main. Retry with --ref FULL_COMMIT_SHA or install from a local checkout."
        fi
        REF=$(tr -d '\r\n' < "$STAGE/ref")
    fi
    case "$REF" in ""|*[!a-fA-F0-9]*) die "--ref must be a full 40-character commit SHA." ;; esac
    [ "${#REF}" -eq 40 ] || die "--ref must be a full 40-character commit SHA."
    REPO_URL=https://raw.githubusercontent.com/AkCodes23/AutoEvolve/$REF
    GUIDE=https://github.com/AkCodes23/AutoEvolve/blob/$REF/docs/adapters.md
    echo "Distribution commit: $REF"
else
    GUIDE=$SOURCE_DIR/docs/adapters.md
    echo "Distribution directory: $SOURCE_DIR"
fi
fetch() {
    valid_path "$1" || die "Invalid distribution path: $1"
    mkdir -p "$(dirname "$STAGE/$1")"
    if [ -n "$SOURCE_DIR" ]; then cp "$SOURCE_DIR/$1" "$STAGE/$1"
    else download "$REPO_URL/$1" "$STAGE/$1"; fi
}
verify() {
    expected=$(awk -v file="$1" '$2 == file {print $1}' "$STAGE/checksums.txt")
    if [ -z "$expected" ] || [ "$expected" != "$(hash_file "$STAGE/$1")" ]; then
        die "Checksum mismatch for $1. Retry or regenerate the local distribution."
    fi
}
fetch checksums.txt
fetch adapters/manifest.txt
verify adapters/manifest.txt
awk -F '|' 'NF != 5 || $1 !~ /^[a-z][a-z-]*$/ ||
    ($4 != "automatic" && $4 != "manual") ||
    ($5 != "documented" && $5 != "experimental") {exit 1}' "$STAGE/adapters/manifest.txt" ||
    die "Invalid adapter manifest."
while IFS='|' read -r agent src dst activation status; do
    if ! valid_path "$src" || ! valid_path "$dst"; then die "Invalid adapter path."; fi
done < "$STAGE/adapters/manifest.txt"
if [ "$LIST" -eq 1 ]; then cat "$STAGE/adapters/manifest.txt"; exit 0; fi
case "$AGENTS" in ""|,*|*,|*,,*|*[!a-z,-]*) die "Use a comma-separated list of agent IDs." ;; esac
printf '%s\n' "$AGENTS" | tr ',' '\n' | sort -u > "$STAGE/selected"
while IFS= read -r agent; do
    awk -F '|' -v id="$agent" '$1 == id {found=1} END {exit !found}' "$STAGE/adapters/manifest.txt" ||
        die "Unknown agent '$agent'; use --list-agents."
done < "$STAGE/selected"
for file in DIRECTION.md JOURNAL.md CONSTRAINTS.md; do
    fetch "$file"
    verify "$file"
    printf '%s|%s|state\n' "$file" "$file" >> "$STAGE/plan"
done
while IFS='|' read -r agent src dst activation status; do
    if ! awk -v id="$agent" '$0 == id {found=1} END {exit !found}' "$STAGE/selected"; then continue; fi
    fetch "$src"
    verify "$src"
    printf '%s|%s|engine\n' "$src" "$dst" >> "$STAGE/plan"
    echo "Selected $agent ($status; $activation activation): $dst"
done < "$STAGE/adapters/manifest.txt"

CONFLICTS=0
while IFS='|' read -r src dst kind; do
    safe_target "$dst"
    safe_target ".autoevolve/receipts/$dst.sha256"
    destination=$TARGET_DIR/$dst
    receipt=$TARGET_DIR/.autoevolve/receipts/$dst.sha256
    blocked=0
    parent=$(dirname "$destination")
    while [ "$parent" != "$TARGET_DIR" ]; do
        if [ -e "$parent" ] && [ ! -d "$parent" ]; then blocked=1; break; fi
        parent=$(dirname "$parent")
    done
    if [ "$blocked" -eq 1 ] || { [ -e "$destination" ] && [ ! -f "$destination" ]; }; then
        echo "[manual integration required] $dst (an existing file or directory blocks this path)"
        CONFLICTS=$((CONFLICTS + 1))
        continue
    fi
    if [ -f "$destination" ] && [ "$kind" = state ]; then
        echo "[preserved] $dst"
        continue
    fi
    digest=$(hash_file "$STAGE/$src")
    if [ -f "$destination" ] && [ "$(hash_file "$destination")" != "$digest" ]; then
        previous=$(hash_file "$destination")
        if [ "$FORCE" -ne 1 ] || [ ! -f "$receipt" ] || [ "$(cat "$receipt")" != "$previous" ]; then
            echo "[manual integration required] $dst (existing contents preserved)"
            CONFLICTS=$((CONFLICTS + 1))
            continue
        fi
        safe_target .autoevolve/backups
        mkdir -p "$TARGET_DIR/.autoevolve/backups"
        backup=$(mktemp -d "$TARGET_DIR/.autoevolve/backups/upgrade.XXXXXX")
        cp "$destination" "$backup/$(basename "$dst")"
        echo "[backup] $backup/$(basename "$dst")"
    fi
    if [ -f "$destination" ] && [ "$(hash_file "$destination")" = "$digest" ]; then
        echo "[current] $dst"
    else
        mkdir -p "$(dirname "$destination")"
        TEMPORARY=$(mktemp "$(dirname "$destination")/.autoevolve.XXXXXX")
        cp "$STAGE/$src" "$TEMPORARY"
        mv "$TEMPORARY" "$destination"
        TEMPORARY=
        echo "[installed] $dst"
    fi
    if [ "$kind" = engine ]; then
        mkdir -p "$(dirname "$receipt")"
        printf '%s\n' "$digest" > "$STAGE/receipt"
        mv "$STAGE/receipt" "$receipt"
    fi
done < "$STAGE/plan"
if [ "$CONFLICTS" -ne 0 ]; then
    echo "Installation needs manual integration for $CONFLICTS file(s). No conflicting files were replaced."
    echo "Compare the selected adapter with your existing instructions; see $GUIDE"
    exit 2
fi
echo "Files installed or already current. This does not verify agent activation."
echo "Follow the selected agent's activation check at $GUIDE, then complete DIRECTION.md."
