---
date: 2025-12-29T22:30:45Z
session_name: context-usage-fix
git_commit: fe8977a10dd274fd702fe8ad7c02b4681712b302
branch: main
repository: LerianStudio/ring
topic: "Real Context Usage from Session File"
tags: [hooks, context-usage, session-data, gotcha-moment]
status: complete
outcome: SUCCEEDED
---

# Handoff: Real Context Usage Implementation

## Task Summary

**Goal:** Fix the inaccurate context usage estimation in Ring hooks.

**Status:** ✅ COMPLETE - Hooks now read REAL token usage from Claude's session file.

**Problem Solved:** The turn-count heuristic was off by 60+ percentage points (estimating 30% when actual was 90%+).

## Critical References

- `shared/lib/get-context-usage.sh` - NEW: Script to read real context usage
- `default/hooks/context-usage-check.sh` - Updated to use real data
- `shared/lib/context-check.sh` - Updated warning messages
- `~/.claude/projects/{project}/*.jsonl` - Where Claude stores session data with usage

## Recent Changes

### New File: `shared/lib/get-context-usage.sh`
Reads actual token usage from Claude's session JSONL file:
- Finds session file in `~/.claude/projects/{project}/`
- Extracts `usage` from last message
- Calculates: `(cache_read + cache_creation + input) / 200000 * 100`

### Modified: `default/hooks/context-usage-check.sh`
- Added `get_real_context_usage()` function
- Tries real data first, falls back to turn-count estimate
- Tracks `usage_source` (real vs estimate)

### Modified: `shared/lib/context-check.sh`
- Updated messages to say "from session data" instead of "estimated"
- Removed "run /context to verify" (since we now have real data)

## Learnings

### What Worked

1. **Session JSONL contains real usage data** - Each message in `*.jsonl` has:
   ```json
   {
     "usage": {
       "cache_read_input_tokens": 174946,
       "cache_creation_input_tokens": 1715,
       "input_tokens": 8
     }
   }
   ```

2. **Simple extraction with grep + jq** - No tokenizer needed:
   ```bash
   grep '"usage"' "$SESSION_FILE" | tail -1 | jq '.usage'
   ```

3. **File location is predictable** - `~/.claude/projects/{project-path-with-dashes}/*.jsonl`

### What Failed / Gotchas

1. **Slash commands can't be run by Claude** - We initially told Claude to "run /context" but Claude can't execute slash commands programmatically

2. **Turn-count heuristic was terrible** - Formula `23 + (turns * 1.25)%` massively underestimates when:
   - Dispatching parallel agents (10 agents = 10x tool outputs)
   - Reading large files
   - Getting verbose tool responses

3. **CLAUDE_SESSION_ID not always set** - Need to find session file by project path instead

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Read from session JSONL | Only reliable source of real usage |
| Fall back to estimate | Graceful degradation if file not found |
| Remove "/context" suggestions | Claude can't run slash commands |

## Files Modified

| File | Action | Commit |
|------|--------|--------|
| `shared/lib/get-context-usage.sh` | Created | fe8977a |
| `default/hooks/context-usage-check.sh` | Modified | fe8977a |
| `shared/lib/context-check.sh` | Modified | fe8977a |

## Action Items & Next Steps

### Completed
- [x] Create script to read real context usage
- [x] Integrate into context-usage-check.sh hook
- [x] Update warning messages
- [x] Commit changes

### Future Improvements

1. **Update task-completion-check.sh** - Could also use real context data to decide if handoff is truly needed

2. **Consider caching** - Reading JSONL on every prompt might be slow for huge sessions

3. **Add output_tokens tracking** - Currently only tracking input; output also contributes

## Session Statistics

| Metric | Value |
|--------|-------|
| Final context usage | 94% |
| Estimated (old method) | ~30% |
| Accuracy improvement | 64 percentage points |

## How to Verify

```bash
# Test the new script
bash shared/lib/get-context-usage.sh
# Should output: Context Usage: XX% / Tier: [safe|info|warning|critical]

# Test the hook
bash default/hooks/context-usage-check.sh | jq -r '.hookSpecificOutput.additionalContext'
# Should show real percentage, not estimate
```

## The "Gotcha Moment"

The breakthrough was realizing:
1. Claude Code stores transcripts in `~/.claude/projects/`
2. Each message includes API response with `usage` field
3. We can grep the last usage to get current context state

No need for tokenizers, no need for heuristics - the data was there all along!
