---
name: ring:dev-delivery-verification
description: |
  Delivery Verification Gate — verifies that what was requested is actually delivered
  as reachable, integrated code. Not quality review (Gate 8), not test verification
  (Gate 9) — this gate answers: "Is the requested functionality actually wired into
  the running application?" Catches dead code, uninitialized structs, unwired
  middleware, and scaffold-without-integration patterns.

trigger: |
  - After Gate 0 (implementation) completes, before advancing to Gate 1
  - After any refactoring task claims completion
  - When code is generated/scaffolded and needs integration verification

NOT_skip_when: |
  - "Code compiles" → Compilation ≠ integration. Dead code compiles.
  - "Tests pass" → Unit tests on isolated structs pass without wiring.
  - "It's just a struct/interface" → Structs that aren't instantiated are dead code.
  - "Wire will happen in next task" → Each task must deliver complete, reachable code.
  - "Time pressure" → Unwired code is worse than no code — it creates false confidence.

sequence:
  after: [ring:dev-implementation]
  before: [ring:dev-devops]

related:
  complementary: [ring:dev-cycle, ring:dev-implementation, ring:verification-before-completion, ring:requesting-code-review]

input_schema:
  required:
    - name: unit_id
      type: string
      description: "Task or subtask identifier being verified"
    - name: requirements
      type: string
      description: "Original task requirements or acceptance criteria"
    - name: files_changed
      type: array
      items: string
      description: "List of files created or modified by Gate 0"
  optional:
    - name: gate0_handoff
      type: object
      description: "Full handoff from Gate 0 implementation"

output_schema:
  format: markdown
  required_sections:
    - name: "Delivery Verification Summary"
      pattern: "^## Delivery Verification Summary"
      required: true
    - name: "Requirement Coverage Matrix"
      pattern: "^## Requirement Coverage Matrix"
      required: true
    - name: "Integration Verification"
      pattern: "^## Integration Verification"
      required: true
    - name: "Dead Code Detection"
      pattern: "^## Dead Code Detection"
      required: true
    - name: "Verdict"
      pattern: "^## Verdict"
      required: true
  metrics:
    - name: result
      type: enum
      values: [PASS, FAIL, PARTIAL]
    - name: requirements_total
      type: integer
    - name: requirements_delivered
      type: integer
    - name: requirements_missing
      type: integer
    - name: dead_code_items
      type: integer
---

# Delivery Verification Gate

## The Problem This Solves

Agents generate code that compiles and passes unit tests but is never wired into the application. This creates dead code that gives false confidence — the task appears complete, but the functionality doesn't exist at runtime.

**Real-world example:** An agent was tasked with "Add custom OpenTelemetry application metrics." It created a complete `Metrics` struct with 5 counters/histograms, wrote 12 unit tests (all passing), but never called `NewMetrics()` in the bootstrap. The code was dead. All gates passed. The problem was only discovered weeks later during a manual Grafana investigation.

## The Core Principle

```
REQUESTED ≠ CREATED ≠ DELIVERED

- REQUESTED: What the task/requirement asks for
- CREATED: What files/structs/functions were written
- DELIVERED: What code is reachable from main() at runtime

Only DELIVERED counts. CREATED without DELIVERED is dead code.
```

## The Verification Process

### Step 1: Extract Requirements from Task

Parse the original task into discrete, verifiable requirements.

```
Task: "Add custom OpenTelemetry application metrics (REFACTOR-005)"

Extracted requirements:
  R1: Metrics struct with HTTP request counters/histograms
  R2: Metrics struct with provisioning counters/histograms
  R3: Metrics struct with error counters
  R4: Metrics initialized at application startup
  R5: HTTP requests recorded via metrics
  R6: Provisioning operations recorded via metrics
  R7: Errors recorded via metrics
```

**Key insight:** R1-R3 are "code exists" requirements. R4-R7 are "code is integrated" requirements. Most agents complete R1-R3 and skip R4-R7.

### Step 2: Verify Each Requirement is DELIVERED (not just CREATED)

For each requirement, trace the path from `main()` to the delivered code:

```
R1: Metrics struct created → metrics.go ✅ CREATED
R4: Metrics initialized at startup → wire.go calls NewMetrics()? 
    → Search: grep -rn "NewMetrics" internal/bootstrap/wire*.go
    → If 0 matches: ❌ NOT DELIVERED (struct exists but never instantiated)
    → If found: ✅ DELIVERED
```

### Step 3: Integration Verification Checklist

For every new artifact created by the implementation, verify integration:

#### Structs & Types
```
For each new struct:
  [ ] Is it instantiated somewhere? (grep for NewXxx or &Xxx{})
  [ ] Is the instance stored/used? (not just _ = NewXxx())
  [ ] Is it reachable from main() → bootstrap → wire → handler chain?
```

#### Functions & Methods
```
For each new exported function:
  [ ] Is it called from at least one non-test file?
  [ ] Is the caller itself reachable from main()?
  [ ] If it's a method: is the receiver struct instantiated and used?
```

#### Middleware
```
For each new middleware:
  [ ] Is it registered in the router/fiber middleware chain?
  [ ] Is it registered in the correct ORDER? (e.g., telemetry before auth)
  [ ] Are its dependencies injected? (not nil at runtime)
```

#### Interfaces & Implementations
```
For each new interface implementation:
  [ ] Is the concrete type registered/injected via DI/wire?
  [ ] Is the interface actually used at a call site?
  [ ] Is the call site reachable from main()?
```

#### Config & Environment Variables
```
For each new config field:
  [ ] Is it read from environment? (env tag or os.Getenv)
  [ ] Is it passed to the component that uses it?
  [ ] Does the component's behavior change based on the value?
```

#### Dependencies (go.mod)
```
For each new dependency added:
  [ ] Is it imported in at least one non-test .go file?
  [ ] Is the import used (not just side-effect import)?
```

### Step 4: Dead Code Detection

Run language-specific dead code analysis:

#### Go
```bash
# Find unexported functions never called internally
grep -rn "^func [a-z]" internal/ --include="*.go" | while read line; do
  func_name=$(echo "$line" | grep -oP 'func \K[a-z]\w+')
  file=$(echo "$line" | cut -d: -f1)
  pkg_dir=$(dirname "$file")
  count=$(grep -rn "$func_name" "$pkg_dir" --include="*.go" | grep -v "_test.go" | wc -l)
  if [ "$count" -le 1 ]; then
    echo "DEAD: $func_name in $file (only defined, never called)"
  fi
done

# Find exported types never referenced outside their package
# Find structs with New* constructors where New* is never called outside tests
```

#### Integration Reachability (Go-specific)
```bash
# For each new file, check if its package is imported by bootstrap/wire/main
new_files=$(git diff --name-only HEAD~1 | grep "\.go$" | grep -v "_test.go")
for f in $new_files; do
  pkg=$(head -1 "$f" | grep -oP 'package \K\w+')
  pkg_path=$(dirname "$f")
  # Check if any bootstrap/wire/main file imports this package
  importers=$(grep -rn "\".*$pkg_path\"" internal/bootstrap/ cmd/ --include="*.go" | grep -v "_test.go")
  if [ -z "$importers" ]; then
    echo "WARNING: Package $pkg_path not imported by bootstrap/cmd"
  fi
done
```

### Step 5: Requirement Coverage Matrix

Build and output the matrix:

```markdown
## Requirement Coverage Matrix

| # | Requirement | Created | Integrated | Reachable | Status |
|---|-------------|---------|------------|-----------|--------|
| R1 | Metrics struct with HTTP counters | ✅ metrics.go | ✅ NewMetrics() in wire.go | ✅ via Application.Metrics | ✅ DELIVERED |
| R2 | Metrics struct with provisioning counters | ✅ metrics.go | ✅ NewMetrics() in wire.go | ✅ via Application.Metrics | ✅ DELIVERED |
| R4 | Metrics initialized at startup | ✅ NewMetrics() exists | ✅ Called in NewApplication() | ✅ main→InitServers→NewApplication | ✅ DELIVERED |
| R5 | HTTP requests recorded | ✅ RecordHTTPRequest() exists | ❌ Never called in any handler | ❌ Dead code | ❌ NOT DELIVERED |
```

### Step 6: Verdict

```
PASS: All requirements have status DELIVERED
       AND dead code count = 0
       AND all integration checks pass

PARTIAL: Some requirements DELIVERED, some NOT DELIVERED
         → List specific gaps
         → Agent MUST fix before advancing

FAIL: Critical requirements NOT DELIVERED
      OR significant dead code introduced
      → Return to Gate 0
```

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "The struct is there, wiring is a separate task" | Unwired struct = dead code. Each task must deliver complete functionality. | **Wire it NOW or mark task as incomplete** |
| "Tests prove it works" | Tests on isolated structs prove the struct works in isolation. Not that it works in the app. | **Verify reachability from main()** |
| "It compiles, so it's integrated" | Compilation doesn't prove integration. Unused imports compile too. | **Trace call path from main()** |
| "The next PR will wire it" | The next PR is not guaranteed. Deliver complete or don't deliver. | **Complete integration in this task** |
| "It's just scaffolding" | Scaffolding without integration is dead code with extra steps. | **Either wire it or don't create it** |
| "Review will catch it" | Review catches quality issues, not integration gaps. Different concerns. | **Verify integration explicitly** |
| "Go vet would catch unused code" | Go vet catches unused variables, not unused exported types/functions. | **Run integration verification** |

## Integration with dev-cycle

This gate runs as **Gate 0.5** — after implementation (Gate 0), before DevOps (Gate 1):

```
Gate 0:   Implementation (write code)
Gate 0.5: Delivery Verification (verify code is wired) ← THIS GATE
Gate 1:   DevOps (infrastructure)
Gate 2:   SRE (reliability)
Gate 3:   Unit Testing
...
```

If Gate 0.5 returns PARTIAL or FAIL:
1. List specific undelivered requirements
2. Return to Gate 0 with explicit instructions: "Wire the following: [list]"
3. Re-run Gate 0.5 after fixes
4. Only advance to Gate 1 when Gate 0.5 returns PASS

## Example Output

```markdown
## Delivery Verification Summary

Task: REFACTOR-005 — Add custom OpenTelemetry application metrics
Gate 0 Agent: ring:backend-engineer-golang
Files Changed: internal/bootstrap/metrics.go, internal/bootstrap/metrics_test.go

## Requirement Coverage Matrix

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Metrics struct with 5 counters/histograms | ✅ DELIVERED | metrics.go:L82-L135 |
| R2 | NewMetrics() constructor | ✅ DELIVERED | metrics.go:L140-L195 |
| R3 | RecordHTTPRequest() method | ⚠️ CREATED NOT DELIVERED | metrics.go:L210, never called |
| R4 | RecordProvisioningOperation() method | ⚠️ CREATED NOT DELIVERED | metrics.go:L230, never called |
| R5 | RecordError() method | ⚠️ CREATED NOT DELIVERED | metrics.go:L250, never called |
| R6 | Metrics initialized at startup | ❌ NOT DELIVERED | NewMetrics() not called in wire.go |
| R7 | HTTP requests recorded in handlers | ❌ NOT DELIVERED | No handler calls RecordHTTPRequest() |

## Integration Verification

- [ ] ❌ `NewMetrics()` not called in `wire.go` or `NewApplication()`
- [ ] ❌ `Metrics` not added to `Application` struct
- [ ] ❌ `RecordHTTPRequest()` not called in any handler or middleware
- [ ] ❌ `RecordProvisioningOperation()` not called in any service

## Dead Code Detection

| Item | Location | Issue |
|------|----------|-------|
| `NewMetrics()` | metrics.go:140 | Constructor never called outside tests |
| `RecordHTTPRequest()` | metrics.go:210 | Method never called outside tests |
| `RecordProvisioningOperation()` | metrics.go:230 | Method never called outside tests |
| `RecordError()` | metrics.go:250 | Method never called outside tests |

## Verdict

**FAIL** — 2/7 requirements delivered. 4 dead code items introduced.

Return to Gate 0 with instructions:
1. Add `Metrics *Metrics` to Application struct in wire.go
2. Call `NewMetrics()` in NewApplication() after telemetry init
3. Create HTTP metrics middleware calling RecordHTTPRequest()
4. Inject metrics into TenantServiceHandler and call Record* methods
5. Inject metrics into tenant-service service for provisioning tracking
```
