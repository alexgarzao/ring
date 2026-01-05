---
name: testing-agents-with-subagents
description: |
  Agent testing methodology - run agents with test inputs, observe outputs,
  iterate until outputs are accurate and well-structured.
license: MIT
compatibility: opencode
metadata:
  trigger: "Before deploying new agent, after editing agent, agent produces structured outputs"
  skip_when: "Agent is simple passthrough, agent already tested for use case"
  source: ring-default
---

# Testing Agents With Subagents

## Related Skills

**Complementary:** test-driven-development

---

## Overview

**Testing agents is TDD applied to AI worker definitions.**

You run agents with known test inputs (RED - observe incorrect outputs), fix the agent definition (GREEN - outputs now correct), then handle edge cases (REFACTOR - robust under all conditions).

**Core principle:** If you didn't run an agent with test inputs and verify its outputs, you don't know if the agent works correctly.

**REQUIRED BACKGROUND:** You MUST understand `test-driven-development` before using this skill. That skill defines the fundamental RED-GREEN-REFACTOR cycle. This skill provides agent-specific test formats (test inputs, output verification, accuracy metrics).

**Key difference from testing-skills-with-subagents:**
- **Skills** = instructions that guide behavior; test if agent follows rules under pressure
- **Agents** = separate instances via Task tool; test if they produce correct outputs

## The Iron Law

```
NO AGENT DEPLOYMENT WITHOUT RED-GREEN-REFACTOR TESTING FIRST
```

About to deploy an agent without completing the test cycle? You have ONLY one option:

### STOP. TEST FIRST. THEN DEPLOY.

**You CANNOT:**
- "Deploy and monitor for issues"
- "Test with first real usage"
- "Quick smoke test is enough"
- "Tested manually in Claude UI"
- "One test case passed"
- "Agent prompt looks correct"
- "Based on working template"
- "Deploy now, test in parallel"
- "Production is down, no time to test"

**ZERO exceptions. Simple agent, expert confidence, time pressure, production outage - NONE override testing.**

## When to Use

Test agents that:
- Analyze code/designs and produce findings (reviewers)
- Generate structured outputs (planners, analyzers)
- Make decisions or categorizations (severity, priority)
- Have defined output schemas that must be followed
- Are used in parallel workflows where consistency matters

**Test exemptions require explicit human partner approval:**
- Simple pass-through agents (just reformatting) - **only if human partner confirms**
- Agents without structured outputs - **only if human partner confirms**
- **You CANNOT self-determine test exemption**
- **When in doubt -> TEST**

## TDD Mapping for Agent Testing

| TDD Phase | Agent Testing | What You Do |
|-----------|---------------|-------------|
| **RED** | Run with test inputs | Dispatch agent, observe incorrect/incomplete outputs |
| **Verify RED** | Document failures | Capture exact output issues verbatim |
| **GREEN** | Fix agent definition | Update prompt/schema to address failures |
| **Verify GREEN** | Re-run tests | Agent now produces correct outputs |
| **REFACTOR** | Test edge cases | Ambiguous inputs, empty inputs, complex scenarios |
| **Stay GREEN** | Re-verify all | Previous tests still pass after changes |

Same cycle as code TDD, different test format.

## RED Phase: Baseline Testing (Observe Failures)

**Goal:** Run agent with known test inputs - observe what's wrong, document exact failures.

**Process:**
- [ ] **Create test inputs** (known issues, edge cases, clean inputs)
- [ ] **Run agent** - dispatch via Task tool with test inputs
- [ ] **Compare outputs** - expected vs actual
- [ ] **Document failures** - missing findings, wrong severity, bad format
- [ ] **Identify patterns** - which input types cause failures?

### Test Input Categories

| Category | Purpose | Example |
|----------|---------|---------|
| **Known Issues** | Verify agent finds real problems | Code with SQL injection, hardcoded secrets |
| **Clean Inputs** | Verify no false positives | Well-written code with no issues |
| **Edge Cases** | Verify robustness | Empty files, huge files, unusual patterns |
| **Ambiguous Cases** | Verify judgment | Code that could go either way |
| **Severity Calibration** | Verify severity accuracy | Mix of critical, high, medium, low issues |

### Minimum Test Suite Requirements

Before deploying ANY agent, you MUST have:

| Agent Type | Minimum Test Cases | Required Coverage |
|------------|-------------------|-------------------|
| **Reviewer agents** | 6 tests | 2 known issues, 2 clean, 1 edge case, 1 ambiguous |
| **Analyzer agents** | 5 tests | 2 typical, 1 empty, 1 large, 1 malformed |
| **Decision agents** | 4 tests | 2 clear cases, 2 boundary cases |
| **Planning agents** | 5 tests | 2 standard, 1 complex, 1 minimal, 1 edge case |

**Fewer tests = incomplete testing = DO NOT DEPLOY.**

## GREEN Phase: Fix Agent Definition (Make Tests Pass)

Write/update agent definition addressing specific failures documented in RED phase.

**Common fixes:**

| Failure Type | Fix Approach |
|--------------|--------------|
| Missing findings | Add explicit instructions to check for X |
| Wrong severity | Add severity calibration examples |
| Bad output format | Add output schema with examples |
| False positives | Add "don't flag X when Y" instructions |
| Incomplete analysis | Add "always check A, B, C" checklist |

## REFACTOR Phase: Edge Cases and Robustness

Agent passes basic tests? Now test edge cases.

### Edge Case Categories

| Category | Test Cases |
|----------|------------|
| **Empty/Null** | Empty file, null input, whitespace only |
| **Large** | 10K line file, deeply nested code |
| **Unusual** | Minified code, generated code, config files |
| **Multi-language** | Mixed JS/TS, embedded SQL, templates |
| **Ambiguous** | Code that could be good or bad depending on context |

## Agent Testing Checklist

**RED Phase:** Create test inputs (known issues, clean, edge cases) -> Run agent -> Document failures verbatim

**GREEN Phase:** Update agent definition -> Re-run tests -> All pass

**REFACTOR Phase:** Test edge cases -> Test stress scenarios -> Add explicit handling -> Verify consistency (3+ runs) -> Test parallel integration (if applicable) -> Re-run ALL tests after each change

**Metrics (reviewer agents):** True positive >95%, False positive <10%, False negative <5%, Severity accuracy >90%, Schema compliance 100%, Consistency >95%

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Testing only "happy path" inputs | Include ambiguous + edge cases |
| Not documenting exact outputs | Capture verbatim, compare to expected |
| Fixing without re-running all tests | Re-run entire suite after each change |
| Testing single agent in isolation (parallel workflow) | Test parallel dispatch + aggregation |
| Not testing consistency | Run same input 3+ times |
| Skipping severity calibration | Add explicit severity examples |
| Single test case validation | Minimum 4-6 test cases per agent type |
| Skipping re-test for "small" changes | Re-run full suite after ANY modification |

## Rationalization Table

| Excuse | Reality |
|--------|---------|
| "Agent prompt is obviously correct" | Obvious prompts fail in practice. Test proves correctness. |
| "Tested manually in Claude UI" | Ad-hoc != reproducible. No baseline documented. |
| "One test case passed" | Sample size = 1 proves nothing. Need 4-6 cases minimum. |
| "Will test after first production use" | Production is not QA. Test before deployment. Always. |
| "Reading prompt is sufficient review" | Reading != executing. Must run agent with inputs. |
| "Changes are small, re-test unnecessary" | Small changes cause big failures. Re-run full suite. |
| "Based agent on proven template" | Templates need validation for your use case. Test anyway. |
| "Production is down, no time to test" | Deploying untested fix may make outage worse. Test first. |

## The Bottom Line

**Agent testing IS TDD. Same principles, same cycle, same benefits.**

If you wouldn't deploy code without tests, don't deploy agents without testing them.

RED-GREEN-REFACTOR for agents works exactly like RED-GREEN-REFACTOR for code:
1. **RED:** See what's wrong (run with test inputs)
2. **GREEN:** Fix it (update agent definition)
3. **REFACTOR:** Make it robust (edge cases, consistency)

**Evidence before deployment. Always.**
