---
name: linting-codebase
description: |
  Parallel lint fixing pattern - runs lint checks, groups issues into independent
  streams, and dispatches AI agents to fix all issues until the codebase is clean.

trigger: |
  - User runs /ring-default:lint command
  - Codebase has lint issues that need fixing
  - Multiple lint errors across different files/components

skip_when: |
  - Single lint error → fix directly without agent dispatch
  - Lint already passes → nothing to do
  - User only wants to see lint output, not fix
---

# Linting Codebase

## Overview

This skill runs lint checks on the codebase, analyzes the results to identify independent fix streams, and dispatches parallel AI agents to fix all issues. The process iterates until the codebase passes all lint checks.

**Core principle:** Group lint issues by file/component, dispatch one agent per independent stream, iterate until clean.

## ⛔ CRITICAL CONSTRAINTS

These constraints are NON-NEGOTIABLE and must be communicated to ALL dispatched agents:

```
┌─────────────────────────────────────────────────────────────────┐
│  🚫 DO NOT CREATE AUTOMATED SCRIPTS TO FIX LINT ISSUES         │
│  🚫 DO NOT CREATE DOCUMENTATION OR README FILES                 │
│  🚫 DO NOT ADD COMMENTS EXPLAINING THE FIXES                   │
│  ✅ FIX EACH ISSUE DIRECTLY BY EDITING THE SOURCE CODE         │
│  ✅ MAKE MINIMAL CHANGES - ONLY WHAT'S NEEDED FOR LINT         │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Lint Execution

### Step 1.1: Detect Lint Command

Check for available lint commands in this order:

```bash
# Priority order for lint detection
1. make lint          # If Makefile exists with lint target
2. npm run lint       # If package.json with lint script
3. yarn lint          # If yarn.lock exists
4. pnpm lint          # If pnpm-lock.yaml exists
5. golangci-lint run  # If Go project (go.mod exists)
6. cargo clippy       # If Rust project (Cargo.toml exists)
7. ruff check .       # If Python project (pyproject.toml/setup.py)
8. eslint .           # Fallback for JS/TS
```

### Step 1.2: Run Lint

Execute the detected lint command and capture output:

```bash
# Run lint and capture both stdout and stderr
<lint_command> 2>&1 | tee /tmp/lint-output.txt
echo "EXIT_CODE: $?"
```

### Step 1.3: Parse Results

Extract structured information from lint output:
- File path
- Line number
- Column number (if available)
- Error code/rule
- Error message
- Severity (error/warning)

## Phase 2: Stream Analysis

### Step 2.1: Group Issues

Group lint issues into independent streams that can be fixed in parallel:

**Grouping strategies (choose based on issue count):**

| Issue Count | Grouping Strategy |
|-------------|-------------------|
| < 10 issues | Group by file |
| 10-50 issues | Group by directory |
| 50-100 issues | Group by error type/rule |
| > 100 issues | Group by component/module |

### Step 2.2: Identify Independence

A stream is independent if:
- Files don't import/depend on each other
- Fixes won't cause conflicts
- Each agent can work without knowledge of other streams

**Example stream identification:**

```
Stream 1: src/api/*.ts (5 issues)
  - unused-vars: 3
  - no-explicit-any: 2

Stream 2: src/services/*.ts (8 issues)
  - prefer-const: 4
  - no-unused-expressions: 4

Stream 3: src/utils/*.ts (3 issues)
  - eqeqeq: 2
  - no-shadow: 1
```

### Step 2.3: Create Stream Summary

For each stream, create a summary:

```markdown
## Lint Analysis Summary

**Total issues:** 16
**Streams identified:** 3

### Stream 1: API Layer (5 issues)
- Path: src/api/
- Issues: unused-vars (3), no-explicit-any (2)
- Independence: ✅ No dependencies on other streams

### Stream 2: Services Layer (8 issues)
- Path: src/services/
- Issues: prefer-const (4), no-unused-expressions (4)
- Independence: ✅ No dependencies on other streams

### Stream 3: Utilities (3 issues)
- Path: src/utils/
- Issues: eqeqeq (2), no-shadow (1)
- Independence: ✅ No dependencies on other streams

**Recommended agents:** 3 (one per stream)
```

## Phase 3: Parallel Agent Dispatch

### Step 3.1: Prepare Agent Prompts

Each agent receives a focused prompt with:

1. **Scope** - Specific files/directories to fix
2. **Issues** - Exact lint errors with locations
3. **Constraints** - What NOT to do
4. **Output** - Expected return format

**Agent prompt template:**

```markdown
Fix the following lint issues in [SCOPE]:

## Issues to Fix

[LIST OF ISSUES WITH FILE:LINE:COLUMN AND ERROR MESSAGE]

## Constraints

⛔ CRITICAL - YOU MUST FOLLOW THESE RULES:
- DO NOT create any automated scripts to fix issues
- DO NOT create documentation or README files
- DO NOT add comments explaining your fixes
- DO NOT make changes beyond what's needed for lint
- FIX each issue directly by editing the source code
- MAKE minimal, targeted changes only

## Expected Output

After fixing all issues, return:

### Summary
- Files modified: [list]
- Issues fixed: [count]
- Issues unable to fix: [list with reasons]

### Changes Made
[Brief description of changes per file]
```

### Step 3.2: Dispatch Agents in Parallel

**CRITICAL: Use a single message with multiple Task tool calls**

```
Task tool #1 (general-purpose):
  description: "Fix lint issues in [Stream 1 scope]"
  prompt: [Agent prompt for Stream 1]

Task tool #2 (general-purpose):
  description: "Fix lint issues in [Stream 2 scope]"
  prompt: [Agent prompt for Stream 2]

Task tool #3 (general-purpose):
  description: "Fix lint issues in [Stream 3 scope]"
  prompt: [Agent prompt for Stream 3]
```

### Step 3.3: Await All Agents

Wait for all dispatched agents to complete their work before proceeding.

## Phase 4: Verification Loop

### Step 4.1: Re-run Lint

After all agents complete:

```bash
<lint_command> 2>&1
```

### Step 4.2: Evaluate Results

| Result | Action |
|--------|--------|
| **Lint passes** | ✅ Done - report success |
| **Same issues remain** | ⚠️ Investigate why fixes didn't work |
| **New issues appeared** | 🔄 Analyze and dispatch new agents |
| **Fewer issues remain** | 🔄 Create new streams, dispatch agents |

### Step 4.3: Iterate If Needed

If issues remain:
1. Parse new lint output
2. Group remaining issues into streams
3. Dispatch new agents
4. Repeat until clean

**Maximum iterations:** 5 (prevent infinite loops)

If issues persist after 5 iterations:
- Report remaining issues
- Ask user for guidance
- Possible causes: lint rules conflict, auto-fix not possible

## Agent Dispatch Rules

### DO dispatch when:
- 3+ files have lint issues
- Issues are in independent areas
- Fixes are mechanical (unused vars, formatting, etc.)

### DO NOT dispatch when:
- Single file has issues → fix directly
- Issues require architectural decisions
- Fixes would cause breaking changes

### Agent selection:

| Issue Type | Agent Type |
|------------|------------|
| TypeScript/JavaScript | `general-purpose` |
| Go | `general-purpose` or `ring-dev-team:backend-engineer-golang` |
| Security lints | `ring-default:security-reviewer` for analysis first |
| Style/formatting | `general-purpose` |

## Output Format

### After Successful Completion

```markdown
# Lint Fix Complete ✅

## Summary
- **Initial issues:** 16
- **Streams processed:** 3
- **Agents dispatched:** 3
- **Iterations needed:** 1
- **Final status:** All lint checks pass

## Changes by Stream

### Stream 1: API Layer
- Files: src/api/users.ts, src/api/auth.ts
- Issues fixed: 5
- Agent: Successfully completed

### Stream 2: Services Layer
- Files: src/services/user-service.ts, src/services/auth-service.ts
- Issues fixed: 8
- Agent: Successfully completed

### Stream 3: Utilities
- Files: src/utils/helpers.ts
- Issues fixed: 3
- Agent: Successfully completed

## Verification
✅ `make lint` passes with no errors
```

### After Partial Completion

```markdown
# Lint Fix Incomplete ⚠️

## Summary
- **Initial issues:** 16
- **Issues fixed:** 12
- **Issues remaining:** 4
- **Iterations completed:** 5 (max reached)

## Remaining Issues

These issues could not be automatically fixed:

1. `src/legacy/old-code.ts:45` - no-explicit-any
   - Reason: Requires type definition from external library

2. `src/config/settings.ts:12` - no-process-env
   - Reason: Intentional use of process.env

## Recommended Actions

1. Review remaining issues manually
2. Consider adding lint rule exceptions if intentional
3. Create type definitions for external libraries
```

## Error Handling

### Lint command not found
```
⚠️ Could not detect lint command.
Checked: make lint, npm run lint, golangci-lint, etc.

Please specify the lint command to use:
> _
```

### Agent failure
```
⚠️ Agent for Stream 2 failed to complete.

Error: [error details]

Options:
1. Retry this stream
2. Skip and continue with others
3. Investigate manually
```

### Conflicting changes
```
⚠️ Agents made conflicting changes to shared file.

File: src/shared/types.ts
- Stream 1 changed line 45
- Stream 2 changed line 47

Resolution: Review changes and merge manually.
```

## Integration with Other Skills

| Skill | When to use |
|-------|-------------|
| `dispatching-parallel-agents` | Pattern basis for this skill |
| `systematic-debugging` | If lint errors indicate deeper issues |
| `requesting-code-review` | After lint passes, before merge |

## Example Session

```
User: /ring-default:lint
Claude: Running lint checks...

[Executes: make lint]

Found 16 lint issues across 3 areas. Analyzing for parallel dispatch...

## Lint Analysis Summary

**Total issues:** 16
**Streams identified:** 3

### Stream 1: API Layer (5 issues)
- Path: src/api/
- Files: users.ts, auth.ts, middleware.ts
- Issues: unused-vars (3), no-explicit-any (2)

### Stream 2: Services (8 issues)
- Path: src/services/
- Files: user-service.ts, auth-service.ts
- Issues: prefer-const (4), no-unused-expressions (4)

### Stream 3: Utilities (3 issues)
- Path: src/utils/
- Files: helpers.ts, validators.ts
- Issues: eqeqeq (2), no-shadow (1)

Dispatching 3 agents in parallel...

[Task #1: Fix API layer lint issues]
[Task #2: Fix Services lint issues]
[Task #3: Fix Utilities lint issues]

All agents completed. Re-running lint...

[Executes: make lint]

✅ All lint checks pass!

# Lint Fix Complete ✅

## Summary
- Initial issues: 16
- Streams processed: 3
- Agents dispatched: 3
- Iterations: 1
- Final status: All lint checks pass
```
