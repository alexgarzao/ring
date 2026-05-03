---
name: ring:interview-me
description: |
  Proactive requirements gathering - systematically interviews the user to uncover
  ambiguities, preferences, and constraints BEFORE implementation begins.

trigger: |
  - User invokes /ring:interview-me command
  - Claude detects significant ambiguity in requirements (>3 unclear decisions)
  - Multiple valid implementation paths exist with no clear winner
  - User says "interview me", "ask me questions", "clarify with me"

skip_when: |
  - Requirements are already crystal clear
  - User has provided detailed specifications
  - Following an existing plan with explicit instructions
  - Single question would suffice (use doubt-triggered-questions instead)

sequence:
  before: [ring:brainstorm, ring:write-plan]
---

# Interviewing User for Requirements

Proactively surface and resolve ambiguities BEFORE implementation begins.

**Core principle:** 5 questions upfront > 3 implementation rewrites.

**Announce at start:** "Using ring:interview-me to gather requirements before we begin."

## Process

### Phase 1: Context Analysis (explore before asking)

Analyze: what was explicitly stated, what the codebase implies, what remains ambiguous, what decisions must be made. Explore the codebase for 30s — answers from context save questions.

**Ambiguity inventory:** architecture decisions, behavior gaps, constraints, preferences, integration points.

### Phase 2: Question Clustering

> **Shared pattern:** For "when to ask vs proceed" criteria, genuine doubt definition, anti-patterns, and question quality guidelines, see [`shared-patterns/doubt-triggered-questions.md`](../shared-patterns/doubt-triggered-questions.md). This skill extends that pattern with structured multi-round interview flow.

| Priority | Category | Criteria |
|----------|----------|----------|
| P0 | Blocking | Cannot proceed without answer |
| P1 | Architecture | Affects overall structure |
| P2 | Behavior | Affects user-facing functionality |
| P3 | Preferences | Style, not correctness |

**Budget:** max 4 questions per AskUserQuestion call, max 3 rounds total.

### Phase 3: Structured Interview

Use `AskUserQuestion` with:
- Evidence of what you already know (shows exploration)
- Why you're uncertain (genuine conflict)
- 2-4 concrete, mutually exclusive options with descriptions

<example>
Good: header="Auth Method", question="Codebase has session-based auth (UserService) and JWT (APIService). Which for this endpoint?", options=[session, jwt, both]
Bad: question="What auth should I use?", options=[Option 1, Option 2]
</example>

### Phase 4: Understanding Summary

```markdown
## Validated Understanding
### What We're Building (1-2 sentences)
### Key Decisions Made (table: Decision | Choice | Rationale)
### Constraints Confirmed
### Out of Scope (explicit)
### Assumptions (if any)
```

Present this to user for confirmation.

### Phase 5: Confirm and Proceed

**Confirmed by:** "Confirmed", "Correct", "Proceed", "Go ahead", "Yes" (explicit).  
**NOT confirmed:** silence, "interesting", questions about the summary.

If not confirmed → return to Phase 3 with targeted follow-ups.

## Exit Criteria

- [ ] All P0 (blocking) questions answered
- [ ] All P1 (architecture) questions answered
- [ ] Validated Understanding presented and explicitly confirmed
- [ ] No remaining ambiguities affecting correctness

## Auto-Trigger Conditions

**Use automatically when:**
- Ambiguity count > 3
- Architecture choice unclear with no codebase precedent
- User request is high-level ("Build me X")
- Previous implementation was rejected
