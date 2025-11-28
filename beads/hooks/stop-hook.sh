#!/usr/bin/env bash
set -euo pipefail
# Stop hook for beads plugin
# Prompts Claude to capture leftover work as beads issues before ending session

# Check if bd is installed
if ! command -v bd &>/dev/null; then
  # bd not installed - no action needed
  cat <<'EOF'
{
  "decision": "approve",
  "reason": "beads not installed"
}
EOF
  exit 0
fi

# Check if beads is initialized
if ! bd info --json 2>/dev/null | grep -q '"database_path"'; then
  # Not initialized - no action needed
  cat <<'EOF'
{
  "decision": "approve",
  "reason": "beads not initialized in this repo"
}
EOF
  exit 0
fi

# Check if checkpoint has been completed
# Strategy: If there are open issues OR no uncommitted changes with markers, approve exit
OPEN_ISSUES=$(bd status 2>/dev/null | grep -E "Total Issues:|Open:" | head -2 | tail -1 | awk '{print $2}' || echo "0")
RECENT_MARKERS=$(git diff --name-only HEAD~5 2>/dev/null | head -20 | xargs grep -c -E "(TODO|FIXME|HACK|XXX):" 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "0")

# If we have open issues capturing work, or no markers found, allow exit
if [[ "$OPEN_ISSUES" -gt 0 ]] || [[ "$RECENT_MARKERS" -eq 0 ]]; then
  cat <<'EOF'
{
  "decision": "approve",
  "reason": "beads checkpoint complete - work captured in issues or no markers found"
}
EOF
  exit 0
fi

# Beads is active - inject prompt to capture leftover work
prompt='**BEADS END-OF-SESSION CHECKPOINT**

Before ending this session, capture any leftover work as beads issues:

1. **Search for code markers** in files modified this session:
   ```bash
   # Find TODOs, FIXMEs, HACKs, XXX in recent files
   git diff --name-only HEAD~5 2>/dev/null | head -20 | xargs grep -n -E "(TODO|FIXME|HACK|XXX):" 2>/dev/null | head -30
   ```

2. **Check your TodoWrite list** - any incomplete items should become beads issues

3. **Review any code review findings** that were flagged but not yet addressed

4. **Create beads issues** for each piece of leftover work:
   ```bash
   bd create "TODO: [description from code]" -t task -p 2
   bd create "FIXME: [description from code]" -t bug -p 1
   bd create "Code review: [finding]" -t task -p 2
   ```

5. **Update in-progress issues** - if leaving work incomplete:
   ```bash
   bd update ISSUE-ID --status open  # Release claim if blocked
   bd comment ISSUE-ID "Session ended - progress: [summary]"
   ```

6. **Run final status**:
   ```bash
   bd status
   ```

If there is NO leftover work (all tasks completed, no TODOs found), you may proceed to end the session.

**DO NOT** end the session without:
- Checking for leftover work markers
- Creating issues for any discovered work
- Updating any in-progress issues with status'

# Escape for JSON using jq
if command -v jq &>/dev/null; then
  prompt_escaped=$(echo "$prompt" | jq -Rs . | sed 's/^"//;s/"$//')
else
  prompt_escaped=$(printf '%s' "$prompt" | \
    sed 's/\\/\\\\/g' | \
    sed 's/"/\\"/g' | \
    sed 's/	/\\t/g' | \
    sed $'s/\r/\\\\r/g' | \
    sed 's/\f/\\f/g' | \
    awk '{printf "%s\\n", $0}')
fi

cat <<EOF
{
  "decision": "approve",
  "reason": "${prompt_escaped}"
}
EOF
