---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements - dispatches reviewer subagents (code-reviewer, security-reviewer, business-logic-reviewer) to review implementation against plan or requirements before proceeding
---

# Requesting Code Review

Dispatch reviewer subagents sequentially to catch issues before they cascade.

**Core principle:** Review early, review often. Sequential reviews build on validated foundations.

## Review Order (Sequential, Not Parallel)

Three specialized reviewers run in sequence, each building on the previous:

**1. ring:code-reviewer** (Foundation)
- **Focus:** Architecture, design patterns, code quality, maintainability
- **Why first:** Can't review business logic or security in unreadable code
- **Gates:** Clear structure, testable design, readable names
- **If fails:** Fix architecture before proceeding to next reviewer

**2. ring:business-logic-reviewer** (Correctness)
- **Focus:** Domain correctness, business rules, edge cases, requirements
- **Why second:** Assumes code is now readable and well-structured
- **Gates:** Meets requirements, handles edge cases, maintains invariants
- **If fails:** Fix business logic before proceeding to security review

**3. ring:security-reviewer** (Safety)
- **Focus:** Vulnerabilities, authentication, input validation, OWASP risks
- **Why last:** Most effective on clean, correct implementation
- **Gates:** Secure for production
- **If fails:** Fix security issues (usually smaller scope)

**Critical:** Run sequentially, not parallel. Each reviewer assumes previous gates passed.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## Which Reviewers to Use

**Use all three reviewers (sequential) when:**
- Implementing new features (comprehensive check)
- Before merge to main (final validation)
- After completing major milestone

**Use subset when domain doesn't apply:**
- **Code-reviewer only:** Documentation changes, config updates
- **Code + Business (skip security):** Internal scripts with no external input
- **Code + Security (skip business):** Infrastructure/DevOps changes

**Default: Use all three in sequence.** Only skip reviewers when you're certain their domain doesn't apply.

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Sequential review process:**

**Step 1: Code Review (Foundation)**
```
Task tool (ring:code-reviewer):
  WHAT_WAS_IMPLEMENTED: [What you built]
  PLAN_OR_REQUIREMENTS: [Requirements/plan reference]
  BASE_SHA: [starting commit]
  HEAD_SHA: [current commit]
  DESCRIPTION: [brief summary]
```

**If code review passes → Step 2**
**If code review fails → Fix issues, re-run code review, then proceed**

**Step 2: Business Logic Review (Correctness)**
```
Task tool (ring:business-logic-reviewer):
  [Same parameters as code review]
```

**If business review passes → Step 3**
**If business review fails → Fix issues, re-run from Step 1 (code may have changed)**

**Step 3: Security Review (Safety)**
```
Task tool (ring:security-reviewer):
  [Same parameters as code review]
```

**If security review passes → Done**
**If security review fails → Fix issues, re-run from Step 1 if architecture changed, else re-run from Step 3**

**3. Act on feedback at each gate:**
- **Critical/High issues:** MUST fix before proceeding to next reviewer
- **Medium issues:** Fix before proceeding unless time-critical (document tech debt)
- **Low issues:** Note for later, don't block progress
- **Push back:** If reviewer is wrong, provide reasoning and evidence

## Example: Sequential Review (Passes All Gates)

```
[Just completed Task 2: User profile management]

You: Let me request sequential review before proceeding.

BASE_SHA=$(git rev-parse origin/main)
HEAD_SHA=$(git rev-parse HEAD)

### Gate 1: Code Review
[Dispatch ring:code-reviewer]
  WHAT_WAS_IMPLEMENTED: User profile CRUD with validation
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/user-management.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661

Code reviewer:
  Strengths: Clean architecture, good separation of concerns, testable
  Issues:
    Minor: Consider extracting validation rules to separate module
  Assessment: PASS - Minor issues don't block

### Gate 2: Business Logic Review
[Dispatch ring:business-logic-reviewer - same parameters]

Business reviewer:
  Strengths: User workflow intuitive, edge cases handled
  Issues:
    Low: Could add more descriptive error messages
  Assessment: PASS - Requirements met

### Gate 3: Security Review
[Dispatch ring:security-reviewer - same parameters]

Security reviewer:
  Strengths: Input validation solid, no injection risks
  Issues:
    Medium: Add rate limiting on profile updates
  Assessment: PASS with note - Rate limiting is defense-in-depth, not blocker

You: [Note Minor/Low/Medium issues for tech debt backlog]
[All gates passed - Continue to Task 3]
```

## Example: Sequential Review (Fails Early, Saves Time)

```
[Just completed Task 3: Payment processing]

BASE_SHA=$(git rev-parse origin/main)
HEAD_SHA=$(git rev-parse HEAD)

### Gate 1: Code Review
[Dispatch ring:code-reviewer]

Code reviewer:
  Strengths: Feature complete
  Issues:
    Critical: Payment logic mixed with presentation layer
    Important: No tests for refund calculations
    Important: Magic numbers throughout (fees, limits)
  Assessment: FAIL - Major architectural issues

You: [Fix architecture issues]
[Extract payment service, add tests, create constants]
[Re-run Gate 1]

Code reviewer (2nd attempt):
  Strengths: Clean architecture, well-tested
  Issues: None
  Assessment: PASS

### Gate 2: Business Logic Review
[Dispatch ring:business-logic-reviewer]

Business reviewer:
  Strengths: Calculations correct, edge cases handled
  Issues:
    Critical: Missing refund window validation (PRD requires 30-day limit)
    High: Partial refunds not supported (required per PRD)
  Assessment: FAIL - Missing required features

You: [Add refund window check, implement partial refunds]
[Update code, major changes - re-run from Gate 1]

### Gate 1: Code Review (after business logic fix)
Code reviewer:
  Assessment: PASS - Architecture maintained

### Gate 2: Business Logic Review (2nd attempt)
Business reviewer:
  Assessment: PASS - All requirements met

### Gate 3: Security Review
[Dispatch ring:security-reviewer]

Security reviewer:
  Strengths: Good validation
  Issues:
    Critical: Refund amount not validated against original charge
    High: No idempotency key for payment operations
  Assessment: FAIL - Security vulnerabilities

You: [Add refund validation, implement idempotency]
[Small security fixes - re-run Gate 3 only]

### Gate 3: Security Review (2nd attempt)
Security reviewer:
  Assessment: PASS - Secure for production

Done! All gates passed.
```

**Why sequential saved time:**
- Didn't run business/security reviews on broken architecture
- Business review caught missing features before security audit
- Security only reviewed clean, correct implementation

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
- Run reviewers in parallel (wastes effort on failed gates)
- Skip Gate 1 because "code is simple" (foundation for other gates)
- Proceed to next gate with unfixed Critical/High issues
- Skip security review for "just refactoring" (may expose vulnerabilities)
- Assume business logic is correct without Gate 2 validation
- Argue with valid technical/security feedback

**Always:**
- Run sequentially: Code → Business → Security
- Fix Critical/High issues before next gate
- Re-run from Gate 1 if major architectural changes made
- Document Medium/Low issues as tech debt

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
