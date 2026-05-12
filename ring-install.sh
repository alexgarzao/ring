#!/usr/bin/env bash
# ring-install.sh — build & install Ring plugins for Opencode and Codex.
# Claude Code reads .claude-plugin/marketplace.json directly and needs no symlinks.
#
# Targets: macOS bash 3.2 and Linux bash 4+. No associative arrays, no mapfile.

set -euo pipefail

# ---------- portable repo-root detection ----------
SCRIPT_SOURCE="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_SOURCE")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# ---------- constants ----------
TEAMS="default dev-team pm-team tw-team"
BUILD_DIR="$REPO_ROOT/.ring-build"
OPENCODE_OUT="$BUILD_DIR/opencode"
CODEX_OUT="$BUILD_DIR/codex/skills"
PY_HELPER="$REPO_ROOT/scripts/_codex_frontmatter.py"
LOOKUP_JSON="$BUILD_DIR/.codex-lookup.json"

OPENCODE_AGENT_TGT="$HOME/.config/opencode/agent"
OPENCODE_SKILL_TGT="$HOME/.config/opencode/skill"
OPENCODE_COMMAND_TGT="$HOME/.config/opencode/command"
OPENCODE_PLUGINS_TGT="$HOME/.config/opencode/plugins"
CODEX_SKILL_TGT="$HOME/.codex/skills"

# ---------- flags ----------
DRY_RUN=0
VERBOSE=0
FORCE=0

# ---------- logging ----------
log()    { printf '%s\n' "$*"; }
vlog()   { if [ "$VERBOSE" -eq 1 ]; then printf '  %s\n' "$*"; fi; }
warn()   { printf 'WARN: %s\n' "$*" >&2; }
err()    { printf 'ERROR: %s\n' "$*" >&2; }
action() {
  # action <verb> <detail>
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[DRY-RUN] would %s %s\n' "$1" "$2"
  else
    if [ "$VERBOSE" -eq 1 ]; then
      printf '%s %s\n' "$1" "$2"
    fi
  fi
}

# ---------- usage ----------
usage() {
  cat <<'EOF'
ring-install.sh — build & install Ring plugins for Opencode and Codex.

USAGE:
  ring-install.sh <subcommand> [flags]

SUBCOMMANDS:
  build      Generate .ring-build/{opencode,codex} from source plugins.
  install    Symlink build outputs into Opencode and Codex config dirs.
  clean      Remove generated build outputs (preserves codex .system/).
  all        clean + build + install.
  doctor     Verify install symlinks and build outputs; print PASS/FAIL.

FLAGS:
  --dry-run  Print intended actions; change nothing.
  --verbose  Per-file logging.
  --force    Replace non-symlink targets at install destinations (timestamped backup).
  --help     Show this message.

EXIT CODES:
  0  clean
  1  usage error
  2  missing python3
  3  invalid source repo
  4  install collision (target exists, not a symlink, --force not given)
  5  build produced zero output
EOF
}

# ---------- sanity ----------
sanity_check_repo() {
  if [ ! -f "$REPO_ROOT/CLAUDE.md" ] || \
     [ ! -d "$REPO_ROOT/default/agents" ] || \
     [ ! -f "$REPO_ROOT/.claude-plugin/marketplace.json" ]; then
    err "not a Ring repo root: $REPO_ROOT (missing CLAUDE.md, default/agents/, or .claude-plugin/marketplace.json)"
    exit 3
  fi
}

require_python3() {
  if ! command -v python3 >/dev/null 2>&1; then
    err "python3 is required for 'build' but was not found in PATH"
    case "$(uname -s)" in
      Darwin) err "install with: xcode-select --install" ;;
      *)      err "install python3 via your package manager" ;;
    esac
    exit 2
  fi
}

# ---------- mutating helpers (dry-run aware) ----------
do_mkdir_p() {
  local d="$1"
  if [ "$DRY_RUN" -eq 1 ]; then
    action "mkdir -p" "$d"
  else
    mkdir -p "$d"
  fi
}

do_rm_rf() {
  local p="$1"
  if [ "$DRY_RUN" -eq 1 ]; then
    action "rm -rf" "$p"
  else
    rm -rf "$p"
  fi
}

do_rm_one() {
  local p="$1"
  if [ "$DRY_RUN" -eq 1 ]; then
    action "rm" "$p"
  else
    rm -f "$p" || rm -rf "$p"
  fi
}

do_mv() {
  local src="$1"; local dst="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    action "mv" "$src -> $dst"
  else
    mv "$src" "$dst"
  fi
}

do_cp_file() {
  local src="$1"; local dst="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    action "cp" "$src -> $dst"
  else
    mkdir -p "$(dirname "$dst")"
    cp -f "$src" "$dst"
  fi
}

do_rsync_dir() {
  local src="$1"; local dst="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    action "rsync -a" "$src/ -> $dst/"
  else
    mkdir -p "$dst"
    rsync -a --delete "$src/" "$dst/"
  fi
}

do_ln_s() {
  local target="$1"; local linkpath="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    action "ln -s" "$target -> $linkpath"
  else
    ln -s "$target" "$linkpath"
  fi
}

# ---------- clean ----------
do_clean() {
  log "==> clean"

  if [ -d "$OPENCODE_OUT" ]; then
    do_rm_rf "$OPENCODE_OUT"
    vlog "removed $OPENCODE_OUT"
  fi

  # Preserve .system/ under codex/skills; wipe everything else there.
  if [ -d "$CODEX_OUT" ]; then
    local entry base
    for entry in "$CODEX_OUT"/* "$CODEX_OUT"/.[!.]*; do
      [ -e "$entry" ] || continue
      base="$(basename "$entry")"
      if [ "$base" = ".system" ]; then
        vlog "preserve $entry"
        continue
      fi
      if [ "$base" = ".codex-lookup.json" ]; then
        # this file lives one level up; defensive only
        continue
      fi
      do_rm_rf "$entry"
      vlog "removed $entry"
    done
  else
    do_mkdir_p "$CODEX_OUT"
  fi

  # Remove stale lookup cache (not under .system/).
  if [ -f "$LOOKUP_JSON" ]; then
    do_rm_one "$LOOKUP_JSON"
  fi
}

# ---------- build ----------
copy_opencode_agents() {
  local team="$1"
  local src_dir="$REPO_ROOT/$team/agents"
  local dst_dir="$OPENCODE_OUT/agent/$team"
  [ -d "$src_dir" ] || return 0
  local f base
  for f in "$src_dir"/*.md; do
    [ -e "$f" ] || continue
    base="$(basename "$f")"
    do_cp_file "$f" "$dst_dir/$base"
    vlog "agent: $team/$base"
  done
}

copy_opencode_skills() {
  local team="$1"
  local src_dir="$REPO_ROOT/$team/skills"
  local dst_dir="$OPENCODE_OUT/skill/$team"
  [ -d "$src_dir" ] || return 0
  local d name
  for d in "$src_dir"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    # shared-patterns has no SKILL.md; it's an accessory dir referenced
    # from other skills via '../shared-patterns/X.md'. Mirror it alongside
    # the skill outputs so those refs resolve naturally.
    if [ "$name" = "shared-patterns" ]; then
      copy_accessory_dir_opencode "$team" "$d"
      continue
    fi
    do_rsync_dir "$d" "$dst_dir/$name"
    vlog "skill: $team/$name"
  done
}

# Mirror {team}/skills/shared-patterns/ into the opencode tree at
# skill/{team}/shared-patterns/ so '../shared-patterns/X.md' refs resolve.
copy_accessory_dir_opencode() {
  local team="$1"; local src="$2"
  local count
  count=$(find "$src" -maxdepth 1 -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "${count:-0}" -eq 0 ]; then
    vlog "shared-patterns empty: $team (skip)"
    return 0
  fi
  local dst="$OPENCODE_OUT/skill/$team/shared-patterns"
  if [ "$DRY_RUN" -eq 1 ]; then
    action "rsync -a" "$src -> $dst/"
  else
    mkdir -p "$dst"
    rsync -a --delete "$src" "$dst/"
  fi
  vlog "opencode shared-patterns: $team"
}

# Mirror dev-team/docs/ into opencode at skill/docs/ so that
# '../../docs/standards/...' refs from skill/{team}/{name}/SKILL.md resolve to
# skill/docs/standards/... — only dev-team has docs referenced cross-skill.
copy_docs_mirror_opencode() {
  local src="$REPO_ROOT/dev-team/docs"
  local dst="$OPENCODE_OUT/skill/docs"
  [ -d "$src" ] || return 0
  if [ "$DRY_RUN" -eq 1 ]; then
    action "rsync -a" "$src/ -> $dst/"
  else
    mkdir -p "$dst"
    rsync -a --delete "$src/" "$dst/"
  fi
  vlog "opencode docs mirror"
}

# Mirror dev-team/skills/shared-patterns/ at the .ring-build/opencode/ top level
# under dev-team/skills/shared-patterns/. The default/codereview reviewers
# reference accessory files via '../../../../dev-team/skills/shared-patterns/X.md',
# which resolves to .ring-build/opencode/dev-team/skills/shared-patterns/X.md.
copy_top_level_cross_plugin_opencode() {
  local src="$REPO_ROOT/dev-team/skills/shared-patterns"
  local dst="$OPENCODE_OUT/dev-team/skills/shared-patterns"
  [ -d "$src" ] || return 0
  if [ "$DRY_RUN" -eq 1 ]; then
    action "rsync -a" "$src/ -> $dst/"
  else
    mkdir -p "$dst"
    rsync -a --delete "$src/" "$dst/"
  fi
  vlog "opencode top-level cross-plugin mirror: dev-team/skills/shared-patterns"
}

copy_opencode_commands() {
  local team="$1"
  local src_dir="$REPO_ROOT/$team/commands"
  local dst_dir="$OPENCODE_OUT/command/$team"
  [ -d "$src_dir" ] || return 0
  local f base
  for f in "$src_dir"/*.md; do
    [ -e "$f" ] || continue
    base="$(basename "$f")"
    do_cp_file "$f" "$dst_dir/$base"
    vlog "command: $team/$base"
  done
}

build_codex_skill() {
  local team="$1"; local skill_dir="$2"
  local name dst_dir src_skill_md dst_skill_md
  name="$(basename "$skill_dir")"
  # shared-patterns is an accessory dir, not a skill — handled separately.
  [ "$name" = "shared-patterns" ] && return 0
  dst_dir="$CODEX_OUT/$team/ring-${team}-${name}"
  src_skill_md="$skill_dir/SKILL.md"
  dst_skill_md="$dst_dir/SKILL.md"

  if [ ! -f "$src_skill_md" ]; then
    warn "skipping (no SKILL.md): $skill_dir"
    return 0
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    action "rsync -a --exclude SKILL.md" "$skill_dir/ -> $dst_dir/"
    action "transform SKILL.md" "$src_skill_md -> $dst_skill_md"
    action "rewrite accessory paths under" "$dst_dir/"
    return 0
  fi

  mkdir -p "$dst_dir"
  # copy supporting files verbatim, but not SKILL.md (helper writes it atomically)
  rsync -a --delete --exclude='SKILL.md' "$skill_dir/" "$dst_dir/"

  python3 "$PY_HELPER" \
    --source "$src_skill_md" \
    --dest   "$dst_skill_md" \
    --team   "$team" \
    --skill-name "$name" \
    --lookup "$LOOKUP_JSON"

  # Rewrite link paths in accessory .md files copied into the codex skill dir.
  rewrite_accessory_paths_in "$dst_dir" "$team"

  vlog "codex skill: $team/$name -> ring-${team}-${name}"
}

# Mirror {team}/skills/shared-patterns/ into codex at skills/{team}/shared-patterns/.
# Then rewrite any cross-skill link refs inside those files (e.g. ../dev-cycle/SKILL.md
# -> ../ring-dev-team-dev-cycle/SKILL.md).
copy_accessory_dir_codex() {
  local team="$1"
  local src="$REPO_ROOT/$team/skills/shared-patterns"
  local dst="$CODEX_OUT/$team/shared-patterns"
  [ -d "$src" ] || return 0
  local count
  count=$(find "$src" -maxdepth 1 -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "${count:-0}" -eq 0 ]; then
    vlog "codex shared-patterns empty: $team (skip)"
    return 0
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    action "rsync -a" "$src/ -> $dst/"
    action "rewrite accessory paths under" "$dst/"
    return 0
  fi
  mkdir -p "$dst"
  rsync -a --delete "$src/" "$dst/"
  rewrite_accessory_paths_in "$dst" "$team"
  vlog "codex shared-patterns: $team"
}

# Mirror dev-team/docs/ into codex at skills/docs/ so '../../docs/standards/...'
# refs from skill SKILL.md files resolve.
copy_docs_mirror_codex() {
  local src="$REPO_ROOT/dev-team/docs"
  local dst="$CODEX_OUT/docs"
  [ -d "$src" ] || return 0
  if [ "$DRY_RUN" -eq 1 ]; then
    action "rsync -a" "$src/ -> $dst/"
  else
    mkdir -p "$dst"
    rsync -a --delete "$src/" "$dst/"
  fi
  vlog "codex docs mirror"
}

# Walk a directory of .md files (skipping SKILL.md, which the helper has
# already transformed) and run the link-path rewriter on each.
rewrite_accessory_paths_in() {
  local dir="$1"; local team="$2"
  [ -d "$dir" ] || return 0
  local f
  # use find -print0 + while-read to handle any oddities; but stay 3.2-compatible
  find "$dir" -type f -name '*.md' ! -name 'SKILL.md' -print | while IFS= read -r f; do
    python3 "$PY_HELPER" --rewrite-paths \
      --source "$f" --dest "$f" \
      --team "$team" --lookup "$LOOKUP_JSON"
  done
}

do_build() {
  require_python3
  log "==> build"

  # clean first (preserves codex .system/)
  do_clean

  # ensure output skeletons
  do_mkdir_p "$OPENCODE_OUT/agent"
  do_mkdir_p "$OPENCODE_OUT/skill"
  do_mkdir_p "$OPENCODE_OUT/command"
  do_mkdir_p "$CODEX_OUT"

  # build the skill-name -> team lookup once
  if [ "$DRY_RUN" -eq 1 ]; then
    action "build lookup" "$LOOKUP_JSON"
  else
    python3 "$PY_HELPER" --build-lookup "$REPO_ROOT" --lookup-out "$LOOKUP_JSON"
    vlog "lookup written: $LOOKUP_JSON"
  fi

  local team d
  for team in $TEAMS; do
    [ -d "$REPO_ROOT/$team" ] || { warn "team dir missing: $team"; continue; }
    copy_opencode_agents   "$team"
    copy_opencode_skills   "$team"
    copy_opencode_commands "$team"
    copy_accessory_dir_codex "$team"

    if [ -d "$REPO_ROOT/$team/skills" ]; then
      for d in "$REPO_ROOT/$team/skills"/*/; do
        [ -d "$d" ] || continue
        build_codex_skill "$team" "${d%/}"
      done
    fi
  done

  # Cross-cutting mirrors (referenced from multiple teams / skills):
  copy_docs_mirror_opencode
  copy_docs_mirror_codex
  copy_top_level_cross_plugin_opencode

  # Sanity: did the build produce anything?
  if [ "$DRY_RUN" -eq 0 ]; then
    local count
    count=$(find "$OPENCODE_OUT" "$CODEX_OUT" -mindepth 1 -maxdepth 4 -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "${count:-0}" -eq 0 ]; then
      err "build produced zero output"
      exit 5
    fi
  fi
}

# ---------- install ----------
ensure_symlink() {
  local src="$1"; local target="$2"

  if [ -L "$target" ]; then
    local current
    current="$(readlink "$target")"
    if [ "$current" = "$src" ]; then
      log "SKIP   $target"
      return 0
    fi
    do_rm_one "$target"
    do_mkdir_p "$(dirname "$target")"
    do_ln_s "$src" "$target"
    log "UPDATE $target  (was -> $current)"
    return 0
  fi

  if [ -e "$target" ]; then
    if [ "$FORCE" -eq 1 ]; then
      local backup
      backup="${target}.backup_$(date +%Y%m%d_%H%M%S)"
      do_mv "$target" "$backup"
      do_mkdir_p "$(dirname "$target")"
      do_ln_s "$src" "$target"
      log "BACKUP+CREATE $target  (backup: $backup)"
      return 0
    fi
    err "collision: $target exists and is not a symlink; re-run with --force to back up and replace"
    exit 4
  fi

  do_mkdir_p "$(dirname "$target")"
  do_ln_s "$src" "$target"
  log "CREATE $target"
}

do_install() {
  log "==> install"

  # Opencode plugins dangling symlink cleanup
  if [ -L "$OPENCODE_PLUGINS_TGT" ] && [ ! -e "$OPENCODE_PLUGINS_TGT" ]; then
    do_rm_one "$OPENCODE_PLUGINS_TGT"
    log "REMOVE $OPENCODE_PLUGINS_TGT  (dangling symlink)"
  fi

  ensure_symlink "$OPENCODE_OUT/agent"   "$OPENCODE_AGENT_TGT"
  ensure_symlink "$OPENCODE_OUT/skill"   "$OPENCODE_SKILL_TGT"
  ensure_symlink "$OPENCODE_OUT/command" "$OPENCODE_COMMAND_TGT"
  ensure_symlink "$CODEX_OUT"            "$CODEX_SKILL_TGT"
}

# ---------- doctor ----------
check_symlink_into_build() {
  # check_symlink_into_build <target> <expected_src>
  local target="$1"; local expected="$2"
  if [ ! -L "$target" ]; then
    log "FAIL   $target  (not a symlink)"
    return 1
  fi
  local current
  current="$(readlink "$target")"
  if [ "$current" != "$expected" ]; then
    log "FAIL   $target  (-> $current; expected $expected)"
    return 1
  fi
  if [ ! -e "$target" ]; then
    log "FAIL   $target  (dangling -> $current)"
    return 1
  fi
  log "PASS   $target"
  return 0
}

is_known_team() {
  local t="$1" k
  for k in $TEAMS; do
    [ "$k" = "$t" ] && return 0
  done
  return 1
}

do_doctor() {
  log "==> doctor"
  local rc=0

  check_symlink_into_build "$OPENCODE_AGENT_TGT"   "$OPENCODE_OUT/agent"   || rc=1
  check_symlink_into_build "$OPENCODE_SKILL_TGT"   "$OPENCODE_OUT/skill"   || rc=1
  check_symlink_into_build "$OPENCODE_COMMAND_TGT" "$OPENCODE_OUT/command" || rc=1
  check_symlink_into_build "$CODEX_SKILL_TGT"      "$CODEX_OUT"            || rc=1

  if [ -e "$OPENCODE_PLUGINS_TGT" ] || [ -L "$OPENCODE_PLUGINS_TGT" ]; then
    warn "$OPENCODE_PLUGINS_TGT exists (expected absent)"
    rc=1
  else
    log "PASS   $OPENCODE_PLUGINS_TGT absent"
  fi

  if [ -d "$CODEX_OUT/.system" ]; then
    log "PASS   $CODEX_OUT/.system present"
  else
    log "FAIL   $CODEX_OUT/.system missing"
    rc=1
  fi

  # accessory mirrors
  if [ -d "$OPENCODE_OUT/skill/docs/standards" ]; then
    log "PASS   $OPENCODE_OUT/skill/docs/standards (docs mirror)"
  else
    log "FAIL   $OPENCODE_OUT/skill/docs/standards missing (docs mirror)"
    rc=1
  fi
  if [ -d "$CODEX_OUT/docs/standards" ]; then
    log "PASS   $CODEX_OUT/docs/standards (docs mirror)"
  else
    log "FAIL   $CODEX_OUT/docs/standards missing (docs mirror)"
    rc=1
  fi
  if [ -d "$OPENCODE_OUT/dev-team/skills/shared-patterns" ]; then
    log "PASS   $OPENCODE_OUT/dev-team/skills/shared-patterns (cross-plugin mirror)"
  else
    log "FAIL   $OPENCODE_OUT/dev-team/skills/shared-patterns missing"
    rc=1
  fi
  # per-team shared-patterns mirrors (only for teams that have one in source)
  local team src_sp
  for team in $TEAMS; do
    src_sp="$REPO_ROOT/$team/skills/shared-patterns"
    [ -d "$src_sp" ] || continue
    local count
    count=$(find "$src_sp" -maxdepth 1 -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
    [ "${count:-0}" -eq 0 ] && continue
    if [ -d "$OPENCODE_OUT/skill/$team/shared-patterns" ]; then
      log "PASS   $OPENCODE_OUT/skill/$team/shared-patterns"
    else
      log "FAIL   $OPENCODE_OUT/skill/$team/shared-patterns missing"
      rc=1
    fi
    if [ -d "$CODEX_OUT/$team/shared-patterns" ]; then
      log "PASS   $CODEX_OUT/$team/shared-patterns"
    else
      log "FAIL   $CODEX_OUT/$team/shared-patterns missing"
      rc=1
    fi
  done

  # stale teams in build output (treat 'docs' and 'dev-team' top-level as
  # legitimate accessory mirrors, not teams)
  local d base
  if [ -d "$OPENCODE_OUT/agent" ]; then
    for d in "$OPENCODE_OUT/agent"/*/; do
      [ -d "$d" ] || continue
      base="$(basename "$d")"
      if ! is_known_team "$base"; then
        warn "stale team in opencode/agent: $base"
      fi
    done
  fi
  if [ -d "$CODEX_OUT" ]; then
    for d in "$CODEX_OUT"/*/; do
      [ -d "$d" ] || continue
      base="$(basename "$d")"
      case "$base" in
        .system|docs) continue ;;
      esac
      if ! is_known_team "$base"; then
        warn "stale team in codex/skills: $base"
      fi
    done
  fi

  # orphan skills: built skill dir whose source no longer exists
  local src_skill_dir
  for team in $TEAMS; do
    if [ -d "$OPENCODE_OUT/skill/$team" ]; then
      for d in "$OPENCODE_OUT/skill/$team"/*/; do
        [ -d "$d" ] || continue
        base="$(basename "$d")"
        # shared-patterns is an accessory mirror, not a skill
        [ "$base" = "shared-patterns" ] && continue
        src_skill_dir="$REPO_ROOT/$team/skills/$base"
        if [ ! -d "$src_skill_dir" ]; then
          warn "orphan opencode skill: $team/$base (no source $src_skill_dir)"
        fi
      done
    fi
    if [ -d "$CODEX_OUT/$team" ]; then
      for d in "$CODEX_OUT/$team"/*/; do
        [ -d "$d" ] || continue
        base="$(basename "$d")"
        [ "$base" = "shared-patterns" ] && continue
        # strip ring-<team>- prefix
        local prefix="ring-${team}-"
        local short="$base"
        case "$base" in
          "$prefix"*) short="${base#$prefix}" ;;
        esac
        src_skill_dir="$REPO_ROOT/$team/skills/$short"
        if [ ! -d "$src_skill_dir" ]; then
          warn "orphan codex skill: $team/$base (no source $src_skill_dir)"
        fi
      done
    fi
  done

  if [ "$rc" -eq 0 ]; then
    log "doctor: all PASS"
  else
    log "doctor: drift detected"
  fi
  return $rc
}

# ---------- arg parsing ----------
SUBCMD=""
for arg in "$@"; do
  case "$arg" in
    --help|-h) usage; exit 0 ;;
    --dry-run) DRY_RUN=1 ;;
    --verbose) VERBOSE=1 ;;
    --force)   FORCE=1 ;;
    build|install|clean|all|doctor)
      if [ -n "$SUBCMD" ]; then
        err "multiple subcommands given: $SUBCMD and $arg"
        usage
        exit 1
      fi
      SUBCMD="$arg"
      ;;
    *)
      err "unknown argument: $arg"
      usage
      exit 1
      ;;
  esac
done

if [ -z "$SUBCMD" ]; then
  usage
  exit 1
fi

sanity_check_repo

case "$SUBCMD" in
  build)   do_build ;;
  install) do_install ;;
  clean)   do_clean ;;
  all)     do_clean; do_build; do_install ;;
  doctor)  do_doctor ;;
esac
