---
name: ring:dev-sre
description: |
  Gate 2 of the development cycle. Validates observability implementation:
  structured logging with trace correlation, OpenTelemetry tracing, 90%+ code
  instrumentation coverage, context propagation.

trigger: |
  - Gate 2 of development cycle
  - After Gate 0 (implementation) and Gate 1 (devops) complete
  - Need to validate observability implementation

skip_when: |
  - Not inside a development cycle (ring:dev-cycle)
  - Task is documentation-only, configuration-only, or non-code
  - Pure library package with no runtime behavior
  - Changes are limited to CI/CD or infrastructure configuration

sequence:
  after: [ring:dev-devops]
  before: [ring:dev-unit-testing]

related:
  complementary: [ring:dev-cycle, ring:dev-implementation, ring:sre]

output_schema:
  required_sections:
    - "Validation Result"
    - "Instrumentation Coverage"
    - "Issues Found"
    - "Handoff to Next Gate"
  metrics:
    result: PASS | FAIL | NEEDS_FIXES
    instrumentation_coverage_percent: float
    iterations: integer
---

# SRE Validation (Gate 2)

**Developers IMPLEMENT observability. SRE VALIDATES it.**

| Who | Responsibility |
|-----|----------------|
| Developers (Gate 0) | Implement observability per Ring Standards |
| SRE Agent (Gate 2) | Validate correctness |
| Implementation Agent | Fix issues found by SRE |

Max 3 iterations, then escalate to user.

## Step 1: Validate Input

Required: `unit_id`, `language`, `service_type`, `implementation_agent`, `implementation_files`, `gate0_handoffs`.
Optional: `external_dependencies`, `gate1_handoff`.

## Step 2: Dispatch SRE Agent

```yaml
Task:
  subagent_type: "ring:sre"
  description: "Validate observability for {unit_id}"
  prompt: |
    ## SRE Validation Gate

    unit_id: {unit_id}
    language: {language}
    service_type: {service_type}
    files: {implementation_files}

    ## Standards
    Load via cached_standards or WebFetch:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/sre.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/observability.md (Go)

    ## Validation Checklist

    ### Structured Logging
    - [ ] JSON format (not text/plain)
    - [ ] Required fields: level, msg, trace_id, span_id, service
    - [ ] Log levels used correctly (DEBUG/INFO/WARN/ERROR)
    - [ ] No log.Print or fmt.Print in business logic
    - [ ] PII not logged

    ### OpenTelemetry Tracing
    - [ ] Spans created for all external calls (DB, HTTP, queue)
    - [ ] Trace context propagated (HTTP headers, amqp headers)
    - [ ] Span attributes include operation name and outcome
    - [ ] Error spans set StatusCode = Error + record exception

    ### Metrics
    - [ ] Request counter (method, path, status)
    - [ ] Request duration histogram
    - [ ] Error counter
    - [ ] Dependency-specific metrics (DB query duration, queue message count)

    ### Instrumentation Coverage (90% required)
    Count: files with observability / total files (excluding test, generated)

    ### /readyz (if service_type = api)
    - [ ] Endpoint exists at /readyz
    - [ ] Checks all external dependencies
    - [ ] Returns 200 OK only when all deps are up

    ## Output
    - Validation result: PASS | NEEDS_FIXES
    - Instrumentation coverage: X%
    - Issues: list with severity, file:line, description, fix
```

## Step 3: Evaluate Results

```
if validation_result = PASS:
  → Proceed to Gate 3

if validation_result = NEEDS_FIXES:
  → Extract issues list
  → Dispatch implementation_agent to fix
  → Re-dispatch SRE for re-validation
  → iterations++

if iterations >= 3:
  → Escalate to user with full issue list
```

## Fix Dispatch Template

```yaml
Task:
  subagent_type: "{implementation_agent}"
  description: "Fix SRE issues in {unit_id}"
  prompt: |
    Fix the following observability issues found by SRE:

    {issues_list}

    Follow Ring observability standards. TDD: write test first where applicable.
    Report: files changed + test results.
```

## Output Format

```markdown
## Validation Result
- unit_id / result (PASS|NEEDS_FIXES) / iterations / coverage

## Instrumentation Coverage
- X% (threshold: 90%)
- Files with observability: N/M

## Issues Found
| Severity | File:Line | Issue | Fix Applied |

## Handoff to Next Gate
- gate2_result: PASS | ESCALATED
- files_changed_in_fixes: [list]
```
