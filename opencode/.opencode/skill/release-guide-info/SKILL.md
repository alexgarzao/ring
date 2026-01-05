---
name: release-guide-info
description: |
  Generate Ops Update Guide from Git Diff. Produces internal Operations-facing
  update/migration guides based on git diff analysis. Includes tag auto-detection
  and commit log analysis.
license: MIT
compatibility: opencode
metadata:
  trigger: "Preparing release, documenting changes between refs, creating ops guide"
  skip_when: "No git repository, single file change, customer-facing notes only"
  source: ring-default
---

# Release Guide Info - Ops Update Guide Generator

## Related Skills

**Complementary:** finishing-a-development-branch, handoff-tracking

---

## Overview

You are a code-aware documentation agent. Produce an **internal** Operations-facing update/migration guide.

## Runtime Inputs (REQUIRED)

| Input | Description | Example |
|-------|-------------|---------|
| `BASE_REF` | Starting point (branch, tag, or SHA) | `main`, `release/v3.4.x`, `v1.0.0` |
| `TARGET_REF` | Ending point (branch, tag, or SHA) | `feature/foo`, `HEAD`, `v1.1.0` |
| `VERSION` (optional) | Version number (auto-detected from tags if not provided) | `v2.0.0`, `1.5.0` |
| `LANGUAGE` (optional) | Output language | `en` (default), `pt-br`, `both` |
| `MODE` (optional) | Execution mode | `STRICT_NO_TOUCH` (default), `TEMP_CLONE_FOR_FRESH_REFS` |

**Language options:**
- `en` - English only (default)
- `pt-br` - Portuguese (Brazil) only
- `both` - Generate two files, one in each language

**Version handling:**
- If `VERSION` provided -> Use it directly
- If `TARGET_REF` is a tag -> Auto-extract version from tag name
- If neither -> Omit version from output

**Comparison range:** Always use triple-dot `BASE_REF...TARGET_REF`

## Safety Invariants

### STRICT_NO_TOUCH (default)

**Hard requirement:** Do NOT alter anything in the current local repo.

**FORBIDDEN commands:**
- `git fetch`, `git pull`, `git push`
- `git checkout`, `git switch`, `git reset`, `git clean`
- `git commit`, `git merge`, `git rebase`, `git cherry-pick`
- `git worktree`, `git gc`, `git repack`, `git prune`
- Any write operation to `.git/` files

**ALLOWED commands (read-only):**
- `git rev-parse`, `git diff`, `git show`, `git log`, `git remote get-url`

**If ref does not exist locally:** STOP and report:
- Which ref failed to resolve
- That STRICT_NO_TOUCH forbids fetching
- Suggest alternative: TEMP_CLONE_FOR_FRESH_REFS

### TEMP_CLONE_FOR_FRESH_REFS (optional)

Goal: Do NOT touch current repo, but allow obtaining up-to-date remote refs in an isolated temporary clone.

## The Process

### Step 1 - Resolve Refs and Metadata

```bash
# Verify refs exist
git rev-parse --verify BASE_REF^{commit}
git rev-parse --verify TARGET_REF^{commit}

# Capture SHAs
BASE_SHA=$(git rev-parse --short BASE_REF)
TARGET_SHA=$(git rev-parse --short TARGET_REF)
```

### Step 2 - Commit Log Analysis

```bash
# Get commit messages between refs
git log --oneline --no-merges BASE_REF...TARGET_REF

# Get detailed commit messages for context
git log --pretty=format:"%h %s%n%b" --no-merges BASE_REF...TARGET_REF
```

**Parse commit messages for:**

| Pattern | Category | Example |
|---------|----------|---------|
| `feat:`, `feature:` | Feature | `feat: add user authentication` |
| `fix:`, `bugfix:` | Bug Fix | `fix: resolve null pointer exception` |
| `refactor:` | Improvement | `refactor: optimize database queries` |
| `breaking:`, `BREAKING CHANGE:` | Breaking | `breaking: remove deprecated API` |

### Step 3 - Produce the Diff

```bash
# Stats view
git diff --find-renames --find-copies --stat BASE_REF...TARGET_REF

# Full diff
git diff --find-renames --find-copies BASE_REF...TARGET_REF
```

### Step 4 - Build Change Inventory

From the diff, identify:

| Category | What to Look For |
|----------|------------------|
| **Endpoints** | New/changed/removed (method/path/request/response/status codes) |
| **DB Schema** | Migrations, backfills, indexes, constraints |
| **Messaging** | Topics, payloads, headers, idempotency, ordering |
| **Config/Env** | New vars, changed defaults |
| **Auth** | Permissions, roles, tokens |
| **Performance** | Rate-limits, timeouts, retries |
| **Dependencies** | Bumps with runtime behavior impact |
| **Observability** | Logging, metrics, tracing changes |
| **Operations** | Scripts, cron, job schedules |

### Step 5 - Write the Ops Update Guide

Use appropriate template based on LANGUAGE parameter.

**Section Labels:**
- **What Changed** - Bullet list with concrete changes
- **Why It Changed** - Infer from code/comments/tests
- **Client Impact** - Risk level: Low/Medium/High
- **Required Client Action** - "None" or exact steps
- **Deploy/Upgrade Notes** - Order of operations, compatibility
- **Post-Deploy Monitoring** - Logs, metrics, signals
- **Rollback** - Safety: Safe/Conditional/Not recommended

### Step 6 - Preview Before Saving

**MANDATORY: Show preview summary before writing to disk.**

Present to user for confirmation before proceeding.

### Step 7 - Persist Guide to Disk

**File naming convention:**

| Has Version? | LANGUAGE | Filename Pattern |
|--------------|----------|------------------|
| Yes | `en` | `{DATE}_{REPO}-{VERSION}.md` |
| Yes | `pt-br` | `{DATE}_{REPO}-{VERSION}_pt-br.md` |
| No | `en` | `{DATE}_{REPO}-{BASE}-to-{TARGET}.md` |
| No | `pt-br` | `{DATE}_{REPO}-{BASE}-to-{TARGET}_pt-br.md` |
| Any | `both` | Generate BOTH files above |

**Output directory:** `notes/releases/`

## Hard Rules (Content)

| Rule | Enforcement |
|------|-------------|
| No invented changes | Everything MUST be supported by diff |
| Uncertain info | Mark as **ASSUMPTION** + **HOW TO VALIDATE** |
| Operational language | Audience is Ops, not customers |
| External changes | API, events, DB, auth, timeouts MUST be called out |
| Preview required | MUST show preview before saving |
| User confirmation | MUST wait for user approval before writing files |

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "The diff is too large, I'll summarize" | Summarizing loses critical details. Ops needs specifics. | **Document ALL significant changes** |
| "This change is obvious, no need to explain" | Obvious to you != obvious to Ops. Context is required. | **Add contextual narrative** |
| "I'll skip the preview, user is in a hurry" | Preview prevents errors. Skipping risks wrong output. | **ALWAYS show preview first** |
| "No breaking changes detected" | Did you check commit messages for BREAKING CHANGE? | **Verify commit messages AND diff** |
| "Rollback analysis not needed, changes are safe" | ALL changes need rollback assessment. No exceptions. | **Include rollback section** |
| "I'll invent a likely reason for this change" | Invented reasons mislead Ops. Mark as ASSUMPTION. | **Mark uncertain info clearly** |

## Quality Checklist

Before output, self-validate:

- [ ] Every section starts with contextual narrative
- [ ] All log messages in table format (Level | Message | Meaning)
- [ ] Rollback analysis consolidated as matrix at end
- [ ] No invented changes - everything traceable to diff
- [ ] File:line references included for key code changes
