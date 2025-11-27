#!/usr/bin/env bash
# Enhanced SessionStart hook for ring plugin
# Provides comprehensive skill overview and status

set -euo pipefail

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Auto-update Ring marketplace and plugins silently
update_message=""
if command -v claude &> /dev/null && command -v git &> /dev/null; then
    # Detect marketplace path (common locations)
    marketplace_path=""
    for path in ~/.claude/plugins/marketplaces/ring ~/.config/claude/plugins/marketplaces/ring ~/Library/Application\ Support/Claude/plugins/marketplaces/ring; do
        if [ -d "$path/.git" ]; then
            marketplace_path="$path"
            break
        fi
    done
    
    if [ -n "$marketplace_path" ]; then
        # Get current commit hash before update
        before_hash=$(git -C "$marketplace_path" rev-parse HEAD 2>/dev/null || echo "none")
        
        # Update marketplace silently
        claude plugin marketplace update ring &> /dev/null || true
        
        # Get commit hash after update
        after_hash=$(git -C "$marketplace_path" rev-parse HEAD 2>/dev/null || echo "none")
        
        # If hashes differ, marketplace was actually updated
        if [ "$before_hash" != "$after_hash" ] && [ "$after_hash" != "none" ]; then
            # Update all installed plugins
            claude plugin install ring-default &> /dev/null || true
            claude plugin install ring-dev-team &> /dev/null || true
            claude plugin install ring-finops-team &> /dev/null || true
            claude plugin install ring-pm-team &> /dev/null || true
            claude plugin install ralph-wiggum &> /dev/null || true

            update_message="┌───────────────────────────────────────────────────────────┐\n│  🔄 MARKETPLACE UPDATE - ACTION REQUIRED                  │\n├───────────────────────────────────────────────────────────┤\n│                                                           │\n│  Ring marketplace updated to latest version!              │\n│                                                           │\n│  ⚠ YOU MUST restart your session to load changes:           │\n│    • Type 'clear' in CLI, or                              │\n│    • Restart Claude Code entirely                         │\n│                                                           │\n│  New skills/agents available after restart.               │\n│                                                           │\n└───────────────────────────────────────────────────────────┘"
        fi
    else
        # Marketplace not found, just run updates silently without message
        claude plugin marketplace update ring &> /dev/null || true
        claude plugin install ring-default &> /dev/null || true
        claude plugin install ring-dev-team &> /dev/null || true
        claude plugin install ring-finops-team &> /dev/null || true
        claude plugin install ring-pm-team &> /dev/null || true
        claude plugin install ralph-wiggum &> /dev/null || true
    fi
fi

# Auto-install PyYAML if Python is available but PyYAML is not
if command -v python3 &> /dev/null; then
    if ! python3 -c "import yaml" &> /dev/null 2>&1; then
        # PyYAML not installed, try to install it
        # Try different pip commands (pip3 preferred, then pip)
        for pip_cmd in pip3 pip; do
            if command -v "$pip_cmd" &> /dev/null; then
                # Strategy: Try --user first, then --user --break-system-packages
                # (--break-system-packages only exists in pip 22.1+, needed for PEP 668)
                if "$pip_cmd" install --quiet --user 'PyYAML>=6.0,<7.0' &> /dev/null 2>&1; then
                    echo "PyYAML installed successfully" >&2
                    break
                elif "$pip_cmd" install --quiet --user --break-system-packages 'PyYAML>=6.0,<7.0' &> /dev/null 2>&1; then
                    echo "PyYAML installed successfully (with --break-system-packages)" >&2
                    break
                fi
            fi
        done
        # If all installation attempts fail, generate-skills-ref.py will use fallback parser
        # (No error message needed - the Python script already warns about missing PyYAML)
    fi
fi

# Critical rules that MUST survive compact (injected directly, not via skill file)
# These are the most-violated rules that need to be in immediate context
CRITICAL_RULES='## ⛔ ORCHESTRATOR CRITICAL RULES (SURVIVE COMPACT)

**3-FILE RULE: HARD GATE**
DO NOT read/edit >3 files directly. This is a PROHIBITION.
- >3 files → STOP. Launch specialist agent. DO NOT proceed manually.
- Already touched 3 files? → At gate. Dispatch agent NOW.

**AUTO-TRIGGER PHRASES → MANDATORY AGENT:**
- "fix issues/remaining/findings" → Launch specialist agent
- "apply fixes", "fix the X issues" → Launch specialist agent
- "find where", "search for", "understand how" → Launch Explore agent

**If you think "this task is small" or "I can handle 5 files":**
WRONG. Count > 3 = agent. No exceptions. Task size is irrelevant.

**Full rules:** Use Skill tool with "ring-default:using-ring" if needed.
'

# Generate skills overview with cascading fallback
# Priority: Python+PyYAML > Python regex > Bash fallback > Error message
generate_skills_overview() {
    local python_cmd=""

    # Try python3 first, then python
    for cmd in python3 python; do
        if command -v "$cmd" &> /dev/null; then
            python_cmd="$cmd"
            break
        fi
    done

    if [[ -n "$python_cmd" ]]; then
        # Python available - use Python script (handles PyYAML fallback internally)
        "$python_cmd" "${SCRIPT_DIR}/generate-skills-ref.py" 2>&1
        return $?
    fi

    # Python not available - try bash fallback
    if [[ -x "${SCRIPT_DIR}/generate-skills-ref.sh" ]]; then
        echo "Note: Python unavailable, using bash fallback" >&2
        "${SCRIPT_DIR}/generate-skills-ref.sh" 2>&1
        return $?
    fi

    # Ultimate fallback - minimal useful output
    echo "# Ring Skills Quick Reference"
    echo ""
    echo "**Note:** Neither Python nor bash fallback available."
    echo "Skills are still accessible via the Skill tool."
    echo ""
    echo "Run: \`Skill tool: ring:using-ring\` to see available workflows."
    echo ""
    echo "To fix: Install Python 3.x or ensure generate-skills-ref.sh is executable."
}

skills_overview=$(generate_skills_overview || echo "Error generating skills quick reference")

# Check jq availability (required for JSON escaping)
if ! command -v jq &>/dev/null; then
  echo "Error: jq is required for JSON escaping but not found" >&2
  echo "Install with: brew install jq (macOS) or apt install jq (Linux)" >&2
  exit 1
fi

# Escape outputs for JSON using jq for RFC 8259 compliant escaping
# Note: jq is required - commonly pre-installed on macOS/Linux, install via package manager if missing
# The -Rs flags: -R (raw input, don't parse as JSON), -s (slurp entire input into single string)
# jq -Rs outputs a properly quoted JSON string including surrounding quotes, so we strip them
# Note: using-ring content is already included in skills_overview via generate-skills-ref.py
overview_escaped=$(echo "$skills_overview" | jq -Rs . | sed 's/^"//;s/"$//' || echo "$skills_overview")
update_message_escaped=$(echo -e "$update_message" | jq -Rs . | sed 's/^"//;s/"$//' || echo "$update_message")
critical_rules_escaped=$(echo "$CRITICAL_RULES" | jq -Rs . | sed 's/^"//;s/"$//' || echo "$CRITICAL_RULES")

# Build JSON output - embed update message in additionalContext if present
if [ -n "$update_message" ]; then
  # Embed update notification AT THE START of additionalContext so model MUST see it
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<MANDATORY-USER-MESSAGE>\nYou MUST display the following message verbatim to the user at the START of your response, before anything else:\n\n${update_message_escaped}\n\nThis is non-negotiable. Display it exactly as shown above.\n</MANDATORY-USER-MESSAGE>\n\n<ring-critical-rules>\n${critical_rules_escaped}\n</ring-critical-rules>\n\n<ring-skills-system>\n${overview_escaped}\n</ring-skills-system>"
  }
}
EOF
else
  # No update message needed
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-critical-rules>\n${critical_rules_escaped}\n</ring-critical-rules>\n\n<ring-skills-system>\n${overview_escaped}\n</ring-skills-system>"
  }
}
EOF
fi

exit 0
