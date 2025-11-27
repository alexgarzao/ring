#!/usr/bin/env bash
set -euo pipefail
# Session start hook for ring-tw-team plugin
# Dynamically generates quick reference for technical writing agents

# Find the monorepo root (where shared/ directory exists)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MONOREPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"

# Path to shared utility
SHARED_UTIL="$MONOREPO_ROOT/shared/lib/generate-reference.py"

# Generate agent reference
if [ -f "$SHARED_UTIL" ] && command -v python3 &>/dev/null; then
  # Use || true to prevent set -e from exiting on non-zero return
  agents_table=$(python3 "$SHARED_UTIL" agents "$PLUGIN_ROOT/agents" 2>/dev/null) || true

  if [ -n "$agents_table" ]; then
    # Build the context message
    context="<ring-tw-team-system>
**Technical Writing Specialists Available**

Use via Task tool with \`subagent_type\`:

${agents_table}

**Documentation Standards:**
- Voice: Assertive but not arrogant, encouraging, tech-savvy but human
- Capitalization: Sentence case for headings (only first letter + proper nouns)
- Structure: Lead with value, short paragraphs, scannable content

For full details: Skill tool with \"ring-tw-team:using-tw-team\"
</ring-tw-team-system>"

    # Escape for JSON using jq (requires jq to be installed)
    if command -v jq &>/dev/null; then
      context_escaped=$(echo "$context" | jq -Rs . | sed 's/^"//;s/"$//')
    else
      # Fallback: more complete escaping
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
  else
    # Fallback to static output if script fails
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-tw-team-system>\n**Technical Writing Specialists Available**\n\nUse via Task tool with `subagent_type`:\n\n| Agent | Expertise |\n|-------|----------|\n| `ring-tw-team:functional-writer` | Guides, tutorials, conceptual docs |\n| `ring-tw-team:api-writer` | API reference, endpoints, schemas |\n| `ring-tw-team:docs-reviewer` | Quality review, voice/tone compliance |\n\n**Documentation Standards:**\n- Voice: Assertive but not arrogant, encouraging, tech-savvy but human\n- Capitalization: Sentence case for headings\n- Structure: Lead with value, short paragraphs, scannable content\n\nFor full details: Skill tool with \"ring-tw-team:using-tw-team\"\n</ring-tw-team-system>"
  }
}
EOF
  fi
else
  # Fallback if Python not available
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-tw-team-system>\n**Technical Writing Specialists**\n\n| Agent | Expertise |\n|-------|----------|\n| `ring-tw-team:functional-writer` | Guides, tutorials, conceptual docs |\n| `ring-tw-team:api-writer` | API reference, endpoints, schemas |\n| `ring-tw-team:docs-reviewer` | Quality review, voice/tone compliance |\n\nFor full list: Skill tool with \"ring-tw-team:using-tw-team\"\n</ring-tw-team-system>"
  }
}
EOF
fi
