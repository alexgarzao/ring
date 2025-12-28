# Context Usage Warnings

Ring monitors your estimated context usage and provides proactive warnings before you hit Claude's context limits.

## How It Works

A UserPromptSubmit hook estimates context usage based on:
- Turn count in current session
- Conservative token-per-turn estimates

Warnings are injected into the conversation at these thresholds:

| Threshold | Level | What Happens |
|-----------|-------|--------------|
| 50% | Info | Gentle reminder to consider summarizing |
| 70% | Warning | Recommend creating continuity ledger |
| 85% | Critical | Urgent - must clear context soon |

## Warning Behavior

- **50% and 70% warnings** are shown once per session
- **85% critical warnings** are always shown (safety feature)
- Warnings reset when you run `/clear` or start a new session

## Resetting Warnings

If you've dismissed a warning but want to see it again:

```bash
# Method 1: Clear context (recommended)
# Run /clear in Claude Code

# Method 2: Force reset via environment
export RING_RESET_CONTEXT_WARNING=1
# Then submit your next prompt
```

## Estimation Formula

The estimation uses conservative defaults:

| Constant | Value | Description |
|----------|-------|-------------|
| TOKENS_PER_TURN | 2,500 | Average tokens per conversation turn |
| BASE_SYSTEM_OVERHEAD | 45,000 | System prompt, tools, etc. |
| DEFAULT_CONTEXT_SIZE | 200,000 | Claude's typical context window |

**Formula:** `percentage = (45000 + turns * 2500) * 100 / 200000`

| Turn Count | Estimated % | Tier |
|------------|-------------|------|
| 1 | 23% | none |
| 22 | 50% | info |
| 38 | 70% | warning |
| 50 | 85% | critical |

## Customization

### Adjusting Thresholds

Edit `shared/lib/context-check.sh` and modify the `get_warning_tier` function:

```bash
get_warning_tier() {
    local pct="${1:-0}"

    if [[ "$pct" -ge 85 ]]; then   # Adjust critical threshold
        echo "critical"
    elif [[ "$pct" -ge 70 ]]; then  # Adjust warning threshold
        echo "warning"
    elif [[ "$pct" -ge 50 ]]; then  # Adjust info threshold
        echo "info"
    else
        echo "none"
    fi
}
```

### Adjusting Estimation

Modify the constants in `shared/lib/context-check.sh`:

```bash
readonly TOKENS_PER_TURN=2500        # Average tokens per turn
readonly BASE_SYSTEM_OVERHEAD=45000  # System prompt overhead
readonly DEFAULT_CONTEXT_SIZE=200000 # Total context window
```

### Disabling Warnings

To disable context warnings entirely, remove the hook from `default/hooks/hooks.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/claude-md-reminder.sh"
          }
          // Remove context-usage-check.sh entry
        ]
      }
    ]
  }
}
```

## State Files

Context state is stored in:
- `.ring/state/context-usage-{session_id}.json` (if `.ring/` exists)
- `/tmp/context-usage-{session_id}.json` (fallback)

State files are automatically cleaned up on session start.

## Performance

The hook is designed to execute in <50ms to avoid slowing down prompts. Performance is achieved by:
- Simple turn-count based estimation (no API calls)
- Atomic file operations
- Minimal JSON processing

## Troubleshooting

### Warnings not appearing

1. Check hook is registered:
   ```bash
   cat default/hooks/hooks.json | grep context-usage
   ```

2. Check hook is executable:
   ```bash
   ls -la default/hooks/context-usage-check.sh
   ```

3. Run hook manually:
   ```bash
   echo '{"prompt": "test"}' | default/hooks/context-usage-check.sh
   ```

### Warnings appearing too early/late

Adjust the `TOKENS_PER_TURN` constant in `shared/lib/context-check.sh`. Higher values = warnings appear earlier.

### State file issues

Clear state manually:
```bash
rm -f .ring/state/context-usage-*.json
rm -f /tmp/context-usage-*.json
```

## Security

The hook includes security measures:
- **Session ID validation**: Only alphanumeric, hyphens, and underscores allowed
- **JSON escaping**: Prevents injection attacks in state files
- **Atomic writes**: Uses temp file + mv pattern to prevent corruption
- **Symlink resolution**: PROJECT_DIR resolved to canonical path
