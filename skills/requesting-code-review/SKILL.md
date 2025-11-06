---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements - dispatches reviewer subagents (code-reviewer, security-reviewer, business-logic-reviewer) to review implementation against plan or requirements before proceeding
---

# Requesting Code Review

Dispatch reviewer subagents sequentially to catch issues before they cascade.

**Core principle:** Review early, review often. Reviews build on validated foundations.

## Review Order (In Parallel, using the Full Reviewer agent that orchestrates 3 parallel subagents)

Three specialized reviewers run in sequence, each building on the previous:

**1. ring:code-reviewer** (Foundation)
- **Focus:** Architecture, design patterns, code quality, maintainability
- **Why first:** Can't review business logic or security in unreadable code
- **Gates:** Clear structure, testable design, readable names
- **If fails:** Report for final summary

**2. ring:business-logic-reviewer** (Correctness)
- **Focus:** Domain correctness, business rules, edge cases, requirements
- **Why second:** Assumes code is now readable and well-structured
- **Gates:** Meets requirements, handles edge cases, maintains invariants
- **If fails:** Report for final summary

**3. ring:security-reviewer** (Safety)
- **Focus:** Vulnerabilities, authentication, input validation, OWASP risks
- **Why last:** Most effective on clean, correct implementation
- **Gates:** Secure for production
- **If fails:** Report for final summary

**Critical:** Run in parallel. Summarize after finished. Fix automatically CRITICAL, HIGH, and MEDIUM issues. Report on low/cosmetic issues.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## Which Reviewers to Use

**Use all three reviewers (parallel) when:**
- Implementing new features (comprehensive check)
- Before merge to main (final validation)
- After completing major milestone

**Use subset when domain doesn't apply:**
- **Code-reviewer only:** Documentation changes, config updates
- **Code + Business (skip security):** Internal scripts with no external input
- **Code + Security (skip business):** Infrastructure/DevOps changes

**Default: Use all three in parallel.** Only skip reviewers when you're certain their domain doesn't apply.
**Important note: if you wish, the 'full-reviewer' agent orchestrates the other reviewers.**

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Parallel review process:**

**Step 1: Code Review (Foundation)**
```
Task tool (ring:code-reviewer):
  WHAT_WAS_IMPLEMENTED: [What you built]
  PLAN_OR_REQUIREMENTS: [Requirements/plan reference]
  BASE_SHA: [starting commit]
  HEAD_SHA: [current commit]
  DESCRIPTION: [brief summary]
```

**If code review passes → Report**
**If code review fails → Report**

**Step 2: Business Logic Review (Correctness)**
```
Task tool (ring:business-logic-reviewer):
  [Same parameters as code review]
```

**If code review passes → Report**
**If code review fails → Report**

**Step 3: Security Review (Safety)**
```
Task tool (ring:security-reviewer):
  [Same parameters as code review]
```

**If code review passes → Report**
**If code review fails → Report**

**3. Act on feedback at each gate:**
- **Critical/High/Medium issues:** MUST fix immediately before proceeding to next task.
- **Low issues:** Report before proceeding (document tech debt at ``docs/tech-debt/{date}-{subject}.md``)
- **Push back:** If reviewer is wrong, provide reasoning and evidence

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task sequentially (Gate 1 → Gate 2 → Gate 3)
- Catch issues at earliest gate
- Fix before moving to next reviewer, then next task

**Executing Plans:**
- Review after each batch (3 tasks) sequentially
- Get feedback at each gate, apply, continue
- Re-run from Gate 1 if major changes needed

**Ad-Hoc Development:**
- Review before merge sequentially (all three gates)
- Review when stuck (may only need Gate 1 for perspective)

## Red Flags

**Never:**
- Skip Gate 1 because "code is simple" (foundation for other gates)
- Proceed to next task with unfixed Critical/High/Medium issues
- Skip security review for "just refactoring" (may expose vulnerabilities)
- Assume business logic is correct without Gate 2 validation
- Argue with valid technical/security feedback

**Always:**
- Run in parallel: Code / Business / Security
- Fix Critical/High/Medium issues before next task
- Re-run from Gate 1 if major architectural changes made
- Document Low issues as tech debt

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification
- Security concerns require extra scrutiny

## When to Re-run From Gate 1

After fixing issues, decide where to restart:

**Re-run from Gate 1 (code review):**
- Major architectural changes
- Significant refactoring
- New files or modules added
- Changed project structure

**Re-run from Gate 2 (business logic):**
- Business rule changes
- Added/changed features
- Modified workflows or state machines

**Re-run only Gate 3 (security):**
- Small security fixes (validation, encoding, config)
- No architectural or business logic changes
- Adding defensive measures only
