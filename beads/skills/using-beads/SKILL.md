---
name: using-beads
description: |
  Beads (bd) workflow integration - dependency-aware issue tracking for AI agents.
  Teaches proper bd usage: ready work discovery, issue lifecycle, dependency management.

trigger: |
  - ALWAYS at session start (auto-injected via hook)
  - When working on tasks that need tracking
  - When discovering work that should be logged
  - When needing to find next actionable work

skip_when: |
  - Never skip - foundational workflow knowledge

related:
  complementary: [test-driven-development, systematic-debugging]
---

# Using Beads (bd) - Dependency-Aware Issue Tracking

## Overview

Beads is a lightweight issue tracker with first-class dependency support, designed for AI-supervised workflows. Issues chain together like beads on a string.

**Key Concept:** `bd ready` shows unblocked work - issues with status 'open' AND no blocking dependencies.

## Essential Workflow

### 1. Check Ready Work First

```bash
bd ready                    # What can I work on NOW?
bd ready --json             # Programmatic format
bd list --status open       # All open issues
bd list --status in_progress # What's being worked on
```

### 2. Claim and Work

```bash
bd update ISSUE-ID --status in_progress   # Claim work
# ... do the work ...
bd close ISSUE-ID --reason "Completed in commit abc123"
```

### 3. Create Issues When Discovering Work

```bash
bd create "Fix login bug"                           # Basic
bd create "Add auth" -p 0 -t feature                # Priority 0 (highest), type feature
bd create "Write tests" -d "Unit tests for auth"   # With description
```

### 4. Manage Dependencies

```bash
bd dep add ISSUE-A ISSUE-B          # B blocks A (A depends on B)
bd dep add ISSUE-A ISSUE-B --type related   # Soft link (doesn't block)
bd dep tree ISSUE-ID                # Visualize dependency tree
bd dep cycles                       # Detect circular dependencies
```

## Priority Levels

| Priority | Meaning | Use When |
|----------|---------|----------|
| 0 | Critical | Blocking production, security issues |
| 1 | High | Important bugs, key features |
| 2 | Medium | Normal priority (default) |
| 3 | Low | Nice-to-have, minor improvements |
| 4 | Minimal | Backlog, someday/maybe |

## Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - General work item
- `epic` - Large multi-issue work
- `spike` - Research/investigation

## Common Patterns

### Pattern: Start of Session
```bash
bd status                   # Overview of database
bd ready                    # What's ready to work on
bd list --status in_progress # What's already claimed
```

### Pattern: Discover Blocking Work
```bash
# While working on ISSUE-A, discover ISSUE-B must be done first
bd create "Fix dependency X" -t bug
bd dep add ISSUE-A NEW-ISSUE-ID   # NEW blocks ISSUE-A
bd update ISSUE-A --status open   # Back to open (now blocked)
bd update NEW-ISSUE-ID --status in_progress  # Work on blocker
```

### Pattern: Close with Context
```bash
bd close ISSUE-ID --reason "Fixed in PR #42"
bd close ISSUE-ID --reason "Resolved by implementing X in commit abc"
```

### Pattern: Search and Find
```bash
bd search "authentication"    # Text search
bd list --label security      # By label
bd list --assignee alice      # By assignee
bd show ISSUE-ID              # Full details
```

## Database Setup

```bash
bd init                       # Initialize in current directory
bd init --prefix api          # Custom prefix (api-1, api-2, ...)
bd info                       # Show database location
bd doctor                     # Health check
```

## JSON Output (for programmatic use)

Most commands support `--json`:
```bash
bd ready --json               # Ready issues as JSON
bd list --json                # All issues as JSON
bd show ISSUE-ID --json       # Single issue details
```

## Anti-Patterns to Avoid

1. **Don't create issues without checking existing ones first**
   ```bash
   bd search "keyword"         # Check before creating
   bd duplicates               # Find potential duplicates
   ```

2. **Don't leave issues in_progress when blocked**
   - If blocked, set back to `open` and create blocker issue

3. **Don't ignore dependencies**
   - Always use `bd dep add` when work has prerequisites

4. **Don't close without reason**
   - Always provide `--reason` for traceability

## Quick Reference

| Action | Command |
|--------|---------|
| What's ready? | `bd ready` |
| Start work | `bd update ID --status in_progress` |
| Create issue | `bd create "title"` |
| Add blocker | `bd dep add BLOCKED BLOCKER` |
| Finish work | `bd close ID --reason "..."` |
| Show details | `bd show ID` |
| Search | `bd search "query"` |
| Overview | `bd status` |

## Remember

- **`bd ready`** is your starting point - it shows what's actually actionable
- **Dependencies prevent duplicate effort** - always model blocking relationships
- **Close with context** - future you will thank present you
- **JSON for automation** - use `--json` when parsing output
