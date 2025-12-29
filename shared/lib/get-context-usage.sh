#!/usr/bin/env bash
# Get actual context usage from Claude Code session file
# Returns: percentage (0-100) or "unknown" if cannot determine
#
# Usage: source get-context-usage.sh && get_context_usage
# Or:    bash get-context-usage.sh  (prints percentage)

set -euo pipefail

# Find the current session file
find_session_file() {
    local project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    local claude_projects="$HOME/.claude/projects"

    # Convert project path to Claude's format (replace / with -)
    local project_key
    project_key=$(echo "$project_dir" | sed 's|/|-|g')

    local project_sessions="$claude_projects/$project_key"

    if [[ ! -d "$project_sessions" ]]; then
        echo ""
        return
    fi

    # Find most recently modified .jsonl file
    local session_file
    session_file=$(ls -t "$project_sessions"/*.jsonl 2>/dev/null | head -1)

    echo "$session_file"
}

# Get context usage percentage from session file
get_context_usage() {
    local session_file
    session_file=$(find_session_file)

    if [[ -z "$session_file" ]] || [[ ! -f "$session_file" ]]; then
        echo "unknown"
        return
    fi

    # Extract usage from last message with usage data
    local usage_json
    usage_json=$(grep '"usage"' "$session_file" 2>/dev/null | tail -1)

    if [[ -z "$usage_json" ]]; then
        echo "unknown"
        return
    fi

    # Calculate total tokens and percentage
    # Context window is 200k for Claude
    local context_size=200000

    if command -v jq &>/dev/null; then
        # Use jq for accurate parsing
        local pct
        pct=$(echo "$usage_json" | jq -r '
            .message.usage // . |
            ((.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0) + (.input_tokens // 0)) as $total |
            ($total * 100 / 200000) | floor
        ' 2>/dev/null)

        if [[ "$pct" =~ ^[0-9]+$ ]]; then
            echo "$pct"
            return
        fi
    fi

    # Fallback: grep-based extraction
    local cache_read cache_create input_tok
    cache_read=$(echo "$usage_json" | grep -o '"cache_read_input_tokens":[0-9]*' | grep -o '[0-9]*' | head -1)
    cache_create=$(echo "$usage_json" | grep -o '"cache_creation_input_tokens":[0-9]*' | grep -o '[0-9]*' | head -1)
    input_tok=$(echo "$usage_json" | grep -o '"input_tokens":[0-9]*' | grep -o '[0-9]*' | head -1)

    cache_read=${cache_read:-0}
    cache_create=${cache_create:-0}
    input_tok=${input_tok:-0}

    local total=$((cache_read + cache_create + input_tok))
    local pct=$((total * 100 / context_size))

    echo "$pct"
}

# Get warning tier based on actual usage
get_context_tier() {
    local pct
    pct=$(get_context_usage)

    if [[ "$pct" == "unknown" ]]; then
        echo "unknown"
        return
    fi

    if [[ "$pct" -ge 85 ]]; then
        echo "critical"
    elif [[ "$pct" -ge 70 ]]; then
        echo "warning"
    elif [[ "$pct" -ge 50 ]]; then
        echo "info"
    else
        echo "safe"
    fi
}

# If run directly (not sourced), output usage
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    pct=$(get_context_usage)
    tier=$(get_context_tier)
    echo "Context Usage: ${pct}%"
    echo "Tier: ${tier}"
fi
