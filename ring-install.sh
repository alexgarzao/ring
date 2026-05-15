#!/usr/bin/env bash
# ==============================================================================
# DEPRECATED — use install-symlinks.sh instead.
# ==============================================================================
# This script is a thin compatibility shim that forwards all subcommands to
# install-symlinks.sh, which now handles all four targets (Claude Code,
# Factory AI, Opencode, Codex) from a single entry point.
#
# Mapping:
#   ring-install.sh build     -> install-symlinks.sh build
#   ring-install.sh install   -> install-symlinks.sh install --opencode --codex
#   ring-install.sh clean     -> install-symlinks.sh clean
#   ring-install.sh all       -> install-symlinks.sh all --opencode --codex
#   ring-install.sh doctor    -> install-symlinks.sh doctor
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEW_SCRIPT="$SCRIPT_DIR/install-symlinks.sh"

if [ ! -f "$NEW_SCRIPT" ]; then
  printf 'ERROR: %s not found. Re-clone the Ring repository.\n' "$NEW_SCRIPT" >&2
  exit 1
fi

printf '\033[1;33mDEPRECATED:\033[0m ring-install.sh is now a wrapper around install-symlinks.sh\n' >&2
printf '            Switch to: \033[1mbash install-symlinks.sh\033[0m (now supports all four tools + interactive menu)\n\n' >&2

# Translate old subcommands. ring-install.sh only ever targeted opencode + codex,
# so pin those targets to preserve historical behavior for any caller still
# scripted against this entry point.
SUBCMD=""
EXTRA=()
for arg in "$@"; do
  case "$arg" in
    build|install|clean|all|doctor)
      SUBCMD="$arg"
      ;;
    *)
      EXTRA+=("$arg")
      ;;
  esac
done

case "$SUBCMD" in
  install|all)
    exec bash "$NEW_SCRIPT" "$SUBCMD" --opencode --codex --yes "${EXTRA[@]}"
    ;;
  build|clean|doctor|"")
    # No target flags needed for these subcommands.
    [ -z "$SUBCMD" ] && SUBCMD="build"
    exec bash "$NEW_SCRIPT" "$SUBCMD" "${EXTRA[@]}"
    ;;
  *)
    printf 'ERROR: unknown subcommand: %s\n' "$SUBCMD" >&2
    exec bash "$NEW_SCRIPT" --help
    ;;
esac
