#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# Context Usage Check - UserPromptSubmit hook
# Estimates context usage and injects tiered warnings
# Performance target: <50ms execution time

set -euo pipefail

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MONOREPO_ROOT="$(cd "${PLUGIN_ROOT}/.." && pwd)"

# Session identification
# CLAUDE_SESSION_ID is provided by Claude Code, fallback to PPID for session isolation
SESSION_ID="${CLAUDE_SESSION_ID:-$PPID}"

# REQUIRED: Validate session ID - alphanumeric, hyphens, underscores only
if [[ ! "$SESSION_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    # Fall back to PPID if invalid
    SESSION_ID="$PPID"
fi

# Allow users to reset warnings via environment variable
# Set RING_RESET_CONTEXT_WARNING=1 to re-enable warnings
if [[ "${RING_RESET_CONTEXT_WARNING:-}" == "1" ]]; then
    # Will be cleaned up below after STATE_FILE is set
    RESET_REQUESTED=true
else
    RESET_REQUESTED=false
fi

# State file location - use project's .ring/state/ if available, else /tmp
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
# Resolve symlinks to canonical path (prevents path confusion, allows /tmp -> /private/tmp)
if [[ -L "$PROJECT_DIR" ]] && [[ -d "$PROJECT_DIR" ]]; then
    PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd -P)"
fi
if [[ -d "${PROJECT_DIR}/.ring/state" ]]; then
    STATE_DIR="${PROJECT_DIR}/.ring/state"
else
    # Fallback to /tmp for projects without .ring/ initialized
    STATE_DIR="/tmp"
fi
STATE_FILE="${STATE_DIR}/context-usage-${SESSION_ID}.json"
TEMP_STATE="${STATE_FILE}.tmp.$$"

# Cleanup trap for temp file on exit (prevents orphaned files)
trap 'rm -f "$TEMP_STATE" 2>/dev/null' EXIT

# Handle reset request now that STATE_FILE is defined
if [[ "$RESET_REQUESTED" == "true" ]]; then
    rm -f "$STATE_FILE" 2>/dev/null || true
fi

# Source shared libraries
SHARED_LIB="${MONOREPO_ROOT}/shared/lib"
if [[ -f "${SHARED_LIB}/context-check.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SHARED_LIB}/context-check.sh"
else
    # Fallback: inline minimal estimation
    estimate_context_pct() {
        local turn_count="${1:-0}"
        # Match shared lib: (45000 + turns*2500) * 100 / 200000 = 22.5 + turns*1.25
        # Simplified: 23 + (turns * 5 / 4) for integer math (rounds up base for accuracy)
        local pct=$(( 23 + (turn_count * 5 / 4) ))
        [[ "$pct" -gt 100 ]] && pct=100
        echo "$pct"
    }
    get_warning_tier() {
        local pct="${1:-0}"
        if [[ "$pct" -ge 85 ]]; then echo "critical"
        elif [[ "$pct" -ge 70 ]]; then echo "warning"
        elif [[ "$pct" -ge 50 ]]; then echo "info"
        else echo "none"
        fi
    }
    format_context_warning() {
        local tier="$1"
        local pct="$2"
        case "$tier" in
            critical)
                cat <<EOF
<MANDATORY-USER-MESSAGE>
[!!!] CONTEXT CRITICAL: ${pct}% usage detected.

**MANDATORY ACTIONS (NON-NEGOTIABLE):**
1. STOP current task immediately
2. Run /create-handoff to save progress NOW
3. Create continuity-ledger with current state
4. Run /clear to reset context
5. Resume from handoff in new session

**WARNING:** Continuing without handoff risks losing all session progress.
</MANDATORY-USER-MESSAGE>
EOF
                ;;
            warning)
                cat <<EOF
<MANDATORY-USER-MESSAGE>
[!!] Context Warning: ${pct}% usage detected.

**MANDATORY ACTION:**
Create a continuity-ledger NOW to preserve session state.

Run: /create-handoff or manually create ledger with current progress.

**Recommended:** Complete current task, then /clear before starting new work.
</MANDATORY-USER-MESSAGE>
EOF
                ;;
            info) echo "[i] Context at ${pct}%." ;;
            *) echo "" ;;
        esac
    }
fi

if [[ -f "${SHARED_LIB}/json-escape.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SHARED_LIB}/json-escape.sh"
else
    # Fallback: minimal JSON escaping
    json_escape() {
        local input="$1"
        if command -v jq &>/dev/null; then
            printf '%s' "$input" | jq -Rs . | sed 's/^"//;s/"$//'
        else
            printf '%s' "$input" | sed \
                -e 's/\\/\\\\/g' \
                -e 's/"/\\"/g' \
                -e 's/\t/\\t/g' \
                -e 's/\r/\\r/g' \
                -e ':a;N;$!ba;s/\n/\\n/g'
        fi
    }
fi

# Helper function to write state file (consolidates duplicate code)
# Args: $1 = acknowledged_tier value
write_state_file() {
    local ack_tier="$1"
    cat > "$TEMP_STATE" <<EOF
{
  "session_id": "${SESSION_ID_ESCAPED}",
  "turn_count": ${turn_count},
  "estimated_pct": ${estimated_pct},
  "current_tier": "${current_tier}",
  "acknowledged_tier": "${ack_tier}",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    mv "$TEMP_STATE" "$STATE_FILE"
}

# Read current state or initialize
if [[ -f "$STATE_FILE" ]]; then
    if command -v jq &>/dev/null; then
        turn_count=$(jq -r '.turn_count // 0' "$STATE_FILE" 2>/dev/null || echo 0)
        acknowledged_tier=$(jq -r '.acknowledged_tier // "none"' "$STATE_FILE" 2>/dev/null || echo "none")
    else
        # Fallback: grep-based parsing
        turn_count=$(grep -o '"turn_count":[0-9]*' "$STATE_FILE" 2>/dev/null | grep -o '[0-9]*' || echo 0)
        acknowledged_tier=$(grep -o '"acknowledged_tier":"[^"]*"' "$STATE_FILE" 2>/dev/null | sed 's/.*://;s/"//g' || echo "none")
    fi
else
    turn_count=0
    acknowledged_tier="none"
fi

# Increment turn count
turn_count=$((turn_count + 1))

# Estimate context percentage
estimated_pct=$(estimate_context_pct "$turn_count")

# Determine warning tier
current_tier=$(get_warning_tier "$estimated_pct")

# Write updated state using helper function
# Uses atomic write pattern: write to temp, then mv (TEMP_STATE defined at top with trap)
mkdir -p "$(dirname "$STATE_FILE")"

# JSON escape session ID to prevent injection
SESSION_ID_ESCAPED=$(json_escape "$SESSION_ID")

write_state_file "$acknowledged_tier"

# Determine if we should show a warning
# Don't repeat same-tier warnings within session (user has seen it)
# But DO show if tier has escalated
show_warning=false
if [[ "$current_tier" != "none" ]]; then
    case "$current_tier" in
        critical)
            # Always show critical warnings
            show_warning=true
            ;;
        warning)
            # Show if not already acknowledged at warning or higher
            if [[ "$acknowledged_tier" != "warning" && "$acknowledged_tier" != "critical" ]]; then
                show_warning=true
            fi
            ;;
        info)
            # Show if not already acknowledged at any tier
            if [[ "$acknowledged_tier" == "none" ]]; then
                show_warning=true
            fi
            ;;
    esac
fi

# Update acknowledged tier if showing a warning
if [[ "$show_warning" == "true" ]]; then
    # Update state with current tier as acknowledged
    write_state_file "$current_tier"
fi

# Generate output
if [[ "$show_warning" == "true" ]]; then
    warning_content=$(format_context_warning "$current_tier" "$estimated_pct")
    warning_escaped=$(json_escape "$warning_content")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "${warning_escaped}"
  }
}
EOF
else
    # No warning needed, return minimal output
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit"
  }
}
EOF
fi

exit 0
