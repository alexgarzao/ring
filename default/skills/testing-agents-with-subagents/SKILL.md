---
name: ring:testing-agents-with-subagents
description: |
  Agent testing methodology - run agents with test inputs, observe outputs,
  iterate until outputs are accurate and well-structured.

trigger: |
  - Before deploying a new agent
  - After editing an existing agent
  - Agent produces structured outputs that must be accurate

skip_when: |
  - Simple pass-through agent (human partner must confirm)
  - Agent already tested for this use case

related:
  complementary: [ring:test-driven-development]
---

# Testing Agents With Subagents

**Testing agents is TDD applied to AI worker definitions.** Run agents with known test inputs (RED), fix agent definition (GREEN), then test edge cases (REFACTOR).

**Prerequisite:** Understand `ring:test-driven-development` first — same cycle, agent-specific test format.

**Key difference:** Skills = instructions that guide behavior. Agents = separate Claude instances via Task tool; test if they produce correct outputs.

## Iron Law

```
NO AGENT DEPLOYMENT WITHOUT RED-GREEN-REFACTOR TESTING FIRST
```

**Test exemptions require explicit human partner approval.** You cannot self-determine exemption.

## TDD Mapping for Agent Testing

| TDD Phase | Agent Testing | What You Do |
|-----------|---------------|-------------|
| RED | Run with test inputs | Dispatch agent, document exact output failures verbatim |
| GREEN | Fix agent definition | Update prompt/schema to address failures |
| Verify GREEN | Re-run all tests | Agent now produces correct outputs |
| REFACTOR | Test edge cases | Empty, large, ambiguous, multi-language inputs |
| Stay GREEN | Re-verify all | Previous tests still pass after changes |

## Minimum Test Suite Requirements

| Agent Type | Minimum Test Cases | Required Coverage |
|------------|-------------------|-------------------|
| Reviewer agents | 6 tests | 2 known issues, 2 clean, 1 edge case, 1 ambiguous |
| Analyzer agents | 5 tests | 2 typical, 1 empty, 1 large, 1 malformed |
| Decision agents | 4 tests | 2 clear cases, 2 boundary cases |
| Planning agents | 5 tests | 2 standard, 1 complex, 1 minimal, 1 edge case |

**Fewer tests = incomplete testing = DO NOT DEPLOY.**

## RED Phase: Baseline Testing

Test input categories: known issues (verify finds real problems), clean inputs (verify no false positives), edge cases (empty, huge, unusual), ambiguous cases (context-dependent), severity calibration (mix of critical/high/medium/low).

Run agent via Task tool → **document exact output verbatim** (don't summarize).

## GREEN Phase: Fix Agent Definition

Address specific failures from RED phase:

| Failure Type | Fix |
|--------------|-----|
| Missing findings | Add explicit instructions to check for X |
| Wrong severity | Add severity calibration examples |
| Bad output format | Add output schema with examples |
| False positives | Add "don't flag X when Y" instructions |

Re-run ALL test cases after fixing. Continue until all pass.

## Verify GREEN: Accuracy Metrics

| Metric | Target |
|--------|--------|
| True Positives | 100% |
| False Positives | <10% |
| False Negatives | <5% |
| Severity Accuracy | >90% |
| Schema Compliance | 100% |

**Consistency:** Run same input 3 times → outputs should be identical.

## REFACTOR Phase: Edge Cases

| Category | Test Cases |
|----------|------------|
| Empty/Null | Empty file, null input, whitespace only |
| Large | 10K line file, deeply nested code |
| Unusual | Minified code, generated code, config files |
| Ambiguous | Context-dependent (local dev comment, etc.) |

**Re-run ALL tests after every agent modification** — one-word prompt changes can alter LLM behavior completely.

## Testing Parallel Workflows

When agents run in parallel: test combined workflow for parallel consistency (same input → findings should align) and aggregation (same issue from multiple reviewers → consistent severity).

## Prohibited Shortcuts

None of these substitute for documented test runs:
- Reading agent definition carefully
- Manual testing in Claude UI
- Basing on proven template
- Expert prompt engineering intuition
- "Deploy now, test in parallel"
