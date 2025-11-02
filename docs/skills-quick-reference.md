# ring Skills Quick Reference Card

## 🚨 Most Important Skills (Use These First!)

### Before ANY Task
**using-ring** - Check for relevant skills first (MANDATORY)
```
Before ANY action → Check skills
Before ANY tool use → Check skills
Before ANY code → Check skills
```

### When Writing Code
**test-driven-development** - Test first, always
```
RED → Write failing test → Watch it fail
GREEN → Minimal code → Watch it pass
REFACTOR → Clean up → Stay green
```

### When Something Breaks
**systematic-debugging** - Find root cause before fixing
```
Phase 1: Investigate (gather ALL evidence)
Phase 2: Analyze patterns
Phase 3: Test hypothesis (one at a time)
Phase 4: Implement fix (with test)
```

### Before Claiming "Done"
**verification-before-completion** - Evidence before claims
```
Run command → Paste output → Then claim
No "should work" → Only "does work" with proof
```

## 📚 Available Skills (28 total)

### 🧪 Testing & Debugging (5)
- **test-driven-development** - Write test first, watch fail, minimal code
- **systematic-debugging** - 4-phase root cause investigation
- **verification-before-completion** - Evidence before claims
- **testing-anti-patterns** - Common test pitfalls to avoid
- **condition-based-waiting** - Replace timeouts with conditions

### 🤝 Collaboration & Planning (9)
- **brainstorming** - Structured design refinement
- **writing-plans** - Zero-context implementation plans
- **executing-plans** - Batch execution with checkpoints
- **requesting-code-review** - Pre-review checklist
- **receiving-code-review** - Responding to feedback
- **dispatching-parallel-agents** - Concurrent workflows
- **subagent-driven-development** - Fast iteration
- **using-git-worktrees** - Isolated development
- **finishing-a-development-branch** - Merge/PR decisions

### 📋 Pre-Dev Workflow (8 gates)
1. **pre-dev-prd-creation** - Business requirements
2. **pre-dev-feature-map** - Feature relationships
3. **pre-dev-trd-creation** - Technical architecture
4. **pre-dev-api-design** - Component contracts
5. **pre-dev-data-model** - Entity relationships
6. **pre-dev-dependency-map** - Technology selection
7. **pre-dev-task-breakdown** - Work increments
8. **pre-dev-subtask-creation** - Atomic units

### 🔧 Meta Skills (4)
- **using-ring** - Mandatory skill discovery
- **writing-skills** - TDD for documentation
- **testing-skills-with-subagents** - Skill validation
- **sharing-skills** - Contributing back

### 🚀 Commands
- **/ring:brainstorm** - Interactive design refinement
- **/ring:write-plan** - Create implementation plan
- **/ring:execute-plan** - Execute plan in batches

### 🔍 Review Agents (3 Sequential Gates)
**Run in order - each builds on the previous:**

1. **ring:code-reviewer** (Gate 1 - Foundation)
   - Architecture, design patterns, code quality, maintainability
   - Must pass before Gate 2

2. **ring:business-logic-reviewer** (Gate 2 - Correctness)
   - Domain correctness, business rules, edge cases, requirements
   - Must pass before Gate 3

3. **ring:security-reviewer** (Gate 3 - Safety)
   - Vulnerabilities, authentication, input validation, OWASP Top 10
   - Final gate before production

**Critical: Run sequentially (Code → Business → Security), not in parallel.**

## 📋 By Situation

| Situation | Use This Skill | Key Rule |
|-----------|---------------|----------|
| Starting new feature | `brainstorming` | Research first, ask second |
| Implementing feature | `test-driven-development` | Test first, code second |
| Bug appears | `systematic-debugging` | Root cause before fix |
| Tests flaky | `condition-based-waiting` | No arbitrary timeouts |
| Ready to commit | `verification-before-completion` | Evidence before claims |
| Code complete | `requesting-code-review` | Gate 1→2→3 sequential |
| Planning work | `writing-plans` | Zero-context detail |
| Complex task | `pre-dev-*` workflow | 8 gates in order |

## ⚡ Speed Combos

### "Build This Feature" Combo
1. `/ring:brainstorm` - Design it
2. `using-git-worktrees` - Isolate work
3. `/ring:write-plan` - Plan tasks
4. `/ring:execute-plan` - Build it
5. `requesting-code-review` - Review it (Gate 1→2→3 sequential)

### "Fix This Bug" Combo
1. `systematic-debugging` - Find root cause
2. `test-driven-development` - Write test for bug
3. `verification-before-completion` - Verify fixed

### "Major Project" Combo (8 Gates)
1. `pre-dev-prd-creation` - Business requirements
2. `pre-dev-feature-map` - Feature relationships
3. `pre-dev-trd-creation` - Technical design
4. `pre-dev-api-design` - Contracts
5. `pre-dev-data-model` - Data structures
6. `pre-dev-dependency-map` - Tech choices
7. `pre-dev-task-breakdown` - Work items
8. `pre-dev-subtask-creation` - Atomic tasks

## 🛑 Universal Rules (All Skills)

### State Tracking
```
SKILL: [name]
PHASE: [current]
COMPLETED: [✓ what's done]
NEXT: [→ what's next]
EVIDENCE: [last output]
```

### When Stuck
- 3 attempts failed? → STOP, reassess
- Confused? → Say "I don't understand X"
- Blocked? → Document blocker explicitly

### TodoWrite Required
```
□ Create todos for each phase
□ Mark in_progress when starting
□ Update after each completion
```

### Exit Criteria
```
□ All steps complete
□ Verification run
□ Evidence included
□ No "should" or "probably"
```

## 🎯 Bulletproofing Features (Nov 2025)

**Every skill now enforces:**
- Mandatory check points (can't skip)
- Banned phrases (no weasel words)
- Evidence requirements (proof required)
- Time limits (prevent thrashing)
- Failure paths (know when stuck)

## 🔥 Pro Tips

1. **Skills are MANDATORY** - If one exists for your task, you must use it
2. **Evidence over claims** - Never say "works" without proof
3. **State tracking** - Always know where you are
4. **Fail fast** - 3 attempts max, then escalate
5. **Zero assumptions** - Verify everything

## Common Violations to Avoid

❌ "Let me just quickly check..." → Check for skills first
❌ "Should be working now" → Run verification
❌ "I'll test after" → Test FIRST
❌ "Simple fix" → Still need root cause
❌ "Appears correct" → Banned phrase

## Remember

> **Check for skills → Use the skill → Follow it exactly**

No exceptions. No shortcuts. No rationalization.