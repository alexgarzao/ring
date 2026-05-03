---
name: ring:systematic-debugging
description: |
  Four-phase debugging framework - root cause investigation, pattern analysis,
  hypothesis testing, implementation. Ensures understanding before attempting fixes.

trigger: |
  - Bug reported or test failure observed
  - Unexpected behavior or error message
  - Root cause unknown
  - Previous fix attempt didn't work

skip_when: |
  - Root cause already known → just fix it
  - Error deep in call stack, need to trace backward → use ring:root-cause-tracing
  - Issue obviously caused by your last change → quick verification first

related:
  complementary: [ring:root-cause-tracing]
---

# Systematic Debugging

**Core principle: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

Especially when: under time pressure, "just one quick fix" seems obvious, previous fix didn't work, you don't fully understand the issue.

## The Four Phases

### Phase 1: Root Cause Investigation

Complete ALL before Phase 2:
- [ ] Error message copied verbatim
- [ ] Reproduction confirmed (exact steps)
- [ ] Recent changes reviewed (`git diff`, recent commits, new deps, config changes)
- [ ] Evidence gathered from ALL components (log at each boundary)
- [ ] Data flow traced (origin → error)

Error deep in stack → **use ring:root-cause-tracing skill.**

**Phase 1 Summary:** Error: [exact] | Reproduces: [steps] | Recent changes: [commits] | Component evidence: [each layer] | Data origin: [source]

### Phase 2: Pattern Analysis

Find working examples of similar code in the codebase. Read reference implementation COMPLETELY — don't skim. List EVERY difference between working and broken. Don't assume "that can't matter."

### Phase 3: Hypothesis Testing

1. Form single hypothesis: "I think X is root cause because Y" — be specific
2. Test with SMALLEST possible change — one variable at a time
3. Track: `H#1: [what] → [result] | H#2: [what] → [result]`

**If 3 hypotheses fail:** STOP immediately. "3 hypotheses failed, architecture review required." Discuss before more attempts.

### Phase 4: Implementation

1. **Create failing test** — use ring:test-driven-development skill
2. **Implement single fix** — root cause only, ONE change, no "while I'm here" improvements
3. **Verify** — test passes, no other tests broken
4. **If fix fails:** count fixes. <3 → return to Phase 1. ≥3 → STOP, architecture review required
5. After verified: post-completion review

## Time Limits

- 30 min without root cause → escalate
- 3 failed fixes → architecture review
- 1 hour total → stop, document, ask for guidance

## Red Flags (Return to Phase 1)

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "I don't fully understand but this might work"
- "One more fix attempt" (already tried 2+)
- Each fix reveals new problem (architecture issue)

User signals: "Is that not happening?" → you assumed without verifying. "Stop guessing" → proposing fixes without understanding.

## Quick Reference

| Phase | Success Criteria |
|-------|-----------------|
| 1. Root Cause | Understand WHAT and WHY |
| 2. Pattern | Identify what's different from working code |
| 3. Hypothesis | Confirmed single root cause |
| 4. Implementation | Bug resolved, tests pass |

**Circuit breakers:** 3 hypotheses fail → STOP. 3 fixes fail → STOP. 30 min no root cause → escalate.

## Sub-Skills

- **ring:root-cause-tracing** — When error is deep in call stack (Phase 1)
- **ring:test-driven-development** — For failing test case (Phase 4)
