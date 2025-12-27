# Shared Infrastructure Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Create the foundational shell library, directory structure, and artifact index schema that all other context management features depend on.

**Architecture:** A layered infrastructure with shell utilities for hook development, standardized directory layout for runtime state, and SQLite+FTS5 schema for semantic search of all execution artifacts.

**Tech Stack:**
- Bash 4.0+ (shell library)
- SQLite3 with FTS5 (artifact index)
- POSIX-compliant utilities (sed, awk, printf)
- jq (optional, for enhanced JSON escaping)

**Global Prerequisites:**
- Environment: macOS/Linux, Bash 4.0+
- Tools: `bash --version` (4.0+), `sqlite3 --version` (3.24+ for FTS5)
- Access: Write access to `default/` plugin directory
- State: On `main` branch, clean working tree

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
bash --version | head -1   # Expected: version 4.0+ (macOS may show 3.x, that's OK)
sqlite3 --version          # Expected: 3.24+ (3.x with FTS5 support)
git status                 # Expected: clean working tree
ls -la shared/lib/         # Expected: json-escape.sh exists
ls default/lib/ 2>/dev/null || echo "Not exists (OK)"  # Expected: "Not exists (OK)"
```

---

## Task Summary

| Task | Description | Effort |
|------|-------------|--------|
| 1 | Create lib directory structure | 2 min |
| 2 | Create json-escape.sh with RFC 8259 compliance | 5 min |
| 3 | Create hook-utils.sh with stdin/JSON patterns | 5 min |
| 4 | Create context-check.sh with usage estimation | 5 min |
| 5 | Verify shell library works | 3 min |
| 6 | Create .ring directory structure | 3 min |
| 7 | Create artifact_schema.sql | 5 min |
| 8 | Initialize artifact index database | 3 min |
| 9 | Create .gitignore for runtime directories | 2 min |
| 10 | Run code review | 5 min |
| 11 | Final verification and commit | 3 min |

**Total estimated time:** 41 minutes

---

### Task 1: Create lib directory structure

**Files:**
- Create: `default/lib/shell/` (directory)
- Create: `default/lib/artifact-index/` (directory)

**Prerequisites:**
- Current directory: `/Users/fredamaral/repos/lerianstudio/ring`
- `default/` directory must exist

**Step 1: Create the shell library directory**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell
```

**Expected output:** (no output on success)

**Step 2: Create the artifact-index directory**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index
```

**Expected output:** (no output on success)

**Step 3: Verify directory structure**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/
```

**Expected output:**
```
drwxr-xr-x  - user  date  artifact-index
drwxr-xr-x  - user  date  shell
```

**If Task Fails:**
1. **Permission denied:** Check write permissions with `ls -la default/`
2. **Directory already exists:** Safe to continue (mkdir -p is idempotent)
3. **Can't recover:** Document error, return to human partner

---

### Task 2: Create json-escape.sh with RFC 8259 compliance

**Files:**
- Create: `default/lib/shell/json-escape.sh`

**Prerequisites:**
- `default/lib/shell/` directory exists (Task 1)

**Step 1: Write the json-escape.sh file**

Create file at `default/lib/shell/json-escape.sh`:

```bash
#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# RFC 8259 compliant JSON string escaping for Ring hooks
#
# Usage:
#   source /path/to/json-escape.sh
#   escaped=$(json_escape "string with \"quotes\" and
#   newlines")
#
# Handles: backslash, quotes, tabs, carriage returns, newlines, form feeds
# Prefers jq when available for 100% compliance; falls back to awk for portability

set -euo pipefail

# JSON escape a string per RFC 8259
# Args: $1 - string to escape
# Returns: escaped string via stdout
json_escape() {
    local input="${1:-}"

    # Empty string handling
    if [[ -z "$input" ]]; then
        return 0
    fi

    # Prefer jq for 100% RFC 8259 compliance
    if command -v jq &>/dev/null; then
        # jq -Rs reads raw input, outputs as JSON string
        # sed strips the surrounding quotes that jq adds
        printf '%s' "$input" | jq -Rs . | sed 's/^"//;s/"$//'
        return 0
    fi

    # Fallback: awk-based escaping (more portable than sed for multiline)
    # Handles all JSON control characters per RFC 8259
    printf '%s' "$input" | awk '
    BEGIN {
        ORS = ""
    }
    {
        for (i = 1; i <= length($0); i++) {
            c = substr($0, i, 1)
            if (c == "\\") printf "\\\\"
            else if (c == "\"") printf "\\\""
            else if (c == "\t") printf "\\t"
            else if (c == "\r") printf "\\r"
            else if (c == "\b") printf "\\b"
            else if (c == "\f") printf "\\f"
            else printf "%s", c
        }
        # Add escaped newline between lines (except last)
        if (NR > 1 || getline > 0) {
            printf "\\n"
        }
    }
    '
}

# JSON escape for use in JSON string values (adds quotes)
# Args: $1 - string to escape
# Returns: "escaped string" with surrounding quotes
json_string() {
    local escaped
    escaped=$(json_escape "${1:-}")
    printf '"%s"' "$escaped"
}

# Export for subshells
export -f json_escape 2>/dev/null || true
export -f json_string 2>/dev/null || true
```

**Step 2: Make executable**

Run:
```bash
chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/json-escape.sh
```

**Expected output:** (no output on success)

**Step 3: Verify file exists and is executable**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/json-escape.sh
```

**Expected output:**
```
-rwxr-xr-x  1 user  group  size  date  json-escape.sh
```

**If Task Fails:**
1. **File not created:** Check directory exists with `ls -la default/lib/shell/`
2. **chmod fails:** Check file ownership with `ls -la`
3. **Can't recover:** Document error, return to human partner

---

### Task 3: Create hook-utils.sh with stdin/JSON patterns

**Files:**
- Create: `default/lib/shell/hook-utils.sh`

**Prerequisites:**
- `default/lib/shell/` directory exists (Task 1)
- `json-escape.sh` exists (Task 2)

**Step 1: Write the hook-utils.sh file**

Create file at `default/lib/shell/hook-utils.sh`:

```bash
#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# Common hook utilities for Ring hooks
#
# Usage:
#   source /path/to/hook-utils.sh
#   input=$(read_hook_stdin)
#   output_hook_result "continue" "Optional message"
#
# Provides:
#   - read_hook_stdin: Read JSON from stdin (Claude Code hook input)
#   - output_hook_result: Output valid hook JSON response
#   - output_hook_context: Output hook response with additionalContext
#   - get_json_field: Extract field from JSON using jq or grep fallback
#   - get_project_root: Get project root directory
#   - get_ring_state_dir: Get .ring/state directory path

set -euo pipefail

# Determine script location and source dependencies
HOOK_UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source json-escape if not already sourced
if ! declare -f json_escape &>/dev/null; then
    # shellcheck source=json-escape.sh
    source "${HOOK_UTILS_DIR}/json-escape.sh"
fi

# Read hook input from stdin
# Returns: JSON string via stdout
read_hook_stdin() {
    local input=""
    local timeout_seconds="${1:-5}"

    # Read all stdin with timeout
    if command -v timeout &>/dev/null; then
        input=$(timeout "${timeout_seconds}" cat 2>/dev/null || true)
    else
        # macOS fallback: read with built-in timeout
        input=$(cat 2>/dev/null || true)
    fi

    printf '%s' "$input"
}

# Extract a field from JSON input
# Args: $1 - JSON string, $2 - field name (top-level only)
# Returns: field value via stdout
get_json_field() {
    local json="${1:-}"
    local field="${2:-}"

    if [[ -z "$json" ]] || [[ -z "$field" ]]; then
        return 1
    fi

    # Prefer jq for reliable parsing
    if command -v jq &>/dev/null; then
        printf '%s' "$json" | jq -r ".${field} // empty" 2>/dev/null
        return 0
    fi

    # Fallback: grep-based extraction (simple cases only)
    # Matches: "field": "value" or "field": value
    printf '%s' "$json" | grep -o "\"${field}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | \
        sed 's/.*:[[:space:]]*"\([^"]*\)"/\1/' | head -1
}

# Get project root directory
# Uses CLAUDE_PROJECT_DIR if set, otherwise pwd
get_project_root() {
    local project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    printf '%s' "$project_dir"
}

# Get .ring state directory path (creates if needed)
# Returns: path to .ring/state directory
get_ring_state_dir() {
    local project_root
    project_root=$(get_project_root)
    local state_dir="${project_root}/.ring/state"

    # Create if it doesn't exist
    if [[ ! -d "$state_dir" ]]; then
        mkdir -p "$state_dir"
    fi

    printf '%s' "$state_dir"
}

# Get .ring cache directory path (creates if needed)
# Returns: path to .ring/cache directory
get_ring_cache_dir() {
    local project_root
    project_root=$(get_project_root)
    local cache_dir="${project_root}/.ring/cache"

    # Create if it doesn't exist
    if [[ ! -d "$cache_dir" ]]; then
        mkdir -p "$cache_dir"
    fi

    printf '%s' "$cache_dir"
}

# Get .ring ledgers directory path (creates if needed)
# Returns: path to .ring/ledgers directory
get_ring_ledgers_dir() {
    local project_root
    project_root=$(get_project_root)
    local ledgers_dir="${project_root}/.ring/ledgers"

    # Create if it doesn't exist
    if [[ ! -d "$ledgers_dir" ]]; then
        mkdir -p "$ledgers_dir"
    fi

    printf '%s' "$ledgers_dir"
}

# Output a basic hook result
# Args: $1 - result ("continue" or "block"), $2 - message (optional)
output_hook_result() {
    local result="${1:-continue}"
    local message="${2:-}"

    if [[ -n "$message" ]]; then
        local escaped_message
        escaped_message=$(json_escape "$message")
        cat <<EOF
{
  "result": "${result}",
  "message": "${escaped_message}"
}
EOF
    else
        cat <<EOF
{
  "result": "${result}"
}
EOF
    fi
}

# Output a hook response with additionalContext
# Args: $1 - hook event name, $2 - additional context string
output_hook_context() {
    local event_name="${1:-SessionStart}"
    local context="${2:-}"

    local escaped_context
    escaped_context=$(json_escape "$context")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "${event_name}",
    "additionalContext": "${escaped_context}"
  }
}
EOF
}

# Output an empty hook response (no-op)
# Args: $1 - hook event name (optional)
output_hook_empty() {
    local event_name="${1:-}"

    if [[ -n "$event_name" ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "${event_name}"
  }
}
EOF
    else
        echo '{}'
    fi
}

# Export functions for subshells
export -f read_hook_stdin 2>/dev/null || true
export -f get_json_field 2>/dev/null || true
export -f get_project_root 2>/dev/null || true
export -f get_ring_state_dir 2>/dev/null || true
export -f get_ring_cache_dir 2>/dev/null || true
export -f get_ring_ledgers_dir 2>/dev/null || true
export -f output_hook_result 2>/dev/null || true
export -f output_hook_context 2>/dev/null || true
export -f output_hook_empty 2>/dev/null || true
```

**Step 2: Make executable**

Run:
```bash
chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/hook-utils.sh
```

**Expected output:** (no output on success)

**Step 3: Verify file exists and is executable**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/hook-utils.sh
```

**Expected output:**
```
-rwxr-xr-x  1 user  group  size  date  hook-utils.sh
```

**If Task Fails:**
1. **File not created:** Check directory exists
2. **Syntax errors:** Run `bash -n hook-utils.sh` to validate syntax
3. **Can't recover:** Document error, return to human partner

---

### Task 4: Create context-check.sh with usage estimation

**Files:**
- Create: `default/lib/shell/context-check.sh`

**Prerequisites:**
- `default/lib/shell/` directory exists (Task 1)
- `hook-utils.sh` exists (Task 3)

**Step 1: Write the context-check.sh file**

Create file at `default/lib/shell/context-check.sh`:

```bash
#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# Context usage estimation utilities for Ring hooks
#
# Usage:
#   source /path/to/context-check.sh
#   percentage=$(estimate_context_usage)
#   warning=$(get_context_warning "$percentage")
#
# Context estimation approach:
#   - Claude Code's context window is ~200K tokens
#   - We estimate usage from session state files
#   - Conservative estimates to warn early

set -euo pipefail

# Determine script location and source dependencies
CONTEXT_CHECK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source hook-utils if not already sourced
if ! declare -f get_ring_state_dir &>/dev/null; then
    # shellcheck source=hook-utils.sh
    source "${CONTEXT_CHECK_DIR}/hook-utils.sh"
fi

# Approximate context window size (tokens)
# Claude's actual limit is ~200K, we use conservative estimate
readonly CONTEXT_WINDOW_TOKENS=200000

# Warning thresholds
readonly THRESHOLD_INFO=50
readonly THRESHOLD_WARNING=70
readonly THRESHOLD_CRITICAL=85

# Estimate context usage percentage
# Returns: integer 0-100 representing estimated usage percentage
estimate_context_usage() {
    local state_dir
    state_dir=$(get_ring_state_dir)
    local usage_file="${state_dir}/context-usage.json"

    # Check if context-usage.json exists and has recent data
    if [[ -f "$usage_file" ]]; then
        local estimated
        estimated=$(get_json_field "$(cat "$usage_file")" "estimated_percentage" 2>/dev/null || echo "")
        if [[ -n "$estimated" ]] && [[ "$estimated" =~ ^[0-9]+$ ]]; then
            printf '%s' "$estimated"
            return 0
        fi
    fi

    # Fallback: estimate from conversation turn count in state file
    local session_file="${state_dir}/current-session.json"
    if [[ -f "$session_file" ]]; then
        local turns
        turns=$(get_json_field "$(cat "$session_file")" "turn_count" 2>/dev/null || echo "0")

        # Rough estimate: ~2000 tokens per turn average
        # 200K context / 2000 tokens = 100 turns for full context
        if [[ "$turns" =~ ^[0-9]+$ ]]; then
            local percentage=$((turns * 100 / 100))  # turns / 100 max turns * 100%
            if [[ $percentage -gt 100 ]]; then
                percentage=100
            fi
            printf '%s' "$percentage"
            return 0
        fi
    fi

    # No data available, return 0 (unknown)
    printf '0'
}

# Update context usage estimate
# Args: $1 - estimated percentage (0-100)
update_context_usage() {
    local percentage="${1:-0}"
    local state_dir
    state_dir=$(get_ring_state_dir)
    local usage_file="${state_dir}/context-usage.json"

    # Get current timestamp
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$usage_file" <<EOF
{
  "estimated_percentage": ${percentage},
  "updated_at": "${timestamp}",
  "threshold_info": ${THRESHOLD_INFO},
  "threshold_warning": ${THRESHOLD_WARNING},
  "threshold_critical": ${THRESHOLD_CRITICAL}
}
EOF
}

# Increment turn count in session state
increment_turn_count() {
    local state_dir
    state_dir=$(get_ring_state_dir)
    local session_file="${state_dir}/current-session.json"

    local turn_count=0
    if [[ -f "$session_file" ]]; then
        turn_count=$(get_json_field "$(cat "$session_file")" "turn_count" 2>/dev/null || echo "0")
        if ! [[ "$turn_count" =~ ^[0-9]+$ ]]; then
            turn_count=0
        fi
    fi

    turn_count=$((turn_count + 1))

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$session_file" <<EOF
{
  "turn_count": ${turn_count},
  "updated_at": "${timestamp}"
}
EOF

    printf '%s' "$turn_count"
}

# Reset turn count (call on session start)
reset_turn_count() {
    local state_dir
    state_dir=$(get_ring_state_dir)
    local session_file="${state_dir}/current-session.json"

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$session_file" <<EOF
{
  "turn_count": 0,
  "started_at": "${timestamp}",
  "updated_at": "${timestamp}"
}
EOF
}

# Get context warning message for a given percentage
# Args: $1 - percentage (0-100)
# Returns: warning message or empty string
get_context_warning() {
    local percentage="${1:-0}"

    if [[ $percentage -ge $THRESHOLD_CRITICAL ]]; then
        printf 'CRITICAL: Context at %d%%. MUST run /clear with ledger save NOW or risk losing work.' "$percentage"
    elif [[ $percentage -ge $THRESHOLD_WARNING ]]; then
        printf 'WARNING: Context at %d%%. Recommend running /clear with ledger save soon.' "$percentage"
    elif [[ $percentage -ge $THRESHOLD_INFO ]]; then
        printf 'INFO: Context at %d%%. Consider summarizing or preparing ledger.' "$percentage"
    else
        # No warning needed
        printf ''
    fi
}

# Get warning severity level
# Args: $1 - percentage (0-100)
# Returns: "critical", "warning", "info", or "ok"
get_warning_level() {
    local percentage="${1:-0}"

    if [[ $percentage -ge $THRESHOLD_CRITICAL ]]; then
        printf 'critical'
    elif [[ $percentage -ge $THRESHOLD_WARNING ]]; then
        printf 'warning'
    elif [[ $percentage -ge $THRESHOLD_INFO ]]; then
        printf 'info'
    else
        printf 'ok'
    fi
}

# Export functions for subshells
export -f estimate_context_usage 2>/dev/null || true
export -f update_context_usage 2>/dev/null || true
export -f increment_turn_count 2>/dev/null || true
export -f reset_turn_count 2>/dev/null || true
export -f get_context_warning 2>/dev/null || true
export -f get_warning_level 2>/dev/null || true
```

**Step 2: Make executable**

Run:
```bash
chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/context-check.sh
```

**Expected output:** (no output on success)

**Step 3: Verify file exists and is executable**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/context-check.sh
```

**Expected output:**
```
-rwxr-xr-x  1 user  group  size  date  context-check.sh
```

**If Task Fails:**
1. **File not created:** Check directory exists
2. **Syntax errors:** Run `bash -n context-check.sh` to validate
3. **Can't recover:** Document error, return to human partner

---

### Task 5: Verify shell library works

**Files:**
- Test: `default/lib/shell/json-escape.sh`
- Test: `default/lib/shell/hook-utils.sh`
- Test: `default/lib/shell/context-check.sh`

**Prerequisites:**
- All shell library files created (Tasks 2-4)

**Step 1: Validate syntax of all shell files**

Run:
```bash
bash -n /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/json-escape.sh && \
bash -n /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/hook-utils.sh && \
bash -n /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/context-check.sh && \
echo "All syntax valid"
```

**Expected output:**
```
All syntax valid
```

**Step 2: Test json_escape function**

Run:
```bash
source /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/json-escape.sh && \
result=$(json_escape 'Test "quotes" and
newlines') && \
echo "Escaped: $result"
```

**Expected output:**
```
Escaped: Test \"quotes\" and\nnewlines
```

**Step 3: Test hook-utils functions**

Run:
```bash
source /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/hook-utils.sh && \
output_hook_result "continue" "Test message"
```

**Expected output:**
```json
{
  "result": "continue",
  "message": "Test message"
}
```

**Step 4: Test context-check functions**

Run:
```bash
export CLAUDE_PROJECT_DIR="/tmp/ring-test" && \
mkdir -p /tmp/ring-test && \
source /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/context-check.sh && \
warning=$(get_context_warning 75) && \
echo "Warning at 75%: $warning" && \
rm -rf /tmp/ring-test
```

**Expected output:**
```
Warning at 75%: WARNING: Context at 75%. Recommend running /clear with ledger save soon.
```

**If Task Fails:**
1. **Syntax errors:** Fix the specific file indicated
2. **Function not found:** Check source path is correct
3. **Wrong output:** Review the function implementation
4. **Can't recover:** Document error, return to human partner

---

### Task 6: Create .ring directory structure

**Files:**
- Create: `.ring/state/` (directory)
- Create: `.ring/cache/` (directory)
- Create: `.ring/cache/artifact-index/` (directory)
- Create: `.ring/cache/learnings/` (directory)
- Create: `.ring/ledgers/` (directory)

**Prerequisites:**
- Clean working tree

**Step 1: Create all .ring subdirectories**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/.ring/state && \
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index && \
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/learnings && \
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers && \
echo "Directories created"
```

**Expected output:**
```
Directories created
```

**Step 2: Create .gitkeep files to preserve empty directories**

Run:
```bash
touch /Users/fredamaral/repos/lerianstudio/ring/.ring/state/.gitkeep && \
touch /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/.gitkeep && \
touch /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/learnings/.gitkeep && \
touch /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/.gitkeep && \
echo "Gitkeep files created"
```

**Expected output:**
```
Gitkeep files created
```

**Step 3: Verify directory structure**

Run:
```bash
find /Users/fredamaral/repos/lerianstudio/ring/.ring -type d | sort
```

**Expected output:**
```
/Users/fredamaral/repos/lerianstudio/ring/.ring
/Users/fredamaral/repos/lerianstudio/ring/.ring/cache
/Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index
/Users/fredamaral/repos/lerianstudio/ring/.ring/cache/learnings
/Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers
/Users/fredamaral/repos/lerianstudio/ring/.ring/state
```

**If Task Fails:**
1. **Permission denied:** Check parent directory permissions
2. **Directory already exists:** Safe to continue (mkdir -p is idempotent)
3. **Can't recover:** Document error, return to human partner

---

### Task 7: Create artifact_schema.sql

**Files:**
- Create: `default/lib/artifact-index/artifact_schema.sql`

**Prerequisites:**
- `default/lib/artifact-index/` directory exists (Task 1)

**Step 1: Write the artifact_schema.sql file**

Create file at `default/lib/artifact-index/artifact_schema.sql`:

```sql
-- Ring Artifact Index Schema
-- Database location: $PROJECT_ROOT/.ring/cache/artifact-index/context.db
--
-- This schema supports indexing and querying Ring session artifacts:
-- - Handoffs (completed tasks with post-mortems)
-- - Plans (design documents)
-- - Continuity ledgers (session state snapshots)
-- - Queries (compound learning from Q&A)
--
-- FTS5 is used for full-text search with porter stemming.
-- Triggers keep FTS5 indexes in sync with main tables.
-- Adapted from Continuous-Claude-v2 for Ring plugin architecture.

-- Enable WAL mode for better concurrent read performance
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- ============================================================================
-- MAIN TABLES
-- ============================================================================

-- Handoffs (completed tasks with post-mortems)
CREATE TABLE IF NOT EXISTS handoffs (
    id TEXT PRIMARY KEY,
    session_name TEXT NOT NULL,
    task_number INTEGER,
    file_path TEXT NOT NULL,

    -- Core content
    task_summary TEXT,
    what_worked TEXT,
    what_failed TEXT,
    key_decisions TEXT,
    files_modified TEXT,  -- JSON array

    -- Outcome (from user annotation)
    outcome TEXT CHECK(outcome IN ('SUCCEEDED', 'PARTIAL_PLUS', 'PARTIAL_MINUS', 'FAILED', 'UNKNOWN')),
    outcome_notes TEXT,
    confidence TEXT CHECK(confidence IN ('HIGH', 'INFERRED')) DEFAULT 'INFERRED',

    -- Trace correlation (for debugging and analysis)
    session_id TEXT,         -- Claude session ID
    trace_id TEXT,           -- Optional external trace ID

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plans (design documents)
CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    session_name TEXT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,

    -- Content
    overview TEXT,
    approach TEXT,
    phases TEXT,  -- JSON array
    constraints TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Continuity snapshots (session state at key moments)
CREATE TABLE IF NOT EXISTS continuity (
    id TEXT PRIMARY KEY,
    session_name TEXT NOT NULL,

    -- State
    goal TEXT,
    state_done TEXT,  -- JSON array
    state_now TEXT,
    state_next TEXT,
    key_learnings TEXT,
    key_decisions TEXT,

    -- Context
    snapshot_reason TEXT CHECK(snapshot_reason IN ('phase_complete', 'session_end', 'milestone', 'manual', 'clear', 'compact')),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Queries (compound learning from Q&A)
CREATE TABLE IF NOT EXISTS queries (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,

    -- Matches
    handoffs_matched TEXT,  -- JSON array of IDs
    plans_matched TEXT,
    continuity_matched TEXT,

    -- Feedback
    was_helpful BOOLEAN,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learnings (extracted patterns from successful/failed sessions)
CREATE TABLE IF NOT EXISTS learnings (
    id TEXT PRIMARY KEY,
    pattern_type TEXT CHECK(pattern_type IN ('success', 'failure', 'efficiency', 'antipattern')),

    -- Content
    description TEXT NOT NULL,
    context TEXT,  -- When this applies
    recommendation TEXT,  -- What to do

    -- Source tracking
    source_handoffs TEXT,  -- JSON array of handoff IDs
    occurrence_count INTEGER DEFAULT 1,

    -- Status
    promoted_to TEXT,  -- 'rule', 'skill', 'hook', or NULL
    promoted_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FTS5 INDEXES (Full-Text Search)
-- ============================================================================

-- FTS5 indexes for full-text search
-- Using porter tokenizer for stemming + prefix index for code identifiers
CREATE VIRTUAL TABLE IF NOT EXISTS handoffs_fts USING fts5(
    task_summary, what_worked, what_failed, key_decisions, files_modified,
    content='handoffs', content_rowid='rowid',
    tokenize='porter ascii',
    prefix='2 3'
);

CREATE VIRTUAL TABLE IF NOT EXISTS plans_fts USING fts5(
    title, overview, approach, phases, constraints,
    content='plans', content_rowid='rowid',
    tokenize='porter ascii',
    prefix='2 3'
);

CREATE VIRTUAL TABLE IF NOT EXISTS continuity_fts USING fts5(
    goal, key_learnings, key_decisions, state_now,
    content='continuity', content_rowid='rowid',
    tokenize='porter ascii'
);

CREATE VIRTUAL TABLE IF NOT EXISTS queries_fts USING fts5(
    question, answer,
    content='queries', content_rowid='rowid',
    tokenize='porter ascii'
);

CREATE VIRTUAL TABLE IF NOT EXISTS learnings_fts USING fts5(
    description, context, recommendation,
    content='learnings', content_rowid='rowid',
    tokenize='porter ascii'
);

-- ============================================================================
-- SYNC TRIGGERS (Keep FTS5 in sync with main tables)
-- ============================================================================

-- HANDOFFS triggers
CREATE TRIGGER IF NOT EXISTS handoffs_ai AFTER INSERT ON handoffs BEGIN
    INSERT INTO handoffs_fts(rowid, task_summary, what_worked, what_failed, key_decisions, files_modified)
    VALUES (NEW.rowid, NEW.task_summary, NEW.what_worked, NEW.what_failed, NEW.key_decisions, NEW.files_modified);
END;

CREATE TRIGGER IF NOT EXISTS handoffs_ad AFTER DELETE ON handoffs BEGIN
    INSERT INTO handoffs_fts(handoffs_fts, rowid, task_summary, what_worked, what_failed, key_decisions, files_modified)
    VALUES('delete', OLD.rowid, OLD.task_summary, OLD.what_worked, OLD.what_failed, OLD.key_decisions, OLD.files_modified);
END;

CREATE TRIGGER IF NOT EXISTS handoffs_au AFTER UPDATE ON handoffs BEGIN
    INSERT INTO handoffs_fts(handoffs_fts, rowid, task_summary, what_worked, what_failed, key_decisions, files_modified)
    VALUES('delete', OLD.rowid, OLD.task_summary, OLD.what_worked, OLD.what_failed, OLD.key_decisions, OLD.files_modified);
    INSERT INTO handoffs_fts(rowid, task_summary, what_worked, what_failed, key_decisions, files_modified)
    VALUES (NEW.rowid, NEW.task_summary, NEW.what_worked, NEW.what_failed, NEW.key_decisions, NEW.files_modified);
END;

-- PLANS triggers
CREATE TRIGGER IF NOT EXISTS plans_ai AFTER INSERT ON plans BEGIN
    INSERT INTO plans_fts(rowid, title, overview, approach, phases, constraints)
    VALUES (NEW.rowid, NEW.title, NEW.overview, NEW.approach, NEW.phases, NEW.constraints);
END;

CREATE TRIGGER IF NOT EXISTS plans_ad AFTER DELETE ON plans BEGIN
    INSERT INTO plans_fts(plans_fts, rowid, title, overview, approach, phases, constraints)
    VALUES('delete', OLD.rowid, OLD.title, OLD.overview, OLD.approach, OLD.phases, OLD.constraints);
END;

CREATE TRIGGER IF NOT EXISTS plans_au AFTER UPDATE ON plans BEGIN
    INSERT INTO plans_fts(plans_fts, rowid, title, overview, approach, phases, constraints)
    VALUES('delete', OLD.rowid, OLD.title, OLD.overview, OLD.approach, OLD.phases, OLD.constraints);
    INSERT INTO plans_fts(rowid, title, overview, approach, phases, constraints)
    VALUES (NEW.rowid, NEW.title, NEW.overview, NEW.approach, NEW.phases, NEW.constraints);
END;

-- CONTINUITY triggers
CREATE TRIGGER IF NOT EXISTS continuity_ai AFTER INSERT ON continuity BEGIN
    INSERT INTO continuity_fts(rowid, goal, key_learnings, key_decisions, state_now)
    VALUES (NEW.rowid, NEW.goal, NEW.key_learnings, NEW.key_decisions, NEW.state_now);
END;

CREATE TRIGGER IF NOT EXISTS continuity_ad AFTER DELETE ON continuity BEGIN
    INSERT INTO continuity_fts(continuity_fts, rowid, goal, key_learnings, key_decisions, state_now)
    VALUES('delete', OLD.rowid, OLD.goal, OLD.key_learnings, OLD.key_decisions, OLD.state_now);
END;

CREATE TRIGGER IF NOT EXISTS continuity_au AFTER UPDATE ON continuity BEGIN
    INSERT INTO continuity_fts(continuity_fts, rowid, goal, key_learnings, key_decisions, state_now)
    VALUES('delete', OLD.rowid, OLD.goal, OLD.key_learnings, OLD.key_decisions, OLD.state_now);
    INSERT INTO continuity_fts(rowid, goal, key_learnings, key_decisions, state_now)
    VALUES (NEW.rowid, NEW.goal, NEW.key_learnings, NEW.key_decisions, NEW.state_now);
END;

-- QUERIES triggers
CREATE TRIGGER IF NOT EXISTS queries_ai AFTER INSERT ON queries BEGIN
    INSERT INTO queries_fts(rowid, question, answer)
    VALUES (NEW.rowid, NEW.question, NEW.answer);
END;

CREATE TRIGGER IF NOT EXISTS queries_ad AFTER DELETE ON queries BEGIN
    INSERT INTO queries_fts(queries_fts, rowid, question, answer)
    VALUES('delete', OLD.rowid, OLD.question, OLD.answer);
END;

CREATE TRIGGER IF NOT EXISTS queries_au AFTER UPDATE ON queries BEGIN
    INSERT INTO queries_fts(queries_fts, rowid, question, answer)
    VALUES('delete', OLD.rowid, OLD.question, OLD.answer);
    INSERT INTO queries_fts(rowid, question, answer)
    VALUES (NEW.rowid, NEW.question, NEW.answer);
END;

-- LEARNINGS triggers
CREATE TRIGGER IF NOT EXISTS learnings_ai AFTER INSERT ON learnings BEGIN
    INSERT INTO learnings_fts(rowid, description, context, recommendation)
    VALUES (NEW.rowid, NEW.description, NEW.context, NEW.recommendation);
END;

CREATE TRIGGER IF NOT EXISTS learnings_ad AFTER DELETE ON learnings BEGIN
    INSERT INTO learnings_fts(learnings_fts, rowid, description, context, recommendation)
    VALUES('delete', OLD.rowid, OLD.description, OLD.context, OLD.recommendation);
END;

CREATE TRIGGER IF NOT EXISTS learnings_au AFTER UPDATE ON learnings BEGIN
    INSERT INTO learnings_fts(learnings_fts, rowid, description, context, recommendation)
    VALUES('delete', OLD.rowid, OLD.description, OLD.context, OLD.recommendation);
    INSERT INTO learnings_fts(rowid, description, context, recommendation)
    VALUES (NEW.rowid, NEW.description, NEW.context, NEW.recommendation);
END;

-- ============================================================================
-- INDEXES (Performance optimization)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_handoffs_session ON handoffs(session_name);
CREATE INDEX IF NOT EXISTS idx_handoffs_outcome ON handoffs(outcome);
CREATE INDEX IF NOT EXISTS idx_handoffs_created ON handoffs(created_at);

CREATE INDEX IF NOT EXISTS idx_plans_session ON plans(session_name);
CREATE INDEX IF NOT EXISTS idx_plans_created ON plans(created_at);

CREATE INDEX IF NOT EXISTS idx_continuity_session ON continuity(session_name);
CREATE INDEX IF NOT EXISTS idx_continuity_reason ON continuity(snapshot_reason);

CREATE INDEX IF NOT EXISTS idx_learnings_type ON learnings(pattern_type);
CREATE INDEX IF NOT EXISTS idx_learnings_promoted ON learnings(promoted_to);

-- ============================================================================
-- VIEWS (Convenience queries)
-- ============================================================================

-- Recent handoffs with outcomes
CREATE VIEW IF NOT EXISTS recent_handoffs AS
SELECT
    id,
    session_name,
    task_summary,
    outcome,
    created_at
FROM handoffs
ORDER BY created_at DESC
LIMIT 100;

-- Success patterns (for compound learning)
CREATE VIEW IF NOT EXISTS success_patterns AS
SELECT
    h.task_summary,
    h.what_worked,
    h.key_decisions,
    COUNT(*) as occurrence_count
FROM handoffs h
WHERE h.outcome IN ('SUCCEEDED', 'PARTIAL_PLUS')
GROUP BY h.what_worked
HAVING COUNT(*) >= 2
ORDER BY occurrence_count DESC;

-- Failure patterns (for compound learning)
CREATE VIEW IF NOT EXISTS failure_patterns AS
SELECT
    h.task_summary,
    h.what_failed,
    h.outcome_notes,
    COUNT(*) as occurrence_count
FROM handoffs h
WHERE h.outcome IN ('FAILED', 'PARTIAL_MINUS')
GROUP BY h.what_failed
HAVING COUNT(*) >= 2
ORDER BY occurrence_count DESC;

-- Unpromoted learnings ready for review
CREATE VIEW IF NOT EXISTS pending_learnings AS
SELECT *
FROM learnings
WHERE promoted_to IS NULL
  AND occurrence_count >= 3
ORDER BY occurrence_count DESC, created_at DESC;
```

**Step 2: Verify file was created**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_schema.sql
```

**Expected output:**
```
-rw-r--r--  1 user  group  size  date  artifact_schema.sql
```

**Step 3: Verify SQL syntax**

Run:
```bash
sqlite3 :memory: < /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_schema.sql && echo "SQL syntax valid"
```

**Expected output:**
```
SQL syntax valid
```

**If Task Fails:**
1. **File not created:** Check directory exists
2. **SQL syntax error:** SQLite will show the line number with the error
3. **FTS5 not available:** Check SQLite version is 3.24+
4. **Can't recover:** Document error, return to human partner

---

### Task 8: Initialize artifact index database

**Files:**
- Create: `.ring/cache/artifact-index/context.db`

**Prerequisites:**
- Schema file exists (Task 7)
- `.ring/cache/artifact-index/` directory exists (Task 6)

**Step 1: Initialize the database with schema**

Run:
```bash
sqlite3 /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db < \
    /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_schema.sql && \
echo "Database initialized"
```

**Expected output:**
```
Database initialized
```

**Step 2: Verify database was created**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db
```

**Expected output:**
```
-rw-r--r--  1 user  group  size  date  context.db
```

**Step 3: Verify tables were created**

Run:
```bash
sqlite3 /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db ".tables"
```

**Expected output:**
```
continuity       handoffs_fts     plans            queries_fts
continuity_fts   learnings        plans_fts        recent_handoffs
failure_patterns learnings_fts    pending_learnings success_patterns
handoffs         queries
```

**Step 4: Verify FTS5 works**

Run:
```bash
sqlite3 /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db \
    "INSERT INTO handoffs (id, session_name, file_path, task_summary) VALUES ('test-1', 'test', '/test', 'Test authentication');" && \
sqlite3 /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db \
    "SELECT * FROM handoffs_fts WHERE handoffs_fts MATCH 'authentication';" && \
sqlite3 /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db \
    "DELETE FROM handoffs WHERE id = 'test-1';" && \
echo "FTS5 working"
```

**Expected output:**
```
Test authentication||||
FTS5 working
```

**If Task Fails:**
1. **Database locked:** Check no other process has it open
2. **FTS5 error:** Verify SQLite version supports FTS5
3. **Permission denied:** Check directory permissions
4. **Can't recover:** Document error, return to human partner

---

### Task 9: Create .gitignore for runtime directories

**Files:**
- Create: `.ring/.gitignore`

**Prerequisites:**
- `.ring/` directory exists (Task 6)

**Step 1: Write the .gitignore file**

Create file at `.ring/.gitignore`:

```gitignore
# Ring runtime state - project-specific, not versioned
# =====================================================
# These files are generated at runtime and should not be committed.
# The .gitkeep files ensure directories exist in version control.

# State files (session-specific)
state/*.json
state/*.log

# Cache files (generated artifacts)
cache/artifact-index/*.db
cache/artifact-index/*.db-wal
cache/artifact-index/*.db-shm
cache/learnings/*.md
cache/learnings/*.json

# Ledger files (session continuity - user may want to keep some)
# Uncomment next line to ignore all ledgers:
# ledgers/*.md

# Keep the directory structure
!.gitkeep
!*/.gitkeep
```

**Step 2: Verify file was created**

Run:
```bash
cat /Users/fredamaral/repos/lerianstudio/ring/.ring/.gitignore
```

**Expected output:** (content of the .gitignore file)

**Step 3: Verify git status shows expected files**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git status --short .ring/
```

**Expected output:**
```
?? .ring/
```
(The entire .ring directory appears as untracked, which is expected since it's new)

**If Task Fails:**
1. **File not created:** Check directory exists
2. **Wrong patterns:** Review gitignore syntax
3. **Can't recover:** Document error, return to human partner

---

### Task 10: Run Code Review

**Prerequisites:**
- All tasks 1-9 complete

**Step 1: Dispatch all 3 reviewers in parallel**

REQUIRED SUB-SKILL: Use requesting-code-review

Dispatch:
- ring-default:code-reviewer
- ring-default:business-logic-reviewer
- ring-default:security-reviewer

All reviewers run simultaneously. Wait for all to complete.

**Step 2: Handle findings by severity (MANDATORY)**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 3 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on [date], severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer] on [date], severity: Cosmetic)`

**Step 3: Proceed only when:**
- Zero Critical/High/Medium issues remain
- All Low issues have TODO(review): comments added
- All Cosmetic issues have FIXME(nitpick): comments added

**If Task Fails:**
1. **Reviewer finds critical issues:** Fix and re-run reviewers
2. **Reviewers disagree:** Escalate to human partner
3. **Can't recover:** Document findings, return to human partner

---

### Task 11: Final verification and commit

**Prerequisites:**
- Code review passed (Task 10)

**Step 1: Verify all files exist**

Run:
```bash
echo "=== Shell Library ===" && \
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/ && \
echo "" && \
echo "=== Artifact Index ===" && \
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/ && \
echo "" && \
echo "=== .ring Directory ===" && \
find /Users/fredamaral/repos/lerianstudio/ring/.ring -type f | sort
```

**Expected output:**
```
=== Shell Library ===
-rwxr-xr-x  1 user  group  size  date  context-check.sh
-rwxr-xr-x  1 user  group  size  date  hook-utils.sh
-rwxr-xr-x  1 user  group  size  date  json-escape.sh

=== Artifact Index ===
-rw-r--r--  1 user  group  size  date  artifact_schema.sql

=== .ring Directory ===
/Users/fredamaral/repos/lerianstudio/ring/.ring/.gitignore
/Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/.gitkeep
/Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db
/Users/fredamaral/repos/lerianstudio/ring/.ring/cache/learnings/.gitkeep
/Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/.gitkeep
/Users/fredamaral/repos/lerianstudio/ring/.ring/state/.gitkeep
```

**Step 2: Run full integration test**

Run:
```bash
# Test complete integration
export CLAUDE_PROJECT_DIR="/Users/fredamaral/repos/lerianstudio/ring"
source /Users/fredamaral/repos/lerianstudio/ring/default/lib/shell/context-check.sh

# Test 1: State directory creation
state_dir=$(get_ring_state_dir)
echo "State dir: $state_dir"

# Test 2: Cache directory creation
cache_dir=$(get_ring_cache_dir)
echo "Cache dir: $cache_dir"

# Test 3: Context warning
warning=$(get_context_warning 72)
echo "Warning at 72%: $warning"

# Test 4: Hook output
output_hook_context "SessionStart" "Test context"

echo "All integration tests passed"
```

**Expected output:**
```
State dir: /Users/fredamaral/repos/lerianstudio/ring/.ring/state
Cache dir: /Users/fredamaral/repos/lerianstudio/ring/.ring/cache
Warning at 72%: WARNING: Context at 72%. Recommend running /clear with ledger save soon.
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Test context"
  }
}
All integration tests passed
```

**Step 3: Stage files for commit**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/lib/ .ring/.gitignore .ring/*/.gitkeep .ring/*/*/.gitkeep && \
git status
```

**Expected output:**
```
Changes to be staged:
  new file:   .ring/.gitignore
  new file:   .ring/cache/artifact-index/.gitkeep
  new file:   .ring/cache/learnings/.gitkeep
  new file:   .ring/ledgers/.gitkeep
  new file:   .ring/state/.gitkeep
  new file:   default/lib/artifact-index/artifact_schema.sql
  new file:   default/lib/shell/context-check.sh
  new file:   default/lib/shell/hook-utils.sh
  new file:   default/lib/shell/json-escape.sh
```

**Step 4: Commit**

REQUIRED SUB-SKILL: Use ring-default:commit

Commit message: "feat(context): add shared infrastructure for context management system"

**If Task Fails:**
1. **Files missing:** Re-run the specific task that creates them
2. **Tests fail:** Debug and fix the specific function
3. **Commit fails:** Check git status for issues
4. **Can't recover:** Document error, return to human partner

---

## Success Criteria

| Criterion | Verification Command |
|-----------|---------------------|
| Shell library files exist and are executable | `ls -la default/lib/shell/` shows 3 .sh files with x permission |
| JSON escaping works | `source default/lib/shell/json-escape.sh && json_escape 'test "quote"'` returns `test \"quote\"` |
| Hook utilities work | `source default/lib/shell/hook-utils.sh && output_hook_result continue` returns valid JSON |
| Context check works | `source default/lib/shell/context-check.sh && get_context_warning 75` returns warning message |
| SQL schema is valid | `sqlite3 :memory: < default/lib/artifact-index/artifact_schema.sql` succeeds |
| Database initialized | `.ring/cache/artifact-index/context.db` exists and has tables |
| FTS5 search works | Query `handoffs_fts MATCH 'test'` executes without error |
| Directory structure exists | `.ring/state/`, `.ring/cache/`, `.ring/ledgers/` all exist |
| .gitignore configured | Runtime files are ignored, .gitkeep files are tracked |

---

## Rollback Plan

If implementation fails and cannot be recovered:

```bash
# Remove all created files and directories
rm -rf /Users/fredamaral/repos/lerianstudio/ring/default/lib/
rm -rf /Users/fredamaral/repos/lerianstudio/ring/.ring/

# Reset any staged changes
git reset HEAD
git checkout -- .
```

---

## Next Steps

After completing this plan:

1. **Update hooks.json** - Register new hooks that use these utilities (Phase 1)
2. **Implement artifact_index.py** - Python script to parse and index artifacts (Phase 1)
3. **Implement artifact_query.py** - Python script for FTS5 queries (Phase 1)
4. **Create continuity-ledger skill** - Use hook-utils for ledger management (Phase 1)

**Reference:** See `docs/plans/2025-12-27-context-management-system.md` Section 4 for dependency graph.
