---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session - dispatches fresh subagent for each task with comprehensive code review (code-reviewer, security-reviewer, business-logic-reviewer) between tasks, enabling fast iteration with quality gates
---

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with code review after each.

**Core principle:** Fresh subagent per task + review between tasks = high quality, fast iteration

## Overview

**vs. Executing Plans (parallel session):**
- Same session (no context switch)
- Fresh subagent per task (no context pollution)
- Code review after each task (catch issues early)
- Faster iteration (no human-in-loop between tasks)

**When to use:**
- Staying in this session
- Tasks are mostly independent
- Want continuous progress with quality gates

**When NOT to use:**
- Need to review plan first (use executing-plans)
- Tasks are tightly coupled (manual execution better)
- Plan needs revision (brainstorm first)

## The Process

### 1. Load Plan

Read plan file, create TodoWrite with all tasks.

### 2. Execute Task with Subagent

For each task:

**Dispatch fresh subagent:**
```
Task tool (general-purpose):
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N from [plan-file].

    Read that task carefully. Your job is to:
    1. Implement exactly what the task specifies
    2. Write tests (following TDD if task says to)
    3. Verify implementation works
    4. Commit your work
    5. Report back

    Work from: [directory]

    Report: What you implemented, what you tested, test results, files changed, any issues
```

**Subagent reports back** with summary of work.

### 3. Review Subagent's Work (Sequential Gates)

**Dispatch reviewer subagents sequentially, not in parallel:**

**Gate 1: Code Review (Foundation)**
```
Task tool (ring:code-reviewer):
  WHAT_WAS_IMPLEMENTED: [from subagent's report]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [commit before task]
  HEAD_SHA: [current commit]
  DESCRIPTION: [task summary]
```
**→ If fails: Fix issues, re-run Gate 1, then proceed**
**→ If passes: Proceed to Gate 2**

**Gate 2: Business Logic Review (Correctness)**
```
Task tool (ring:business-logic-reviewer):
  [Same parameters]
```
**→ If fails: Fix issues, re-run from Gate 1, then proceed**
**→ If passes: Proceed to Gate 3**

**Gate 3: Security Review (Safety)**
```
Task tool (ring:security-reviewer):
  [Same parameters]
```
**→ If fails: Fix issues, determine restart point (usually Gate 1 or Gate 3 only)**
**→ If passes: Task complete**

**Each reviewer returns:** Strengths, Issues (Critical/High/Medium/Low), Assessment (PASS/FAIL)

### 4. Apply Review Feedback at Each Gate

**At each gate:**

**If Critical/High issues:**
- Dispatch fix subagent to address issues
- Re-run from appropriate gate:
  - Major changes → Re-run from Gate 1
  - Business changes → Re-run from Gate 2
  - Small security fixes → Re-run Gate 3 only
- Don't proceed to next gate until current gate passes

**If Medium issues:**
- Fix before proceeding (prevents tech debt accumulation)
- Re-run current gate to verify

**If Low/Minor issues only:**
- Note for tech debt backlog
- Proceed to next gate

**Dispatch follow-up subagent when needed:**
```
"Fix issues from [reviewer name]: [list issues with severity]"
```

### 5. Mark Complete, Next Task

After all three gates pass for current task:
- Mark task as completed in TodoWrite
- Move to next task
- Repeat steps 2-5

### 6. Final Review (After All Tasks)

After all tasks complete, run sequential final validation across entire implementation:

**Final Gate 1: Code Review**
```
Task tool (ring:code-reviewer):
  WHAT_WAS_IMPLEMENTED: All tasks from [plan]
  PLAN_OR_REQUIREMENTS: Complete plan from [plan-file]
  BASE_SHA: [start of development]
  HEAD_SHA: [current commit]
  DESCRIPTION: Full implementation review
```
**→ Reviews overall architecture, integration, consistency**

**Final Gate 2: Business Logic Review**
```
Task tool (ring:business-logic-reviewer): [Same parameters]
```
**→ Validates all plan requirements met, end-to-end workflows work**

**Final Gate 3: Security Review**
```
Task tool (ring:security-reviewer): [Same parameters]
```
**→ Final security audit across all changes, integration security**

### 7. Complete Development

After final review passes:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use ring:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## Example Workflow

```
You: I'm using Subagent-Driven Development to execute this plan.

[Load plan, create TodoWrite]

Task 1: Hook installation script

[Dispatch implementation subagent]
Subagent: Implemented install-hook with tests, 5/5 passing

[Sequential review process]
Gate 1 - Code reviewer: PASS. Strengths: Good test coverage. Issues: None.
Gate 2 - Business reviewer: PASS. Strengths: Meets requirements. Issues: None.
Gate 3 - Security reviewer: PASS. Strengths: No security concerns. Issues: None.

[Mark Task 1 complete]

Task 2: User authentication endpoint

[Dispatch implementation subagent]
Subagent: Added auth endpoint with JWT, 8/8 tests passing

[Sequential review process]
Gate 1 - Code reviewer:
  Strengths: Clean architecture
  Issues (Low): Consider extracting token logic
  Assessment: PASS (low issues don't block)

Gate 2 - Business reviewer:
  Strengths: Workflow correct
  Issues (High): Missing password reset flow (required per PRD)
  Assessment: FAIL

[Dispatch fix subagent for password reset]
Fix subagent: Added password reset flow with email validation

[Re-run from Gate 1 due to new feature]
Gate 1 - Code reviewer: PASS
Gate 2 - Business reviewer: PASS. All requirements met.

Gate 3 - Security reviewer:
  Strengths: Good validation
  Issues (Critical): JWT secret hardcoded, (High): No rate limiting
  Assessment: FAIL

[Dispatch fix subagent for security issues]
Fix subagent: Moved secret to env var, added rate limiting

[Re-run Gate 3 only - small security fixes]
Gate 3 - Security reviewer: PASS. Issues resolved.

[Mark Task 2 complete]

...

[After all tasks]
[Sequential final validation across entire implementation]

Final Gate 1 - Code reviewer:
  All implementation solid, architecture consistent
  Assessment: PASS

Final Gate 2 - Business reviewer:
  All requirements met, workflows complete
  Assessment: PASS

Final Gate 3 - Security reviewer:
  No remaining security concerns, ready for production
  Assessment: PASS

Done!
```

**Why sequential worked better:**
- Business reviewer caught missing feature before security audit
- Security fixes didn't require re-running business review
- Each reviewer worked on validated foundation from previous gates

## Advantages

**vs. Manual execution:**
- Subagents follow TDD naturally
- Fresh context per task (no confusion)
- Parallel-safe (subagents don't interfere)

**vs. Executing Plans:**
- Same session (no handoff)
- Continuous progress (no waiting)
- Review checkpoints automatic

**Cost:**
- More subagent invocations
- But catches issues early (cheaper than debugging later)

## Red Flags

**Never:**
- Skip code review between tasks
- Proceed with unfixed Critical issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Implement without reading plan task

**If subagent fails task:**
- Dispatch fix subagent with specific instructions
- Don't try to fix manually (context pollution)

## Integration

**Required workflow skills:**
- **writing-plans** - REQUIRED: Creates the plan that this skill executes
- **requesting-code-review** - REQUIRED: Review after each task (see Step 3)
- **finishing-a-development-branch** - REQUIRED: Complete development after all tasks (see Step 7)

**Subagents must use:**
- **test-driven-development** - Subagents follow TDD for each task

**Alternative workflow:**
- **executing-plans** - Use for parallel session instead of same-session execution

See reviewer agent definitions: agents/code-reviewer.md, agents/security-reviewer.md, agents/business-logic-reviewer.md
