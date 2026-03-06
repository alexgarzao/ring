---
name: ring:dev-delivery-verification
version: 1.0.0
description: |
  Delivery Verification Gate — verifies that what was requested is actually delivered
  as reachable, integrated code. Not quality review (Gate 8), not test verification
  (Gate 9) — this gate answers: "Is every requirement from the original task actually
  functioning in the running application?" Applies to ANY task type: features, refactors,
  fixes, infrastructure, API endpoints, middleware, business logic, integrations.

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
  - "It's a simple task" → Simple tasks still need verification. Partial delivery is not delivery.

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
    - name: "Return to Gate 0"
      pattern: "^## Return to Gate 0"
      required: true
      description: "Mandatory when verdict is PARTIAL or FAIL. Lists specific undelivered requirements with fix instructions for Gate 0."
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
    - name: remediation_items
      type: integer
      description: "Number of fix instructions returned to Gate 0 (0 when PASS)"
---

# Delivery Verification Gate

## The Problem This Solves

Agents generate code that compiles and passes unit tests but doesn't actually deliver what was requested. The code exists in the repo but is never wired, never called, never reachable at runtime. This applies to **any kind of task** — not just infrastructure or observability, but features, API endpoints, business logic, integrations, refactors, everything.

**The pattern is always the same:** agent creates artifacts (structs, functions, handlers, middleware, config, migrations) that look complete in isolation, but are never connected to the application's execution path. The task appears done. It's not.

## The Core Principle

```
REQUESTED ≠ CREATED ≠ DELIVERED

- REQUESTED: What the task/requirement asks for
- CREATED: What files/structs/functions were written
- DELIVERED: What is actually functioning in the running application

Only DELIVERED counts. CREATED without DELIVERED is dead code.
This applies to EVERY task type, not just infrastructure.
```

## The Verification Process

### Step 1: Extract Requirements from the Original Task

Parse the original task (as given to Gate 0) into discrete, verifiable requirements. **Every requirement the task asks for must become a line item.** Don't filter by type — if it was requested, it must be verified.

**Examples across different task types:**

#### Feature task: "Add tenant suspension with email notification"
```
R1: Suspend endpoint accepts tenant ID and reason
R2: Tenant status changes to 'suspended' in database
R3: All active connections for tenant are closed
R4: Email notification sent to tenant admin
R5: Subsequent API calls from suspended tenant return 403
R6: Suspension is logged with audit trail
```

#### Refactor task: "Migrate authentication from custom JWT to lib-auth middleware"
```
R1: lib-auth middleware replaces custom JWT validation
R2: All protected routes use new middleware
R3: Custom JWT code removed (no dead code left)
R4: Token format backward compatible (existing tokens still work)
R5: Authorization checks use lib-auth's Authorize() method
R6: M2M flow uses lib-auth's GetApplicationToken()
```

#### Fix task: "Fix race condition in connection pool during tenant eviction"
```
R1: Mutex protects concurrent access to connections map
R2: Eviction checks connection state before closing
R3: In-flight requests complete before connection is removed
R4: Test reproduces the race condition (fails without fix)
R5: Test passes with the fix applied
```

#### Infrastructure task: "Add Redis caching to tenant config lookups"
```
R1: Cache interface defined with Get/Set/Invalidate
R2: In-memory implementation as default (zero config)
R3: Redis implementation as opt-in
R4: Client uses cache before HTTP fallback
R5: Cache TTL is configurable
R6: Cache invalidation on config change
R7: Cache metrics (hit/miss) recorded
```

**Key insight:** Every task has "code exists" requirements AND "code is integrated" requirements. Agents consistently complete the first and skip the second. This gate catches that gap.

### Step 2: Verify Each Requirement is DELIVERED (not just CREATED)

For each requirement, answer THREE questions:

1. **Does the code exist?** (file, struct, function, migration, config)
2. **Is it connected?** (called, imported, registered, wired, injected)
3. **Is it reachable at runtime?** (trace path from main() or entry point)

```
Example verification:

R1: "Suspend endpoint accepts tenant ID and reason"
  1. Code exists? → handler.go:SuspendTenant() ✅
  2. Connected? → RegisterRoutes() includes DELETE /tenants/:id/suspend? 
     → grep -rn "Suspend" internal/bootstrap/wire*.go internal/adapters/http/
     → Found in RegisterRoutes() ✅
  3. Reachable? → main→InitServers→initHTTPServer→RegisterRoutes→SuspendTenant ✅
  → Status: ✅ DELIVERED

R4: "Email notification sent to tenant admin"
  1. Code exists? → notifier.go:SendSuspensionEmail() ✅
  2. Connected? → Called from SuspendTenant handler?
     → grep -rn "SendSuspensionEmail" internal/ --include="*.go" | grep -v test
     → 0 matches outside tests ❌
  3. Reachable? → N/A (not connected)
  → Status: ❌ CREATED NOT DELIVERED — function exists but never called
```

### Step 3: Integration Verification Checklist

For **every new artifact** created by Gate 0, verify integration based on its type:

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

#### API Endpoints & Routes
```
For each new endpoint:
  [ ] Is the handler function registered in the router?
  [ ] Is the route path correct and matches the spec?
  [ ] Are required middleware applied (auth, validation, telemetry)?
  [ ] Does a request to this endpoint reach the handler? (trace route registration)
```

#### Middleware
```
For each new middleware:
  [ ] Is it registered in the router/fiber middleware chain?
  [ ] Is it registered in the correct ORDER? (e.g., telemetry before auth)
  [ ] Are its dependencies injected? (not nil at runtime)
```

#### Database Changes
```
For each new migration/schema change:
  [ ] Is the migration file created with up AND down?
  [ ] Is the new column/table used by at least one repository method?
  [ ] Is the repository method called by a service?
  [ ] Is the service called by a handler or consumer?
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

#### Event Publishers & Consumers
```
For each new event:
  [ ] Is the publisher called at the right business moment?
  [ ] Is the consumer registered and listening?
  [ ] Is the event schema consistent between publisher and consumer?
```

#### Dependencies (go.mod / package.json)
```
For each new dependency added:
  [ ] Is it imported in at least one non-test file?
  [ ] Is the import used (not just side-effect import)?
```

### Step 4: Dead Code Detection

Identify any code created by Gate 0 that is not reachable:

#### Go
```bash
# Use files_changed from Gate 0 handoff (NOT git diff — avoids drift on stacked/squashed commits)
# files_changed is provided as input to this gate
if [ -z "$files_changed" ]; then
  echo "ERROR: files_changed not provided. Cannot verify delivery."
  exit 1
fi
changed_files=$(echo "$files_changed" | tr ',' '\n' | grep "\.go$" | grep -v "_test.go")
for f in $changed_files; do
  # Extract exported function/method names
  grep -oP 'func (\(.*?\) )?(\K[A-Z]\w+)' "$f" | while read func_name; do
    # Count non-test references across the repo
    refs=$(grep -rn "$func_name" --include="*.go" . | grep -v "_test.go" | grep -v "^$f:" | wc -l)
    if [ "$refs" -eq 0 ]; then
      echo "DEAD: $func_name in $f (defined but never referenced outside tests)"
    fi
  done
done
```

```bash
# For each changed file, check if its package is imported by bootstrap/wire/main
for f in $changed_files; do
  pkg_path=$(dirname "$f")
  importers=$(grep -rn "\".*$pkg_path\"" internal/bootstrap/ cmd/ --include="*.go" | grep -v "_test.go")
  if [ -z "$importers" ]; then
    echo "WARNING: Package $pkg_path not imported by bootstrap/cmd — code may be unreachable"
  fi
done
```

#### TypeScript
```bash
# Use files_changed from Gate 0 handoff
changed_ts_files=$(echo "$files_changed" | tr ',' '\n' | grep "\.ts$" | grep -v "\.test\.\|\.spec\.")
for f in $changed_ts_files; do
  grep -oP 'export (function|class|const|interface) \K\w+' "$f" | while read name; do
    refs=$(grep -rn "import.*$name\|require.*$name" --include="*.ts" src/ | grep -v "$f" | wc -l)
    if [ "$refs" -eq 0 ]; then
      echo "DEAD: $name in $f (exported but never imported)"
    fi
  done
done
```

### Step 5: Requirement Coverage Matrix

Build and output the full matrix — one row per requirement extracted in Step 1:

```markdown
## Requirement Coverage Matrix

| # | Requirement | Created | Connected | Reachable | Status |
|---|-------------|---------|-----------|-----------|--------|
| R1 | [requirement text] | ✅ file:line | ✅ called by X | ✅ main→...→here | ✅ DELIVERED |
| R2 | [requirement text] | ✅ file:line | ❌ never called | ❌ dead code | ❌ NOT DELIVERED |
| R3 | [requirement text] | ❌ not found | — | — | ❌ NOT CREATED |
```

**Every requirement from Step 1 MUST appear in this matrix.** No filtering, no "this one is obvious." If it was requested, it gets a row.

### Step 6: Verdict

```
PASS: ALL requirements have status DELIVERED
      AND dead code count = 0
      AND all integration checks pass

PARTIAL: Some requirements DELIVERED, some NOT DELIVERED
         → List specific gaps with fix instructions
         → Agent MUST fix before advancing to Gate 1

FAIL: Critical requirements NOT DELIVERED
      OR majority of requirements NOT DELIVERED
      OR significant dead code introduced
      → Return to Gate 0 with explicit instructions
```

**Verdict is based on the original task requirements, not on code quality.** Quality is Gate 8's job. This gate only answers: "Was the requested work actually delivered?"

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "The struct is there, wiring is a separate task" | Unwired struct = dead code. Each task must deliver complete functionality. | **Wire it NOW or mark task as incomplete** |
| "Tests prove it works" | Tests on isolated code prove it works in isolation. Not that it works in the app. | **Verify reachability from main()** |
| "It compiles, so it's integrated" | Compilation doesn't prove integration. Unused code compiles. | **Trace call path from main()** |
| "The next PR will wire it" | The next PR is not guaranteed. Deliver complete or don't deliver. | **Complete integration in this task** |
| "It's just scaffolding" | Scaffolding without integration is dead code with extra steps. | **Either wire it or don't create it** |
| "Review will catch it" | Review catches quality issues, not delivery completeness. Different concerns. | **Verify delivery explicitly** |
| "Go vet would catch unused code" | Go vet catches unused variables, not unused exported types/functions. | **Run integration verification** |
| "The feature works, just missing one small piece" | Partial delivery ≠ delivery. If R4 of 7 requirements is missing, task is incomplete. | **Deliver ALL requirements** |
| "That requirement was implied, not explicit" | If the task says it, verify it. Ambiguity → ask, don't skip. | **Verify or clarify with requester** |
| "I did the hard part, the wiring is trivial" | Trivial ≠ done. If it's trivial, do it now. | **Complete the trivial wiring** |

## Integration with dev-cycle

This gate runs as **Gate 0.5** — after implementation (Gate 0), before DevOps (Gate 1):

```
Gate 0:   Implementation (write code)
Gate 0.5: Delivery Verification (verify ALL requested work is delivered) ← THIS GATE
Gate 1:   DevOps (infrastructure)
Gate 2:   SRE (reliability)
Gate 3:   Unit Testing
...
```

If Gate 0.5 returns PARTIAL or FAIL:
1. List ALL undelivered requirements with specific evidence
2. Return to Gate 0 with explicit instructions: "Deliver the following: [list with file:line references]"
3. Re-run Gate 0.5 after fixes
4. Only advance to Gate 1 when Gate 0.5 returns PASS

**Gate 0.5 is language-agnostic and task-type-agnostic.** It works the same whether the task is a Go API endpoint, a TypeScript frontend component, a database migration, an infrastructure change, or a business logic refactor. The process is always: extract requirements → verify each is delivered → report gaps.
