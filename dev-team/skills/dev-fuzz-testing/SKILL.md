---
name: ring:dev-fuzz-testing
description: |
  Gate 4 of development cycle - ensures fuzz tests exist with proper seed corpus
  to discover edge cases, crashes, and unexpected input handling.
  Runs at TASK cadence (after all subtasks complete Gate 0 + Gate 3 + Gate 9).
---

# Dev Fuzz Testing (Gate 4)

## When to use
- After unit testing complete (Gate 3)
- MANDATORY for all development tasks
- Discovers crashes and edge cases via random input generation

## Skip when
- Not inside a development cycle (ring:dev-cycle)
- Task is documentation-only, configuration-only, or non-code
- No functions accept external or user-controlled input
- Frontend-only project (fuzz testing applies to backend code)

## Sequence
**Runs before:** ring:dev-property-testing
**Runs after:** ring:dev-unit-testing

## Related
**Complementary:** ring:dev-cycle, ring:dev-unit-testing, ring:qa-analyst


## Overview

Ensure critical parsing and input handling code has **fuzz tests** to discover crashes and edge cases through random input generation.

**Core principle:** Fuzz tests find bugs you didn't think to test for. They're mandatory for all code that handles external input.

<block_condition>
- No fuzz functions = FAIL
- Seed corpus < 5 entries = FAIL
- Any crash found = FAIL (fix and re-run)
</block_condition>

## CRITICAL: Role Clarification

**This skill ORCHESTRATES. QA Analyst Agent (fuzz mode) EXECUTES.**

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Gather requirements, dispatch agent, track iterations |
| **QA Analyst Agent** | Write fuzz tests, generate corpus, run fuzz |

---

## Standards Source (Cache-First Pattern)

**Standards Source (Cache-First Pattern):** This sub-skill reads standards from `state.cached_standards` populated by dev-cycle Step 1.5. If invoked outside a cycle (standalone), it falls back to direct WebFetch with a warning. See `shared-patterns/standards-cache-protocol.md` for protocol details.

## Standards Reference

**MANDATORY:** Load testing-fuzz.md standards via the cache-first pattern below.

URL: https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-fuzz.md

**Cache-first loading protocol:**
For each required standards URL:
  IF state.cached_standards[url] exists:
    → Read content from state.cached_standards[url].content
    → Log: "Using cached standard: {url} (fetched {state.cached_standards[url].fetched_at})"
  ELSE:
    → WebFetch url (fallback — should not happen if orchestrator ran Step 1.5)
    → Log warning: "Standard {url} was not pre-cached; fetched inline"

<fetch_required>
https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-fuzz.md
</fetch_required>

---

## Step 1: Validate Input

```text
REQUIRED INPUT:
- unit_id: [TASK id — runs at task cadence, not per subtask]
- implementation_files: [union of changed files across all subtasks of this task]
- language: [go only for native fuzz]
- gate0_handoffs: [array of per-subtask Gate 0 handoffs — one entry per subtask]

OPTIONAL INPUT:
- gate3_handoff: [full Gate 3 output]

if any REQUIRED input is missing:
  → STOP and report: "Missing required input: [field]"

if language != "go":
  → STOP and report: "Native fuzz testing only supported for Go (Go 1.18+)"
```

## Step 2: Dispatch QA Analyst Agent (Fuzz Mode)

```text
Task tool:
  subagent_type: "ring:qa-analyst"
  prompt: |
    **MODE:** FUZZ TESTING (Gate 4)

    **Standards:** Load testing-fuzz.md

    **Input:**
    - Unit ID: {unit_id}
    - Implementation Files: {implementation_files}
    - Language: {language}

    **Requirements:**
    1. Create fuzz functions (FuzzXxx naming)
    2. Add seed corpus (minimum 5 entries per function)
    3. Run fuzz tests for 30 seconds
    4. Report any crashes found

    **Output Sections Required:**
    - ## Fuzz Testing Summary
    - ## Corpus Report
    - ## Handoff to Next Gate
```

## Step 3: Evaluate Results

```text
Parse agent output:

if "Status: PASS" in output:
  → Gate 4 PASSED
  → Return success with metrics

if "Status: FAIL" in output:
  → Dispatch fix to implementation agent
  → Re-run fuzz tests (max 3 iterations)
  → If still failing: ESCALATE to user
```

## Step 4: Generate Output

```text
## Fuzz Testing Summary
**Status:** {PASS|FAIL}
**Fuzz Functions:** {count}
**Corpus Entries:** {count}
**Crashes Found:** {count}

## Corpus Report
| Function | Entries | Crashes |
|----------|---------|---------|
| {function_name} | {count} | {count} |

## Handoff to Next Gate
- Ready for Gate 5 (Property Testing): {YES|NO}
- Iterations: {count}
```

---

## Severity Calibration

| Severity | Criteria | Examples |
|----------|----------|----------|
| **CRITICAL** | Crash found, security vulnerability discovered | Panic on input, buffer overflow, memory corruption |
| **HIGH** | No fuzz functions, missing corpus | Zero FuzzXxx functions, empty seed corpus |
| **MEDIUM** | Insufficient corpus, naming issues | Less than 5 corpus entries, non-standard function names |
| **LOW** | Coverage gaps, optimization | Missing edge case seeds, fuzz duration improvements |

Report all severities. CRITICAL = immediate fix and re-fuzz. HIGH = fix before gate pass. MEDIUM = fix in iteration. LOW = document.

---

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Unit tests cover edge cases" | You can't test what you don't think of. Fuzz finds unknowns. | **Write fuzz tests** |
| "Code is too simple for fuzz" | Simple code can still crash on malformed input. | **Write fuzz tests** |
| "Fuzz testing is slow" | 30 seconds per function. Crashes in production are slower. | **Write fuzz tests** |
| "We validate input anyway" | Validation can have bugs too. Fuzz tests the validators. | **Write fuzz tests** |

---
