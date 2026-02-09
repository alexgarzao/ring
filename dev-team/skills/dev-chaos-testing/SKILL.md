---
name: ring-dev-chaos-testing
title: Development cycle chaos testing (Gate 7)
category: development-cycle
tier: 1
when_to_use: |
  Use after integration testing (Gate 6) is complete.
  MANDATORY for all development tasks with external dependencies - verifies graceful degradation under failure.
description: |
  Gate 7 of development cycle - ensures chaos tests exist using Toxiproxy
  to verify graceful degradation under connection loss, latency, and partitions.

trigger: |
  - After integration testing complete (Gate 6)
  - MANDATORY for all development tasks with external dependencies
  - Verifies system behavior under failure conditions

NOT_skip_when: |
  - "Infrastructure is reliable" - All infrastructure fails eventually. Be prepared.
  - "Integration tests cover failures" - Integration tests verify happy path. Chaos verifies failures.
  - "Toxiproxy is complex" - One container, 20 minutes setup. Prevents production incidents.

sequence:
  after: [ring-dev-integration-testing]
  before: [ring-requesting-code-review]

related:
  complementary: [ring-dev-cycle, ring-dev-integration-testing, ring-qa-analyst]

input_schema:
  required:
    - name: unit_id
      type: string
      description: "Task or subtask identifier"
    - name: external_dependencies
      type: array
      items: string
      description: "External services (postgres, redis, rabbitmq, etc.)"
    - name: language
      type: string
      enum: [go, typescript]
      description: "Programming language"
  optional:
    - name: gate6_handoff
      type: object
      description: "Full handoff from Gate 6 (integration testing)"

output_schema:
  format: markdown
  required_sections:
    - name: "Chaos Testing Summary"
      pattern: "^## Chaos Testing Summary"
      required: true
    - name: "Failure Scenarios"
      pattern: "^## Failure Scenarios"
      required: true
    - name: "Handoff to Next Gate"
      pattern: "^## Handoff to Next Gate"
      required: true
  metrics:
    - name: result
      type: enum
      values: [PASS, FAIL]
    - name: dependencies_tested
      type: integer
    - name: scenarios_tested
      type: integer
    - name: recovery_verified
      type: boolean
    - name: iterations
      type: integer

verification:
  automated:
    - command: "grep -rn 'TestIntegration_Chaos_' --include='*_test.go' ."
      description: "Chaos test functions exist"
      success_pattern: "TestIntegration_Chaos_"
    - command: "grep -rn 'CHAOS.*1' --include='*_test.go' ."
      description: "CHAOS env check present"
      success_pattern: "CHAOS"
  manual:
    - "Chaos tests follow TestIntegration_Chaos_{Component}_{Scenario} naming"
    - "All external dependencies have failure scenarios"
    - "Recovery verified after each failure injection"

examples:
  - name: "Chaos tests for database operations"
    input:
      unit_id: "task-001"
      external_dependencies: ["postgres", "redis"]
      language: "go"
    expected_output: |
      ## Chaos Testing Summary
      **Status:** PASS
      **Dependencies Tested:** 2
      **Scenarios Tested:** 6
      **Recovery Verified:** Yes

      ## Failure Scenarios
      | Component | Scenario | Status | Recovery |
      |-----------|----------|--------|----------|
      | PostgreSQL | Connection Loss | PASS | Yes |
      | PostgreSQL | High Latency | PASS | Yes |
      | PostgreSQL | Network Partition | PASS | Yes |
      | Redis | Connection Loss | PASS | Yes |
      | Redis | High Latency | PASS | Yes |
      | Redis | Network Partition | PASS | Yes |

      ## Handoff to Next Gate
      - Ready for Gate 8 (Code Review): YES
---

# Dev Chaos Testing (Gate 7)

## Overview

Ensure code handles **failure conditions gracefully** by injecting faults using Toxiproxy. Verify connection loss, latency, and network partitions don't cause crashes.

**Core principle:** All infrastructure fails. Chaos testing ensures your code handles it gracefully.

<block_condition>
- No chaos tests = FAIL
- Any dependency without failure test = FAIL
- Recovery not verified = FAIL
- System crashes on failure = FAIL
</block_condition>

## CRITICAL: Role Clarification

**This skill ORCHESTRATES. QA Analyst Agent (chaos mode) EXECUTES.**

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Gather requirements, dispatch agent, track iterations |
| **QA Analyst Agent** | Write chaos tests, setup Toxiproxy, verify recovery |

---

## Standards Reference

**MANDATORY:** Load testing-chaos.md standards via WebFetch.

<fetch_required>
https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-chaos.md
</fetch_required>

---

## Step 1: Validate Input

```text
REQUIRED INPUT:
- unit_id: [task/subtask being tested]
- external_dependencies: [postgres, redis, rabbitmq, etc.]
- language: [go|typescript]

OPTIONAL INPUT:
- gate6_handoff: [full Gate 6 output]

if any REQUIRED input is missing:
  → STOP and report: "Missing required input: [field]"

if external_dependencies is empty:
  → STOP and report: "No external dependencies found - chaos testing requires dependencies"
```

## Step 2: Dispatch QA Analyst Agent (Chaos Mode)

```text
Task tool:
  subagent_type: "ring-qa-analyst"
  model: "opus"
  prompt: |
    **MODE:** CHAOS TESTING (Gate 7)

    **Standards:** Load testing-chaos.md

    **Input:**
    - Unit ID: {unit_id}
    - External Dependencies: {external_dependencies}
    - Language: {language}

    **Requirements:**
    1. Setup Toxiproxy infrastructure in tests/utils/chaos/
    2. Create chaos tests (TestIntegration_Chaos_{Component}_{Scenario} naming)
    3. Use dual-gate pattern (CHAOS=1 env + testing.Short())
    4. Test failure scenarios: Connection Loss, High Latency, Network Partition
    5. Verify 5-phase structure: Normal → Inject → Verify → Restore → Recovery

    **Output Sections Required:**
    - ## Chaos Testing Summary
    - ## Failure Scenarios
    - ## Handoff to Next Gate
```

## Step 3: Evaluate Results

```text
Parse agent output:

if "Status: PASS" in output:
  → Gate 7 PASSED
  → Return success with metrics

if "Status: FAIL" in output:
  → Dispatch fix to implementation agent
  → Re-run chaos tests (max 3 iterations)
  → If still failing: ESCALATE to user
```

## Step 4: Generate Output

```text
## Chaos Testing Summary
**Status:** {PASS|FAIL}
**Dependencies Tested:** {count}
**Scenarios Tested:** {count}
**Recovery Verified:** {Yes|No}

## Failure Scenarios
| Component | Scenario | Status | Recovery |
|-----------|----------|--------|----------|
| {component} | {scenario} | {PASS|FAIL} | {Yes|No} |

## Handoff to Next Gate
- Ready for Gate 8 (Code Review): {YES|NO}
- Iterations: {count}
```

---

## Failure Scenarios by Dependency

| Dependency | Required Scenarios |
|------------|-------------------|
| PostgreSQL | Connection Loss, High Latency, Network Partition |
| Redis | Connection Loss, High Latency, Timeout |
| RabbitMQ | Connection Loss, Network Partition, Slow Consumer |
| HTTP APIs | Timeout, 5xx Errors, Connection Refused |

---

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Infrastructure is reliable" | AWS, GCP, Azure all have outages. Your code must handle them. | **Write chaos tests** |
| "Integration tests cover failures" | Integration tests verify happy path. Chaos tests verify failure handling. | **Write chaos tests** |
| "Toxiproxy is complex" | One container. 20 minutes setup. Prevents production incidents. | **Write chaos tests** |
| "We have monitoring" | Monitoring detects problems. Chaos testing prevents them. | **Write chaos tests** |
| "Circuit breakers handle it" | Circuit breakers need testing too. Chaos tests verify they work. | **Write chaos tests** |

---
