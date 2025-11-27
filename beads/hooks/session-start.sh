#!/usr/bin/env bash
set -euo pipefail
# Session start hook for beads plugin
# Checks bd installation, repo initialization, and injects workflow context

# Check if bd is installed
if ! command -v bd &>/dev/null; then
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<beads-system>\n**Beads (bd) Not Installed**\n\nInstall beads for dependency-aware issue tracking:\nhttps://github.com/steveyegge/beads\n\nFor skill details: Skill tool with \"beads:using-beads\"\n</beads-system>"
  }
}
EOF
  exit 0
fi

# Check if beads is initialized in current repo
beads_initialized="false"
beads_db_path=""
info_json=""

if info_json=$(bd info --json 2>/dev/null); then
  if echo "$info_json" | grep -q '"database_path"'; then
    beads_initialized="true"
    if command -v jq &>/dev/null; then
      beads_db_path=$(echo "$info_json" | jq -r '.database_path // ""')
    fi
  fi
fi

# Build context based on initialization status
if [ "$beads_initialized" = "true" ]; then
  # Get counts using jq if available
  ready_count="0"
  in_progress_count="0"

  if command -v jq &>/dev/null; then
    ready_count=$(bd ready --json 2>/dev/null | jq 'length' || echo "0")
    in_progress_count=$(bd list --status in_progress --json 2>/dev/null | jq 'length' || echo "0")
  fi

  # Shorten path for display
  display_path="$beads_db_path"
  if [ -n "$beads_db_path" ]; then
    display_path=$(echo "$beads_db_path" | sed "s|$HOME|~|")
  fi

  context="<beads-system>
**Beads (bd) - Issue Tracking ACTIVE**

Database: ${display_path}
Ready: ${ready_count} | In Progress: ${in_progress_count}

**START OF SESSION CHECKLIST:**
1. Run \`bd ready\` to see what's actionable
2. Run \`bd list --status in_progress\` to see claimed work
3. Claim work with \`bd update ID --status in_progress\`

**Quick Commands:**
| Action | Command |
|--------|---------|
| What's ready? | \`bd ready\` |
| Start work | \`bd update ID --status in_progress\` |
| Create issue | \`bd create \"title\"\` |
| Add blocker | \`bd dep add BLOCKED BLOCKER\` |
| Finish work | \`bd close ID --reason \"...\"\` |

**IMPORTANT:** Before ending session, leftover work (TODOs, FIXMEs, review issues) will be captured as beads issues.

For full workflow: Skill tool with \"beads:using-beads\"
</beads-system>"
else
  context="<beads-system>
**Beads (bd) - NOT INITIALIZED IN THIS REPO**

Beads is installed but this repository has no .beads/ directory.

**ACTION REQUIRED:** Initialize beads for this project:
\`\`\`bash
bd init                    # Use directory name as prefix
bd init --prefix myapp     # Or specify custom prefix
\`\`\`

After initialization:
1. \`bd create \"First issue\"\` - Create your first issue
2. \`bd ready\` - See what's ready to work on

**Why initialize?**
- Track discovered work as you code
- Manage dependencies between tasks
- Never lose TODOs, FIXMEs, or review items
- AI-friendly workflow with \`bd ready\`

For full workflow: Skill tool with \"beads:using-beads\"
</beads-system>"
fi

# Escape for JSON using jq
if command -v jq &>/dev/null; then
  context_escaped=$(echo "$context" | jq -Rs . | sed 's/^"//;s/"$//')
else
  context_escaped=$(printf '%s' "$context" | \
    sed 's/\\/\\\\/g' | \
    sed 's/"/\\"/g' | \
    sed 's/	/\\t/g' | \
    sed $'s/\r/\\\\r/g' | \
    sed 's/\f/\\f/g' | \
    awk '{printf "%s\\n", $0}')
fi

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${context_escaped}"
  }
}
EOF
