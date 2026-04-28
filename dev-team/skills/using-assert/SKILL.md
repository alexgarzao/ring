---
name: ring:using-assert
description: |
  Dual-mode skill for github.com/LerianStudio/lib-commons/v5/commons/assert — Lerian's
  production-grade runtime assertion package. Companion deep-dive to ring:using-lib-commons
  focused entirely on the commons/assert subsystem.

  Sweep Mode (primary): Dispatches 6 parallel explorer subagents to sweep any Lerian Go
  codebase for DIY invariant checks, zero-panic policy violations, hand-rolled domain
  predicates, missing metric initialization, production-drift between tests and runtime,
  and unstructured error-boundary logging. Detects version drift in commons/assert,
  identifies replacement opportunities with file:line precision, generates tasks compatible
  with ring:dev-cycle for batched fixes.

  Reference Mode: Comprehensive catalog of commons/assert (latest v5.x) — full API surface,
  asserter lifecycle, instance method semantics, the complete domain predicate catalog
  (numeric, financial, transaction state machine, network, time), the observability trident
  (log + span event + metric), AssertionError unwrapping, decision tree for
  panic-vs-assert-vs-error, testing patterns, and the anti-pattern catalog. Load for
  API discovery and when enforcing financial invariants in production Go code.

trigger: |
  Sweep mode:
  - "Sweep the codebase for commons/assert opportunities"
  - "Audit this service for zero-panic policy compliance"
  - "Find where we could replace DIY invariant checks with assert"
  - "Identify assert migration opportunities"
  - "Check assert coverage across the ledger"

  Reference mode:
  - Writing a balance posting and need invariant enforcement
  - Writing a transaction state transition (CREATED / APPROVED / PENDING / CANCELED / NOTED)
  - Enforcing double-entry invariant (debits == credits) in a new code path
  - Adding a positive-amount or non-negative-amount check
  - Need the signature for an assert predicate or asserter method
  - Setting up InitAssertionMetrics during service bootstrap
  - Unwrapping AssertionError in an HTTP / gRPC / message-consumer error boundary
  - Deciding whether to panic, assert, or return an error for a given condition
  - Testing that assertions fire correctly on failure paths
  - Migrating panic() / log.Fatal() calls out of production code

skip_when: |
  - Working on non-Go services
  - Working on frontend code
  - Target codebase is Ring itself (no lib-commons dependency)

related:
  similar: [ring:using-lib-commons, ring:using-runtime, ring:using-dev-team, ring:dev-refactor]
---

# ring:using-assert

This skill serves two distinct purposes. Choose the correct mode before proceeding.

## Mode Selection

MUST choose mode based on the request shape:

| Request Shape                                                           | Mode          |
| ----------------------------------------------------------------------- | ------------- |
| "Sweep / audit the codebase for assert opportunities"                   | **Sweep**     |
| "Find panic()/log.Fatal() violations"                                   | **Sweep**     |
| "Replace DIY invariant checks with commons/assert"                      | **Sweep**     |
| "What's the signature for assert.DebitsEqualCredits?"                   | **Reference** |
| "How do I initialize assertion metrics?"                                | **Reference** |
| "Should I panic, assert, or return an error here?"                      | **Reference** |
| "How do I unwrap AssertionError in a Fiber error handler?"              | **Reference** |

- **Sweep Mode** (primary): Active orchestration. Executes a 4-phase protocol that scans a
  target Lerian Go codebase, identifies DIY invariant patterns that should be replaced
  with `commons/assert`, and emits tasks for `ring:dev-cycle` consumption.
- **Reference Mode**: Passive catalog. Read sections 1–14 below for API discovery,
  predicate catalog, and composition patterns.

Sweep Mode uses Reference Mode content as explorer context — each explorer receives the
relevant API and predicate entries for its angle so it knows the target surface.

## Table of Contents

| #  | Section                             | Mode      | What You'll Find                                              |
| -- | ----------------------------------- | --------- | ------------------------------------------------------------- |
| —  | Mode Selection                      | Both      | How to choose sweep vs reference                              |
| —  | Sweep Protocol                      | Sweep     | 4-phase scan orchestration                                    |
| —  | Explorer Angle Specs                | Sweep     | 6 DIY patterns and replacements                               |
| —  | Report Template                     | Sweep     | Findings format                                               |
| —  | Task Generation                     | Sweep     | ring:dev-cycle handoff format                                 |
| 1  | API Surface                         | Reference | Exported symbols, signatures, one-line purposes               |
| 2  | Asserter Lifecycle                  | Reference | Scoping, component/operation naming, anti-patterns            |
| 3  | Instance Methods                    | Reference | When to use That / NotNil / NotEmpty / NoError / Never / Halt |
| 4  | Full Domain Predicate Catalog       | Reference | Numeric / financial / state-machine / network / time          |
| 5  | Composition Pattern                 | Reference | Pure predicates + observable asserter                         |
| 6  | The Observability Trident           | Reference | Log + span event + metric on every failure                    |
| 7  | AssertionError Unwrapping           | Reference | Error boundary patterns, sentinel check                       |
| 8  | Decision Tree — panic vs assert vs error | Reference | Three-way distinction with worked examples               |
| 9  | Testing Patterns                    | Reference | Proving assertions fire, production-drift detection           |
| 10 | Anti-Pattern Catalog                | Reference | Six anti-patterns with consequence narrative                  |
| 11 | Bootstrap Order                     | Reference | Where InitAssertionMetrics fits                               |
| 12 | Cross-References                    | Reference | Pointers into using-lib-commons, using-runtime                |
| 13 | Cross-Cutting Patterns              | Reference | Nil-safety, production mode, runtime interaction, performance |
| 14 | Breaking Changes                    | Reference | v4 → v5 delta for commons/assert                              |

---

# SWEEP MODE

MANDATORY: When invoked in Sweep Mode, the orchestrator MUST execute all four phases in
order. MUST NOT skip phases. MUST NOT shortcut Phase 3 by reducing explorer count.
FORBIDDEN: Producing a report based on the orchestrator's own code inspection — the 6
explorers are the source of truth for findings.

## Sweep Protocol

The sweep runs in four sequential phases. Each phase has a HARD GATE — MUST NOT proceed
to the next phase until the current phase produces its required artifact.

```
Phase 1: Version Reconnaissance   → version-report.json
Phase 2: CHANGELOG Delta Analysis → delta-report.json
Phase 3: Multi-Angle DIY Sweep    → 6 × assert-sweep-{N}-{angle}.json
Phase 4: Consolidated Report      → assert-sweep-report.md + assert-sweep-tasks.json
```

★ Insight ─────────────────────────────────────
The sweep's value is not that it catches `panic()` — `grep` does that. The sweep's value
is that it catches **asymmetric drift**: invariants enforced only in tests, defensive
checks that return silent errors, hand-rolled predicates that duplicate canonical ones.
These patterns pass code review because each individual instance is "not obviously wrong"
— the wrongness is systemic and only visible when you aggregate across the codebase.
─────────────────────────────────────────────────

### Phase 1: Version Reconnaissance

MANDATORY steps (orchestrator executes directly):

1. **Read `go.mod`** at the target project root.
   - Extract the line matching `github.com/LerianStudio/lib-commons/vN`.
   - Capture the exact pinned version (e.g., `v5.1.0`, `v4.2.0`).
   - If the dependency is absent, STOP and report: "Target is not a lib-commons consumer.
     Assert sweep not applicable."

2. **WebFetch latest release:**

   ```
   https://api.github.com/repos/LerianStudio/lib-commons/releases/latest
   ```

   Extract `tag_name` (the latest v5.x release) and `published_at`.

3. **Compare versions** and flag drift:

   | Condition                                   | Classification      |
   | ------------------------------------------- | ------------------- |
   | Pinned == Latest                            | Up-to-date          |
   | Pinned is patch behind                      | Minor drift         |
   | Pinned is minor behind                      | Moderate drift      |
   | Pinned is major behind (v4.x → v5.x)        | **Major upgrade**   |
   | Module path mismatch (no `/vN` suffix)      | **Module mismatch** |

4. **If v4.x detected:** Add a "major upgrade advisory" flag to the report. Phase 3
   explorers MUST receive this flag. The `commons/assert` API surface is source-compatible
   v4 → v5, but the module path bump (v4 → v5) is a prerequisite for every recommendation
   in the report, so it must lead the task list.

5. **Emit `/tmp/assert-version-report.json`** with fields:
   - `pinned_version` (string)
   - `latest_version` (string)
   - `drift_classification` (one of: up-to-date, minor-drift, moderate-drift, major-upgrade, module-mismatch)
   - `major_upgrade_required` (bool)
   - `module_path` (string, e.g., `github.com/LerianStudio/lib-commons/v5`)

### Phase 2: CHANGELOG Delta Analysis

MANDATORY steps:

1. **WebFetch CHANGELOG:**

   ```
   https://raw.githubusercontent.com/LerianStudio/lib-commons/main/CHANGELOG.md
   ```

2. **Extract entries** between `pinned_version` (exclusive) and `latest_version`
   (inclusive) that affect `commons/assert`. Parse the standard Keep-a-Changelog
   sections: `Added`, `Changed`, `Fixed`, `Security`, `Deprecated`, `Removed`.

3. **Filter to assert-scoped changes.** Look for entries referencing:
   - `commons/assert` or `assert` package
   - Asserter methods (`That`, `NotNil`, `NotEmpty`, `NoError`, `Never`, `Halt`)
   - Domain predicates (`PositiveDecimal`, `DebitsEqualCredits`, `ValidTransactionStatus`, etc.)
   - `AssertionError`, `ErrAssertionFailed`
   - `InitAssertionMetrics`

4. **Classify each entry** into one of:
   - `new-predicate` — a new domain predicate added
   - `new-method` — a new Asserter method
   - `breaking-change` — backward-incompatible change
   - `security-fix` — fix the consumer benefits from by upgrading
   - `bugfix` — consumer-facing bug resolved

5. **Emit `/tmp/assert-delta-report.json`** with a list of entries. If no
   assert-scoped changes exist between the pinned and latest versions, emit an empty
   array — this is a valid outcome and the Unadopted Features section of the report
   will be empty.

### Phase 3: Multi-Angle DIY Sweep

MANDATORY: Dispatch all 6 explorer angles in **ONE batch** of 6 parallel dispatches.
MUST NOT skip any angle. MUST wait for the batch to complete before proceeding to
Phase 4.

**Per-explorer dispatch contract:**

Each explorer MUST be dispatched with `subagent_type: ring:codebase-explorer`. The
prompt MUST contain exactly these sections:

```
## Target
<absolute path to target repo root>

## Your Angle
<angle number + name, e.g., "Angle 1: panic() in non-test code">

## Severity Calibration
<CRITICAL | HIGH | MEDIUM | LOW — from angle spec>

## What to Detect (DIY patterns)
<bullet list of grep patterns, import paths, code signatures>

## Replacement
<commons/assert API — method + predicate composition>

## Migration Complexity
<trivial | moderate | complex>

## Version Context
Pinned: <from Phase 1>
Latest: <from Phase 1>
Major upgrade required: <bool from Phase 1>

## Output
Write findings to: /tmp/assert-sweep-{N}-{angle-slug}.json
Schema: see below.
```

**Explorer output schema** (`/tmp/assert-sweep-{N}-{angle-slug}.json`):

```json
{
  "angle_number": 1,
  "angle_name": "panic() in non-test code",
  "severity": "CRITICAL",
  "migration_complexity": "moderate",
  "findings": [
    {
      "file": "internal/ledger/posting.go",
      "line": 84,
      "diy_pattern": "panic(\"amount must be positive\")",
      "replacement": "asserter.That(ctx, assert.PositiveDecimal(amount), ...)",
      "evidence_snippet": "if amount.IsNegative() { panic(\"amount must be positive\") }",
      "notes": "Zero-panic policy violation — crashes service on bad input"
    }
  ],
  "summary": "3 files contain panic() in non-test code (zero-panic policy violation)",
  "requires_major_upgrade": false
}
```

**If an explorer finds nothing** for its angle, it MUST still write a file with an
empty `findings` array and a summary stating "No DIY patterns detected for this angle".
This lets the synthesizer distinguish "checked and clean" from "not checked".

### Phase 4: Consolidated Report + Task Generation

MANDATORY: Dispatch a synthesizer agent (`subagent_type: ring:codebase-explorer` or
general-purpose) with this contract:

```
## Inputs
- /tmp/assert-version-report.json
- /tmp/assert-delta-report.json
- /tmp/assert-sweep-*.json  (6 files)

## Outputs
1. /tmp/assert-sweep-report.md  (human-readable report — see Report Template)
2. /tmp/assert-sweep-tasks.json  (ring:dev-cycle task array — see Task Generation)

## Your Job
MUST read all 6 explorer files. MUST aggregate findings by severity. MUST produce the
report following the exact template below. MUST generate one task per DIY pattern cluster
(group findings in the same file/package into one task).

MUST NOT invent findings not present in explorer outputs.
MUST NOT omit findings that explorers flagged.
MUST NOT reclassify severity without explicit justification in the task description.
```

After synthesis completes, the orchestrator surfaces the report path + task count to the
user and offers handoff to `ring:dev-cycle`.

---

## Explorer Angle Specifications

MANDATORY: All 6 angles run on every sweep. The catalog below is the source of truth
for what each explorer looks for. MUST NOT edit angle specs at dispatch time — copy
verbatim into the explorer prompt.

---

#### Angle 1: `panic()` / `log.Fatal` / `log.Panic` / `Must*` in non-test code

**Severity:** CRITICAL

**DIY Patterns to Detect:**
- `panic(` in any `.go` file that is not `_test.go`
- `log.Fatal(` / `log.Fatalf(` / `log.Fatalln(` in non-test code
- `log.Panic(` / `log.Panicf(` / `log.Panicln(` in non-test code
- Custom `Must*` helper calls (e.g., `MustParseDecimal`, `MustConnect`) in non-test code
- **Exception (allowed):** `regexp.MustCompile` with a compile-time **string literal constant** is the only sanctioned exception to the zero-panic policy. If the argument is a variable or computed at runtime, it is a violation.

**commons/assert Replacement:**
- `asserter.That(ctx, condition, "message", keysAndValues...)` — returns error, observability trident fires
- `asserter.NotNil(ctx, value, "message", keysAndValues...)` — for nil-receiver guards
- `asserter.NoError(ctx, err, "message", keysAndValues...)` — when wrapping an existing error
- `asserter.Never(ctx, "message", keysAndValues...)` — for unreachable branches

**Migration Complexity:** moderate (callers must be updated to accept returned error)

**Example Transformation:**

```go
// BEFORE:
func postEntry(amount decimal.Decimal) {
    if amount.IsNegative() {
        panic("amount must be positive")
    }
    if amount.IsZero() {
        log.Fatal("amount cannot be zero")
    }
    // ...
}

// AFTER:
func postEntry(ctx context.Context, a *assert.Asserter, amount decimal.Decimal) error {
    if err := a.That(ctx, assert.PositiveDecimal(amount),
        "amount must be positive",
        "amount", amount.String()); err != nil {
        return err
    }
    // ...
    return nil
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for zero-panic policy violations. MUST find every `panic(`,
> `log.Fatal(`, `log.Fatalf(`, `log.Fatalln(`, `log.Panic(`, `log.Panicf(`, `log.Panicln(`,
> and `.Must*(` helper call in any `.go` file that is NOT a `_test.go` file. The only
> allowed exception is `regexp.MustCompile(` whose argument is a compile-time string
> literal — if the argument is a variable, that is a violation. For each finding record
> file:line, the exact call, and whether the surrounding context is bootstrap/init,
> runtime, or hot-path. Severity CRITICAL — these are production crashes waiting to happen
> and each one is a zero-panic policy violation. Write `/tmp/assert-sweep-1-panic.json`.

---

#### Angle 2: Defensive nil/empty checks without metric emission

**Severity:** HIGH

**DIY Patterns to Detect:**
- `if x == nil { return err }` / `if x == nil { return fmt.Errorf(...) }` in code paths where the nil represents an **invariant violation** (internal state that should never be nil), not an expected input-validation failure
- `if s == "" { return err }` on fields that are invariants (tenant ID on authenticated request, transaction ID on internal call), not user input
- `if err != nil { return err }` at invariant boundaries (internal service calls where error "should never happen" but propagates silently with no observability)
- Any pattern that silently propagates an invariant failure without emitting metric / log / span event

**Important distinction:** NOT every `if err != nil { return err }` is wrong. Expected failure paths — user input validation, external I/O failure, context cancellation — are normal error returns and do NOT need asserter coverage. This angle targets **invariant** paths: internal state that the caller/callee contract guarantees will be valid, where a violation is a bug, not a user error.

**commons/assert Replacement:**
- `asserter.NotNil(ctx, x, "x must not be nil at this boundary", keys...)` — for nil-at-invariant
- `asserter.NotEmpty(ctx, s, "tenant ID required at this boundary")` — for empty-string invariants
- `asserter.NoError(ctx, err, "internal call must not fail", keys...)` — for "should never error" paths

**Migration Complexity:** moderate — requires deciding which checks are invariants vs expected failures

**Example Transformation:**

```go
// BEFORE — invariant check silently returns error, no observability:
func postToLedger(ctx context.Context, txnID string, account *Account) error {
    if account == nil {
        return errors.New("account is nil") // silent — never surfaces in metrics
    }
    if txnID == "" {
        return errors.New("transaction ID empty") // silent
    }
    // ...
}

// AFTER — asserter fires the observability trident on invariant violation:
func postToLedger(ctx context.Context, a *assert.Asserter, txnID string, account *Account) error {
    if err := a.NotNil(ctx, account, "account required at ledger boundary",
        "transaction_id", txnID); err != nil {
        return err
    }
    if err := a.NotEmpty(ctx, txnID, "transaction ID required at ledger boundary"); err != nil {
        return err
    }
    // ...
    return nil
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for defensive invariant checks that return silently without
> observability. Search for `if x == nil { return`, `if s == "" { return`, and
> `if err != nil { return err }` patterns. For each finding, assess whether the check is
> on an **invariant path** (internal state that should never be invalid — e.g., tenant
> ID on an authenticated request, non-nil DB connection after successful init, non-empty
> transaction ID on internal call) or an **expected-failure path** (user input
> validation, external I/O, context cancellation). Flag only invariant-path checks —
> expected failures are normal error returns and do NOT need asserter coverage. For each
> flagged finding record file:line, the invariant being checked, and why it is an
> invariant (not expected failure). Severity HIGH — silent invariant violations corrupt
> state and never appear in dashboards. Write `/tmp/assert-sweep-2-defensive.json`.

---

#### Angle 3: Hand-rolled domain predicates duplicating `assert.*`

**Severity:** HIGH

**DIY Patterns to Detect:**
- Functions named `isPositive`, `isValidAmount`, `debitsEqualCredits`, `validateTransactionStatus`, `isValidUUID`, `isPortValid`, `isValidSSLMode`, `inRange`, and their typo/case variants
- Inline equivalents that duplicate canonical predicates: `if amount.IsPositive() && !amount.IsZero()` (equivalent to `assert.PositiveDecimal`), `if d.Cmp(c) == 0 && !d.IsZero()` (equivalent to `assert.DebitsEqualCredits` + `NonZeroTotals`)
- Custom transaction-status switch statements exhaustively enumerating CREATED/APPROVED/PENDING/CANCELED/NOTED (duplicates `assert.ValidTransactionStatus`)
- Hand-rolled status-transition lookup tables (duplicates `assert.TransactionCanTransitionTo`)

**commons/assert Replacement:** Delete the DIY predicate, compose asserter with the canonical predicate:

| DIY Predicate                  | Canonical Replacement                          |
| ------------------------------ | ---------------------------------------------- |
| `isPositive(n int64)`          | `assert.Positive(n)`                           |
| `isNonNegative(n int64)`       | `assert.NonNegative(n)`                        |
| `isInRange(n, min, max)`       | `assert.InRange(n, min, max)`                  |
| `isPositiveAmount(d decimal)`  | `assert.PositiveDecimal(d)`                    |
| `isNonNegativeAmount(d)`       | `assert.NonNegativeDecimal(d)`                 |
| `isValidAmount(d)`             | `assert.ValidAmount(d)`                        |
| `isValidScale(s int)`          | `assert.ValidScale(s)`                         |
| `debitsEqualCredits(d, c)`     | `assert.DebitsEqualCredits(d, c)`              |
| `isValidTxStatus(s)`           | `assert.ValidTransactionStatus(s)`             |
| `canTransitionTo(from, to)`    | `assert.TransactionCanTransitionTo(from, to)`  |
| `isValidUUID(s)`               | `assert.ValidUUID(s)`                          |
| `isValidPort(p)`               | `assert.ValidPort(p)`                          |
| `isValidSSLMode(m)`            | `assert.ValidSSLMode(m)`                       |

**Migration Complexity:** trivial (delete + swap)

**Example Transformation:**

```go
// BEFORE — hand-rolled predicate reinvents the canonical one:
func isValidTransactionStatus(s string) bool {
    switch s {
    case "CREATED", "APPROVED", "PENDING", "CANCELED", "NOTED":
        return true
    }
    return false
}

func process(ctx context.Context, txnID, status string) error {
    if !isValidTransactionStatus(status) {
        return fmt.Errorf("invalid status: %s", status)
    }
    // ...
}

// AFTER — canonical predicate + asserter:
func process(ctx context.Context, a *assert.Asserter, txnID, status string) error {
    if err := a.That(ctx, assert.ValidTransactionStatus(status),
        "invalid transaction status",
        "transaction_id", txnID, "status", status); err != nil {
        return err
    }
    // ...
    return nil
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for hand-rolled domain predicates that duplicate
> `commons/assert` canonical predicates. Search for functions named `isPositive*`,
> `isValidAmount*`, `isValidTransactionStatus*`, `canTransition*`, `isValidUUID*`,
> `isValidPort*`, `debitsEqualCredits*`, `isInRange*`, and similar patterns. Also
> search for inline equivalents — switch statements enumerating
> CREATED/APPROVED/PENDING/CANCELED/NOTED, inline `d.Cmp(c) == 0 && !d.IsZero()`
> constructions, and range checks (`x >= min && x <= max`) that could be
> `assert.InRange`. Cross-reference each hand-rolled predicate against the canonical
> catalog in the "Full Domain Predicate Catalog" section of `ring:using-assert`. For
> each finding record file:line, the DIY predicate name or inline construction, and the
> exact canonical replacement. Severity HIGH — divergence between DIY predicates and
> canonical ones causes subtle bugs (e.g., DIY forgetting a status, accepting zero
> amounts, losing sign checks). Write `/tmp/assert-sweep-3-predicates.json`.

---

#### Angle 4: Missing `InitAssertionMetrics` at startup

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- The service uses `assert.New(` or asserter methods somewhere in the codebase
- But `main.go`, `cmd/*/main.go`, `internal/app/`, or `internal/bootstrap/` packages do NOT contain `assert.InitAssertionMetrics(`
- Symptom: `assert` is imported and used, but the `assertion_failed_total` metric counter is never emitted, so assertion failures are invisible in dashboards even when they fire

**Grep pattern:**
```
Presence:  grep -r 'assert.New\|assertion.That\|a.That\|a.NotNil\|a.NotEmpty\|a.NoError'
Absence:   grep -r 'assert.InitAssertionMetrics' → returns no results
```

**commons/assert Replacement:**

Add to the bootstrap sequence, AFTER telemetry is set up, ALONGSIDE `runtime.InitPanicMetrics`:

```go
// After: tl, _ := opentelemetry.NewTelemetry(...)
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
assert.InitAssertionMetrics(tl.MetricsFactory)  // add this
```

**Migration Complexity:** trivial (one-line bootstrap addition)

**Example Transformation:**

```go
// BEFORE — metrics factory wired, panic metrics initialized, assert metrics forgotten:
tl, _ := opentelemetry.NewTelemetry(telemetryConfig)
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
// assertion_failed_total counter will never fire even when assertions do

// AFTER:
tl, _ := opentelemetry.NewTelemetry(telemetryConfig)
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
assert.InitAssertionMetrics(tl.MetricsFactory)
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo to determine whether `commons/assert` is used without
> `InitAssertionMetrics` being called during bootstrap. First, grep for any usage
> of `assert.New(` or asserter methods (`.That(`, `.NotNil(`, `.NotEmpty(`,
> `.NoError(`, `.Never(`) across the codebase — this establishes that the service
> DOES use the assert package. Then grep `main.go`, `cmd/*/main.go`,
> `internal/app/*`, and `internal/bootstrap/*` for `assert.InitAssertionMetrics(`
> — its ABSENCE is the finding. If assert is used but InitAssertionMetrics is never
> called, record the file:line where asserter usage begins (to establish "yes, used")
> and the bootstrap file:line where the call should be added. If assert is not used
> at all in the service, emit an empty findings array. Severity MEDIUM — missing
> this call does not break functionality but causes invisible failures (trident emits
> log + span event but the metric counter stays at zero, so dashboards never alert on
> assertion spikes). Write `/tmp/assert-sweep-4-initmetrics.json`.

---

#### Angle 5: Financial invariants enforced only in tests, not in production

**Severity:** HIGH

**DIY Patterns to Detect:**
- `_test.go` files that assert on financial invariants using `assert.DebitsEqualCredits`, `assert.TransactionCanTransitionTo`, `assert.BalanceSufficientForRelease`, `assert.PositiveDecimal`, `assert.NonZeroTotals`, or equivalent hand-rolled checks
- But the corresponding **production code path** (the function the test exercises) does NOT enforce the same invariant via an asserter call

**Detection technique:**
1. Grep test files for invariant assertions: `require.True.*DebitsEqualCredits`, `require.NoError.*asserter.That.*DebitsEqualCredits`, or hand-rolled equivalents
2. For each hit, identify the function under test (e.g., test `TestPostTransaction` exercises `PostTransaction`)
3. Read the production function and check: does it call `asserter.That(ctx, assert.DebitsEqualCredits(...), ...)` itself? If not → finding

**Why this matters:** The test confirms the invariant holds under the test's inputs. The production code path can still **receive** inputs that violate the invariant (e.g., a bug upstream produces unbalanced debits) and silently corrupt ledger state. The invariant lives in the test, not in the production code, so CI stays green while production drifts.

**commons/assert Replacement:**

Mirror the test assertion into the production code path:

```go
// Production code — add the same invariant check the test makes:
func PostTransaction(ctx context.Context, a *assert.Asserter, txn *Transaction) error {
    // Invariant: debits must equal credits (double-entry)
    if err := a.That(ctx, assert.DebitsEqualCredits(txn.TotalDebits(), txn.TotalCredits()),
        "double-entry invariant violated at posting",
        "transaction_id", txn.ID,
        "debits", txn.TotalDebits().String(),
        "credits", txn.TotalCredits().String()); err != nil {
        return err
    }
    // ... actual posting logic
    return nil
}
```

**Migration Complexity:** moderate — requires understanding test intent and mirroring into production

**Example Transformation:**

```go
// BEFORE — test asserts invariant, production does not:

// ledger_test.go
func TestPostTransaction_BalancesEqual(t *testing.T) {
    txn := buildTransaction(100, 100)
    require.True(t, assert.DebitsEqualCredits(txn.TotalDebits(), txn.TotalCredits()))
    err := PostTransaction(ctx, txn)
    require.NoError(t, err)
}

// ledger.go — production code has NO invariant check:
func PostTransaction(ctx context.Context, txn *Transaction) error {
    return repo.Insert(ctx, txn) // trusts input blindly
}

// AFTER — invariant mirrored into production, asserter fires trident if violated:

// ledger.go:
func PostTransaction(ctx context.Context, a *assert.Asserter, txn *Transaction) error {
    if err := a.That(ctx, assert.DebitsEqualCredits(txn.TotalDebits(), txn.TotalCredits()),
        "double-entry invariant violated",
        "transaction_id", txn.ID,
        "debits", txn.TotalDebits().String(),
        "credits", txn.TotalCredits().String()); err != nil {
        return err
    }
    return repo.Insert(ctx, txn)
}
```

★ Insight ─────────────────────────────────────
This is the highest-leverage angle in the sweep for a ledger codebase. An invariant
that lives only in tests passes CI and deploys to production, where it becomes a silent
assumption. Production code then trusts upstream callers, and the first time an upstream
bug produces unbalanced debits, the ledger writes the corruption straight to disk.
Mirroring test invariants into production is not redundancy — it's defense-in-depth
against the limits of test coverage.
─────────────────────────────────────────────────

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for financial invariants enforced only in tests and not in
> production. Walk `_test.go` files and find every assertion referencing
> `assert.DebitsEqualCredits`, `assert.TransactionCanTransitionTo`,
> `assert.BalanceSufficientForRelease`, `assert.PositiveDecimal`,
> `assert.NonZeroTotals`, or hand-rolled equivalents (e.g., `require.Equal(t, debits,
> credits)`). For each test assertion, identify the production function under test
> (typically inferred from test name — `TestPostTransaction` → `PostTransaction`). Read
> the production function and check: does it call an asserter with the SAME invariant?
> If not → finding. For each finding record the test file:line, the production
> file:line (function definition), and the specific invariant that is test-only.
> Severity HIGH — these are silent ledger-corruption risks. Write
> `/tmp/assert-sweep-5-test-only.json`.

---

#### Angle 6: `AssertionError` not unwrapped in error boundaries

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- Fiber error handlers (`fiber.Config{ErrorHandler: ...}` or `FiberErrorHandler` overrides) that log errors without `errors.As(err, &assertErr)`
- gRPC unary/stream interceptors that log errors returned by service methods without AssertionError unwrap
- RabbitMQ consumer callbacks / message-handler error paths that log errors without AssertionError unwrap
- HTTP middleware error-logging paths that lose the structured AssertionError context
- Any `logger.Error("handler failed", "error", err)` at an error boundary — when `err` may be an AssertionError, the structural context (Component, Operation, Assertion) is flattened into the opaque error string

**commons/assert Replacement:**

At error boundaries, unwrap and log the structural context:

```go
func logHandlerError(ctx context.Context, logger log.Logger, err error) {
    var assertErr *assert.AssertionError
    if errors.As(err, &assertErr) {
        logger.Error("assertion violated",
            "component", assertErr.Component,
            "operation", assertErr.Operation,
            "assertion", assertErr.Assertion,
            "message", assertErr.Message,
            "context", assertErr.Context,
        )
        return
    }
    logger.Error("handler error", "error", err)
}
```

**Migration Complexity:** trivial (one unwrap block added at each error boundary)

**Example Transformation:**

```go
// BEFORE — error boundary flattens AssertionError:
app := fiber.New(fiber.Config{
    ErrorHandler: func(c *fiber.Ctx, err error) error {
        logger.Error("request failed", "error", err.Error())
        // Component / Operation / Assertion labels lost in err.Error() string
        return c.Status(500).JSON(fiber.Map{"error": err.Error()})
    },
})

// AFTER — unwrap AssertionError at the boundary:
app := fiber.New(fiber.Config{
    ErrorHandler: func(c *fiber.Ctx, err error) error {
        var assertErr *assert.AssertionError
        if errors.As(err, &assertErr) {
            logger.Error("assertion violated at boundary",
                "component", assertErr.Component,
                "operation", assertErr.Operation,
                "assertion", assertErr.Assertion,
                "message", assertErr.Message,
            )
            // Assertion failures are internal invariant violations → 500, not 400
            return c.Status(500).JSON(fiber.Map{"error": "internal invariant violated"})
        }
        logger.Error("request failed", "error", err.Error())
        return c.Status(500).JSON(fiber.Map{"error": err.Error()})
    },
})
```

**Consequence of missing this pattern:** When an assertion fires, the trident emits the
metric and span event correctly, but the log line at the error boundary shows only the
flattened message string. Operators reading the log cannot tell which Component +
Operation + Assertion failed without correlating by timestamp to the span event — painful
during incident triage.

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for error boundaries that do not unwrap `*assert.AssertionError`.
> Search for Fiber error handlers (`ErrorHandler:`, `FiberErrorHandler`), gRPC
> interceptors (`grpc.UnaryInterceptor`, `grpc.StreamInterceptor`), RabbitMQ consumer
> callbacks, and HTTP middleware error-logging paths. For each boundary, check whether
> the error-handling code contains `errors.As(err, &<assertErrVar>)` where the variable
> is of type `*assert.AssertionError`. Boundaries that log the error without this unwrap
> are findings — they flatten Component/Operation/Assertion into an opaque string and
> lose structural observability in logs. For each finding record file:line, the boundary
> type (Fiber / gRPC / AMQP / HTTP middleware), and the log statement that should unwrap.
> Severity MEDIUM — the trident (metric + span event) still fires correctly; only the log
> layer loses structure. Write `/tmp/assert-sweep-6-unwrap.json`.

---

## Report Template

MANDATORY: The synthesizer MUST produce `/tmp/assert-sweep-report.md` following this
exact structure. MUST NOT add sections. MUST NOT reorder sections. MUST populate every
section even if empty (use "None detected" placeholders).

```markdown
# commons/assert Sweep Report

**Target:** <absolute path to target repo>
**Generated:** <ISO-8601 timestamp>
**Sweep duration:** <seconds>

---

## Version Status

| Field                    | Value             |
| ------------------------ | ----------------- |
| Pinned version           | <v5.0.0>          |
| Latest stable            | <resolved at runtime> |
| Drift classification     | <minor-drift>     |
| Major upgrade required   | <yes / no>        |
| Module path              | <.../v5>          |

**Assessment:** <one-paragraph narrative — "project is up-to-date on commons/assert,
all recommendations apply to pinned version" or "project pinned to v4.2.0, v5 migration
required before adopting recommendations below">

---

## Unadopted Features

Changes to `commons/assert` between the pinned version and latest stable that the
target has not yet adopted:

| Version | Feature                     | Classification  | Relevant Finding Angle |
| ------- | --------------------------- | --------------- | ---------------------- |
| <ver>   | <feature>                   | <classification>| <angle>                |

(If no assert-scoped changes exist in the delta, write "No unadopted features — the
commons/assert API surface is unchanged between pinned and latest versions.")

---

## Quick Wins

Severity LOW–MEDIUM, migration complexity trivial. Low-risk, high-leverage fixes
batchable in a single dev-cycle task.

<bulleted list of findings grouped by angle — each bullet: "Angle N: <summary>, <file count> files, trivial">

---

## Strategic Migrations

Severity HIGH–CRITICAL, migration complexity moderate–complex. High-value, multi-task
efforts that MUST go through the full dev-cycle.

<bulleted list of findings grouped by angle — each bullet: "Angle N: <summary>, <file count> files, complexity, expected impact">

---

## Full Findings

| Angle                         | Severity  | File                        | Line | DIY Pattern                                | Replacement                              | Complexity |
| ----------------------------- | --------- | --------------------------- | ---- | ------------------------------------------ | ---------------------------------------- | ---------- |
| 1 panic() in non-test         | CRITICAL  | internal/ledger/posting.go  | 84   | panic("amount must be positive")           | asserter.That + assert.PositiveDecimal   | moderate   |
| 5 invariant test-only         | HIGH      | internal/ledger/ledger.go   | 112  | DebitsEqualCredits only in test            | asserter.That + DebitsEqualCredits       | moderate   |
| 3 hand-rolled predicate       | HIGH      | internal/txn/validate.go    | 47   | isValidTransactionStatus(s)                | assert.ValidTransactionStatus            | trivial    |
| ...                           | ...       | ...                         | ...  | ...                                        | ...                                      | ...        |

---

## Summary Statistics

| Severity | Findings | Files affected | Estimated effort |
| -------- | -------- | -------------- | ---------------- |
| CRITICAL | N        | N              | N days           |
| HIGH     | N        | N              | N days           |
| MEDIUM   | N        | N              | N days           |
| LOW      | N        | N              | N days           |
| **Total**| **N**    | **N**          | **N days**       |

**Angles clean:** <list of angles where no DIY was detected — signals codebase health>

---

## Recommended Next Step

`ring:dev-cycle` consuming `/tmp/assert-sweep-tasks.json` — N tasks generated,
grouped by severity, CRITICAL first. Angle 1 (zero-panic policy) and Angle 5
(test-only invariants) MUST land before other tiers — both are production-safety
risks.
```

---

## Task Generation for ring:dev-cycle

MANDATORY: The synthesizer MUST also emit `/tmp/assert-sweep-tasks.json` — a JSON
array of tasks shaped for `ring:dev-cycle` consumption. The format matches what
`ring:dev-refactor` produces.

**Task grouping rules:**

1. MUST group findings by severity — CRITICAL first, then HIGH, MEDIUM, LOW.
2. Within a severity tier, MUST group findings from the same file or tightly-related
   files (same package, same bounded context) into a single task.
3. CRITICAL findings (Angle 1 — zero-panic violations) MUST be standalone tasks (no
   batching across concerns) — each gets its own dev-cycle pass.
4. MUST include dependency references when one task's correctness depends on another
   (e.g., "Add InitAssertionMetrics" depends on "Upgrade lib-commons to v5" when the
   pinned version is v4.x).

**Task schema:**

```json
{
  "id": "assert-sweep-001",
  "title": "Replace panic() in ledger posting with asserter",
  "severity": "CRITICAL",
  "description": "Target service violates zero-panic policy in internal/ledger/posting.go (3 call sites). panic() on invariant violations crashes the service instead of firing the observability trident and returning a recoverable error. Replace each panic with asserter.That + the appropriate domain predicate (PositiveDecimal, DebitsEqualCredits, ValidTransactionStatus). The assertion_failed_total metric becomes an observable signal on these invariants.",
  "files_affected": [
    "internal/ledger/posting.go:84",
    "internal/ledger/posting.go:127",
    "internal/ledger/posting.go:201"
  ],
  "acceptance_criteria": [
    "All panic() calls in internal/ledger/posting.go removed",
    "Each invariant enforced via asserter.That + canonical assert predicate",
    "Callers updated to accept returned error",
    "Unit tests verify asserter fires on invariant violation (metric counter + span event)",
    "No regexp.MustCompile exception abused — any remaining panic() is justified and minimal"
  ],
  "estimated_complexity": "moderate",
  "depends_on": [],
  "angle": 1,
  "replacement_api": "commons/assert.Asserter + domain predicates"
}
```

**Task emission verbatim example:**

```json
[
  {
    "id": "assert-sweep-001",
    "title": "Upgrade lib-commons from v4.2.0 to latest v5.x",
    "severity": "HIGH",
    "description": "Target service pins github.com/LerianStudio/lib-commons/v4 at v4.2.0. The commons/assert API surface is source-compatible across v4 → v5, but the module path bump requires updating all imports. All recommendations below assume v5 APIs are available. This task MUST complete before any other assert-sweep task lands.",
    "files_affected": ["go.mod", "go.sum", "<all Go files importing lib-commons/v4>"],
    "acceptance_criteria": [
      "go.mod declares github.com/LerianStudio/lib-commons/v5 at latest v5.x tag",
      "All imports updated from /v4 to /v5",
      "go build ./... passes",
      "go test ./... passes"
    ],
    "estimated_complexity": "complex",
    "depends_on": [],
    "angle": "version",
    "replacement_api": "lib-commons/v5"
  },
  {
    "id": "assert-sweep-002",
    "title": "Replace panic() in ledger posting with asserter",
    "severity": "CRITICAL",
    "description": "<as above>",
    "files_affected": ["internal/ledger/posting.go:84", "..."],
    "acceptance_criteria": ["..."],
    "estimated_complexity": "moderate",
    "depends_on": ["assert-sweep-001"],
    "angle": 1,
    "replacement_api": "commons/assert.Asserter + domain predicates"
  },
  {
    "id": "assert-sweep-003",
    "title": "Mirror test-only DebitsEqualCredits invariant into production PostTransaction",
    "severity": "HIGH",
    "description": "Tests assert the double-entry invariant in TestPostTransaction_BalancesEqual, but the production PostTransaction function does not. A caller that produces unbalanced debits will silently corrupt the ledger. Mirror the invariant into production via asserter.That + assert.DebitsEqualCredits so every posting enforces the same check the test does.",
    "files_affected": ["internal/ledger/ledger.go:112", "internal/ledger/ledger_test.go:34"],
    "acceptance_criteria": [
      "PostTransaction calls asserter.That(ctx, assert.DebitsEqualCredits(...), ...) before persisting",
      "Existing tests pass unchanged",
      "New test: calling PostTransaction with unbalanced debits returns AssertionError and increments assertion_failed_total"
    ],
    "estimated_complexity": "moderate",
    "depends_on": ["assert-sweep-001"],
    "angle": 5,
    "replacement_api": "commons/assert + DebitsEqualCredits"
  }
]
```

**Handoff message template** (orchestrator surfaces to user after Phase 4):

```
commons/assert sweep complete. Findings: <N> across <M> of 6 angles.
- CRITICAL: <N>   HIGH: <N>   MEDIUM: <N>   LOW: <N>

Report: /tmp/assert-sweep-report.md
Tasks:  /tmp/assert-sweep-tasks.json (<N> tasks)

Next: Invoke ring:dev-cycle with the task file to execute fixes. CRITICAL tasks
(Angle 1 zero-panic violations) and HIGH tasks (Angle 5 test-only invariants, Angle 3
hand-rolled predicates) MUST be addressed before MEDIUM/LOW tiers.
```

---

# REFERENCE MODE

Sections 1–14 below catalog the `commons/assert` package (latest v5.x). Resolve the
actual version at runtime via `gh api repos/LerianStudio/lib-commons/releases/latest --jq .tag_name`.
Read the sections relevant to your current task. Sweep Mode explorers receive extracts from these sections
as context for their angle.

## 1. API Surface

Full catalog of exported symbols in `github.com/LerianStudio/lib-commons/v5/commons/assert`.

### Constructor

```go
func New(ctx context.Context, logger log.Logger, component, operation string) *Asserter
```

Creates an asserter scoped to a specific component and operation. `component` and
`operation` become metric labels and span-event attributes on every assertion failure.

### Asserter methods

```go
func (a *Asserter) That(ctx context.Context, condition bool, msg string, keysAndValues ...any) error
func (a *Asserter) NotNil(ctx context.Context, value any, msg string, keysAndValues ...any) error
func (a *Asserter) NotEmpty(ctx context.Context, s string, msg string, keysAndValues ...any) error
func (a *Asserter) NoError(ctx context.Context, err error, msg string, keysAndValues ...any) error
func (a *Asserter) Never(ctx context.Context, msg string, keysAndValues ...any) error
func (a *Asserter) Halt(err error)
```

Each method (except `Halt`) returns `error` on failure and `nil` on success. `Halt`
returns no value — it calls `runtime.Goexit()` when `err != nil`.

### Bootstrap

```go
func InitAssertionMetrics(factory metrics.Factory)
```

Registers the `assertion_failed_total` counter with the provided metrics factory. MUST
be called once during service bootstrap AFTER telemetry is initialized. Without this
call, the log and span-event layers of the trident still fire, but the metric layer
stays silent.

### Error types

```go
type AssertionError struct {
    Component string
    Operation string
    Assertion string          // method name: "That", "NotNil", "NotEmpty", "NoError", "Never"
    Message   string
    Context   map[string]any  // keysAndValues flattened into a map
}

func (e *AssertionError) Error() string
func (e *AssertionError) Is(target error) bool

var ErrAssertionFailed = errors.New("assertion failed")  // sentinel for errors.Is
```

### Domain predicates

See [Section 4](#4-full-domain-predicate-catalog) for the full catalog. Signatures
summarized:

```go
// Numeric
func Positive(n int64) bool
func NonNegative(n int64) bool
func InRange(n, min, max int64) bool

// Financial
func PositiveDecimal(amount decimal.Decimal) bool
func NonNegativeDecimal(amount decimal.Decimal) bool
func ValidAmount(amount decimal.Decimal) bool
func ValidScale(scale int) bool
func DebitsEqualCredits(debits, credits decimal.Decimal) bool
func NonZeroTotals(debits, credits decimal.Decimal) bool
func BalanceSufficientForRelease(onHold, releaseAmount decimal.Decimal) bool

// Transaction state machine
func ValidTransactionStatus(status string) bool
func TransactionCanTransitionTo(current, target string) bool
func TransactionCanBeReverted(status string, hasParent bool) bool
func TransactionHasOperations(ops []Operation) bool
func TransactionOperationsContain(ops []Operation, allowed []string) bool

// Network / infrastructure
func ValidUUID(s string) bool
func ValidPort(port string) bool
func ValidSSLMode(mode string) bool

// Time
func DateNotInFuture(date time.Time) bool
func DateAfter(date, reference time.Time) bool
```

---

## 2. Asserter Lifecycle

### Scoping

One asserter per **operation**, not per service. Reuse the asserter across all
invariant checks within the same request handler, message consumer callback, or
bounded operation. The `component` + `operation` labels are the axis along which
metrics and traces are grouped — making the labels too coarse (`component="app"`)
destroys metric granularity; making them too fine (`operation="post-transaction-step-4"`)
explodes label cardinality.

### Context propagation

Pass `ctx` into both the constructor and every method. The context is used to attach
span events to the **active trace**, so operators can jump from an assertion-failure
span event straight to the full request waterfall.

### Component naming conventions

Lowercase, hyphenated, bounded-context-shaped. Examples:

| Component             | Bounded context                    |
| --------------------- | ---------------------------------- |
| `ledger`              | Double-entry ledger core           |
| `transaction`         | Transaction lifecycle              |
| `auth`                | Authentication / authorization     |
| `ingest`              | Inbound event ingestion            |
| `outbox-dispatcher`   | Transactional outbox dispatcher    |
| `posting-engine`      | Balance posting                    |
| `webhook-deliverer`   | Outbound webhook delivery          |
| `dlq-consumer`        | Dead-letter queue consumer         |

### Operation naming conventions

Action-shaped, lowercase, hyphenated. Examples:

| Operation           | What it covers                          |
| ------------------- | --------------------------------------- |
| `post-transaction`  | Full posting workflow                   |
| `create-account`    | Account creation                        |
| `release-hold`      | Release held funds                      |
| `approve-pending`   | PENDING → APPROVED transition           |
| `revert-transaction`| Reverse an approved transaction         |
| `deliver-webhook`   | Send one outbound webhook               |

### Anti-pattern: per-service singleton asserter

```go
// DON'T: one asserter for the whole service
var serviceAsserter = assert.New(ctx, logger, "my-service", "all")

// DO: one asserter per operation
func postTransaction(ctx context.Context, ...) error {
    a := assert.New(ctx, logger, "ledger", "post-transaction")
    // ... invariant checks
}
```

A per-service singleton collapses all assertion metrics into a single
`{component=my-service, operation=all}` label pair, destroying the signal dashboards
rely on.

---

## 3. Instance Methods — When to Use Each

| Method      | When to use                                                            | Example                                                      |
| ----------- | ---------------------------------------------------------------------- | ------------------------------------------------------------ |
| `That`      | General boolean condition — compose with any predicate                 | `a.That(ctx, assert.DebitsEqualCredits(d, c), "...", ...)`   |
| `NotNil`    | Reflect-based nil check — catches typed nils stored in `any` interface | `a.NotNil(ctx, account, "...")`                              |
| `NotEmpty`  | String-only empty check                                                | `a.NotEmpty(ctx, tenantID, "...")`                           |
| `NoError`   | Shortcut for `err != nil` with auto error-type injection               | `a.NoError(ctx, dbErr, "...", "query", "SELECT ...")`        |
| `Never`     | Unreachable branch — exhaustive switch default, impossible sentinel    | `a.Never(ctx, "impossible status", "status", status)`        |
| `Halt`      | Goroutine-level halt via `runtime.Goexit()`                            | `a.Halt(err)` — only halts if `err != nil`                   |

### `That` — general condition

```go
if err := a.That(ctx, amount.IsPositive(), "amount must be positive",
    "amount", amount.String(), "account_id", accountID); err != nil {
    return err
}
```

Use when composing domain predicates. The condition is evaluated by the caller, so
predicates stay pure and the asserter handles observability.

### `NotNil` — typed-nil aware

`NotNil` uses `reflect.ValueOf(v).IsNil()` so it catches the common bug of a typed nil
stored in an `any` interface:

```go
var p *MyStruct  // p is typed nil
var v any = p    // v is not untyped nil — v == nil is FALSE

// a.NotNil correctly detects v is effectively nil
if err := a.NotNil(ctx, v, "MyStruct required"); err != nil {
    return err
}
```

### `NotEmpty` — strings only

`NotEmpty` only checks strings. For slices, use `That`:

```go
if err := a.That(ctx, len(ops) > 0, "operations required"); err != nil {
    return err
}
```

### `NoError` — auto error-type injection

`NoError` automatically appends the original error's type and message to the context,
so the caller does not need to pass them explicitly:

```go
if err := a.NoError(ctx, dbErr, "database query failed",
    "query", "SELECT balance", "account_id", accountID); err != nil {
    return err
}
// Context map also includes: "error_type", "<type>", "error", "<dbErr.Error()>"
```

### `Never` — for unreachable code

Use at exhaustive-switch defaults and impossible-state sentinels:

```go
switch status {
case "APPROVED":
    return approvePath(ctx)
case "CANCELED":
    return cancelPath(ctx)
case "PENDING":
    return pendingPath(ctx)
default:
    return a.Never(ctx, "unreachable status",
        "status", status, "transaction_id", txnID)
}
```

### `Halt` — goroutine-level halt

`Halt(err)` when `err != nil` calls `runtime.Goexit()`:

- Defers in the current goroutine still run
- Other goroutines are unaffected
- Process does not crash

Use only when continuing **this** goroutine is unsafe but the rest of the process is
fine (e.g., a background worker whose state is irrecoverable but whose peers are
healthy). `runtime.Goexit()` is preferred over `panic` because it respects the
zero-panic policy while still stopping the goroutine.

---

## 4. Full Domain Predicate Catalog

Predicates are pure `bool`-returning functions. Zero observability. Compose with an
asserter via `a.That(ctx, predicate, ...)` to add the trident.

### Numeric (int64)

| Predicate                    | What it validates                   | Scenario                              |
| ---------------------------- | ----------------------------------- | ------------------------------------- |
| `Positive(n int64) bool`     | `n > 0`                             | Line counts, retry budgets, TTLs      |
| `NonNegative(n int64) bool`  | `n >= 0`                            | Queue depths, active connection count |
| `InRange(n, min, max) bool`  | `min <= n <= max`                   | Bounded tunables, pagination limits   |

Composition:

```go
a := assert.New(ctx, logger, "posting-engine", "allocate-remainder")
if err := a.That(ctx, assert.Positive(entryCount),
    "entry count must be positive",
    "transaction_id", txnID, "entry_count", entryCount); err != nil {
    return err
}
```

### Financial (shopspring/decimal)

| Predicate                                           | What it validates                                          |
| --------------------------------------------------- | ---------------------------------------------------------- |
| `PositiveDecimal(amount decimal.Decimal) bool`      | `amount > 0`                                               |
| `NonNegativeDecimal(amount decimal.Decimal) bool`   | `amount >= 0`                                              |
| `ValidAmount(amount decimal.Decimal) bool`          | Exponent in `[-18, 18]` — within ledger precision          |
| `ValidScale(scale int) bool`                        | `0 <= scale <= 18`                                         |
| `DebitsEqualCredits(debits, credits) bool`          | `debits == credits` — double-entry invariant               |
| `NonZeroTotals(debits, credits) bool`               | Both sides non-zero                                        |
| `BalanceSufficientForRelease(onHold, release) bool` | `onHold >= release` — sufficient held funds                |

Composition — double-entry enforcement at posting time:

```go
a := assert.New(ctx, logger, "ledger", "post-transaction")

if err := a.That(ctx, assert.DebitsEqualCredits(debits, credits),
    "double-entry violation: debits != credits",
    "debits", debits.String(),
    "credits", credits.String(),
    "transaction_id", txnID); err != nil {
    return err
}

if err := a.That(ctx, assert.NonZeroTotals(debits, credits),
    "double-entry violation: zero-sum posting",
    "debits", debits.String(),
    "credits", credits.String()); err != nil {
    return err
}
```

Composition — sufficient-balance check on hold release:

```go
a := assert.New(ctx, logger, "posting-engine", "release-hold")
if err := a.That(ctx, assert.BalanceSufficientForRelease(holdAmount, releaseAmount),
    "insufficient held funds for release",
    "account_id", accountID,
    "on_hold", holdAmount.String(),
    "release", releaseAmount.String()); err != nil {
    return err
}
```

### Transaction state machine

| Predicate                                                   | What it validates                                               |
| ----------------------------------------------------------- | --------------------------------------------------------------- |
| `ValidTransactionStatus(status string) bool`                | One of `CREATED, APPROVED, PENDING, CANCELED, NOTED`            |
| `TransactionCanTransitionTo(current, target string) bool`   | Transition from current to target is legal                      |
| `TransactionCanBeReverted(status string, hasParent bool)`   | Only `APPROVED` transactions without a parent can be reverted   |
| `TransactionHasOperations(ops []Operation) bool`            | `len(ops) > 0`                                                  |
| `TransactionOperationsContain(ops, allowed []string) bool`  | All operation types in `ops` are members of `allowed`           |

The legal-transition graph (enforced by `TransactionCanTransitionTo`):

```
CREATED → APPROVED
CREATED → PENDING
CREATED → CANCELED
PENDING → APPROVED
PENDING → CANCELED
APPROVED → (terminal, except for NOTED reversal under explicit revert)
```

Composition — status transition at approval time:

```go
a := assert.New(ctx, logger, "transaction", "approve-pending")

if err := a.That(ctx, assert.ValidTransactionStatus(currentStatus),
    "unknown transaction status",
    "transaction_id", txnID, "status", currentStatus); err != nil {
    return err
}

if err := a.That(ctx, assert.TransactionCanTransitionTo(currentStatus, "APPROVED"),
    "illegal status transition",
    "transaction_id", txnID,
    "from", currentStatus, "to", "APPROVED"); err != nil {
    return err
}
```

Composition — revert guard:

```go
a := assert.New(ctx, logger, "transaction", "revert-transaction")
if err := a.That(ctx, assert.TransactionCanBeReverted(status, hasParent),
    "transaction cannot be reverted",
    "transaction_id", txnID,
    "status", status,
    "has_parent", hasParent); err != nil {
    return err
}
```

### Network / infrastructure

| Predicate                       | What it validates                           |
| ------------------------------- | ------------------------------------------- |
| `ValidUUID(s string) bool`      | Well-formed UUID (v1–v7 accepted)           |
| `ValidPort(port string) bool`   | `"1"` to `"65535"` as decimal string        |
| `ValidSSLMode(mode string) bool`| PostgreSQL SSL modes                        |

Composition — guarding configuration at bootstrap:

```go
a := assert.New(ctx, logger, "bootstrap", "parse-config")
if err := a.That(ctx, assert.ValidPort(cfg.Port),
    "invalid port in config",
    "port", cfg.Port); err != nil {
    return err
}
```

### Time

| Predicate                                             | What it validates                    |
| ----------------------------------------------------- | ------------------------------------ |
| `DateNotInFuture(date time.Time) bool`                | `date <= time.Now()`                 |
| `DateAfter(date, reference time.Time) bool`           | `date > reference`                   |

Composition — guard against clock-skew / bad input:

```go
a := assert.New(ctx, logger, "ingest", "accept-event")
if err := a.That(ctx, assert.DateNotInFuture(event.Timestamp),
    "event timestamp in the future",
    "event_id", event.ID,
    "timestamp", event.Timestamp.Format(time.RFC3339)); err != nil {
    return err
}
```

---

## 5. Composition Pattern

The division of labor is deliberate and strict:

| Layer       | Responsibility                                      | Observability |
| ----------- | --------------------------------------------------- | ------------- |
| Predicates  | Pure domain logic — `bool` return                   | None          |
| Asserter    | Observability trident on failure (log + span + metric) | All           |

This separation means:

- Predicates are cheap to test (pure functions, no mocks)
- Predicates are cheap to compose (any Boolean combination)
- Predicates are cheap to share across packages (no dependency on logger/metrics)
- Asserter carries the observability weight — a single call site, three outputs

★ Insight ─────────────────────────────────────
The predicates ARE the business rules. `assert.DebitsEqualCredits` is not "defensive
code that happens to check the accounting invariant" — it IS the accounting invariant,
expressed as executable code. A codebase that composes canonical predicates with
asserters has its regulatory rulebook encoded as runtime-enforced contracts. A codebase
that hand-rolls predicates has its rulebook encoded as prose-in-code-review, which
drifts the moment someone's pattern is a little different than canon.
─────────────────────────────────────────────────

### Canonical composition sites

| Site                             | Composition                                                                 |
| -------------------------------- | --------------------------------------------------------------------------- |
| Posting engine entry             | `DebitsEqualCredits` + `NonZeroTotals` + `PositiveDecimal` per entry        |
| Status transition handler        | `ValidTransactionStatus` + `TransactionCanTransitionTo`                     |
| Hold release                     | `BalanceSufficientForRelease` + `PositiveDecimal`                           |
| Revert guard                     | `TransactionCanBeReverted`                                                  |
| Config bootstrap                 | `ValidPort` + `ValidSSLMode` + `ValidUUID` (for static IDs)                 |
| Inbound event acceptance         | `DateNotInFuture` + `NotEmpty` (ids) + `ValidTransactionStatus` (payload)   |

---

## 6. The Observability Trident

Every assertion failure produces three outputs. They are emitted unconditionally when
the asserter is correctly initialized — the consumer cannot opt into "log only" or
"metric only" without modifying the asserter itself.

### Layer 1 — Structured log

```
ERROR assertion failed: double-entry violation: debits != credits
  component=ledger
  operation=post-transaction
  assertion=That
  debits=150.00
  credits=149.50
  transaction_id=abc-123
```

Emitted via the `log.Logger` passed to `assert.New`. Fields: `component`, `operation`,
`assertion` (method name), `message`, and all `keysAndValues` the caller provided.

### Layer 2 — OTel span event

Event name: `assertion.failed`, attached to the **active span** on the context.

Attributes:

| Attribute              | Value                               |
| ---------------------- | ----------------------------------- |
| `assertion.type`       | Method name (`That`, `NotNil`, ...) |
| `assertion.message`    | The message string                  |
| `assertion.component`  | From `assert.New`                   |
| `assertion.operation`  | From `assert.New`                   |
| All `keysAndValues`    | As span attributes                  |

The span's status is NOT automatically set to Error — the asserter only adds the event.
If the caller wants to mark the span failed, it must do so explicitly.

### Layer 3 — Metric

Counter `assertion_failed_total`, incremented by 1 on each failure.

Labels:

| Label        | Source                              |
| ------------ | ----------------------------------- |
| `component`  | From `assert.New`                   |
| `operation`  | From `assert.New`                   |
| `assertion`  | Method name (`That`, `NotNil`, ...) |

Canonical PromQL for operator dashboards:

```promql
# Rate of assertion failures per component
sum by (component) (rate(assertion_failed_total[5m]))

# Top failing operations
topk(10, sum by (component, operation) (rate(assertion_failed_total[1h])))

# Alert: sustained double-entry violations (ledger-scoped)
sum(rate(assertion_failed_total{component="ledger", operation="post-transaction"}[10m])) > 0
```

★ Insight ─────────────────────────────────────
`assertion_failed_total{assertion="DebitsEqualCredits"}` is a regulatory-grade metric,
not a debugging metric. A spike is a **potential accounting event** — auditors will
ask for the trace. The fact that this signal has three redundant channels (log for
grep, span event for trace correlation, metric for alerting) means no operator can
plausibly claim "we didn't know" after a ledger drift. That's the point.
─────────────────────────────────────────────────

### Production mode behavior

When `runtime.SetProductionMode(true)` is active (or `ENV=production`), the asserter:

- **Suppresses stack traces** in both the log and the span event
- Keeps all other fields identical

In development mode, stack traces are included to help debugging. The choice is binary
— there is no "include N frames" tuning.

---

## 7. AssertionError Unwrapping

Every asserter method returns `*assert.AssertionError` on failure. Error boundaries
MUST unwrap the structural context to preserve observability in logs.

### Canonical unwrap pattern

```go
var assertErr *assert.AssertionError
if errors.As(err, &assertErr) {
    logger.Error("assertion violated",
        "component", assertErr.Component,
        "operation", assertErr.Operation,
        "assertion", assertErr.Assertion,
        "message",   assertErr.Message,
        "context",   assertErr.Context,  // map[string]any of keysAndValues
    )
}
```

### Sentinel check

```go
if errors.Is(err, assert.ErrAssertionFailed) {
    // This is an assertion failure (any type). Use for flow-control
    // decisions without needing the structural context.
}
```

### Where to unwrap

| Boundary                        | What to do                                                          |
| ------------------------------- | ------------------------------------------------------------------- |
| Fiber `ErrorHandler`            | Unwrap, log structured, return 500                                  |
| gRPC unary/stream interceptor   | Unwrap, log structured, convert to `codes.Internal`                 |
| RabbitMQ consumer callback      | Unwrap, log structured, Nack with `requeue=false` (invariant bug)   |
| HTTP middleware error-handler   | Unwrap, log structured, do not leak internal invariants to response |
| Outer `main` defer              | Unwrap, log structured, exit non-zero                               |

### HTTP status code mapping

**AssertionError → HTTP 500, never 400.** Assertion failures represent **internal
invariant violations**, not user-input errors. Returning 400 implies the client made a
bad request, which misleads both the caller and the operator triaging the incident.

```go
// WRONG:
if assertErr != nil {
    return c.Status(400).JSON(fiber.Map{"error": "bad input"}) // misleading
}

// RIGHT:
if assertErr != nil {
    return c.Status(500).JSON(fiber.Map{"error": "internal invariant violated"})
}
```

The one exception is when the assertion wraps a clearly-user-caused validation (e.g.,
`NotEmpty` on a user-provided field at a public API boundary) — in that case, validate
at the edge with a normal error path before the invariant check, so the assertion is
reserved for actual invariants.

---

## 8. Decision Tree — panic vs assert vs error

Three-way decision every Go engineer makes, every day, in a Lerian codebase:

| Choice   | When                                                         | Observability |
| -------- | ------------------------------------------------------------ | ------------- |
| `panic`  | **Never** — except `regexp.MustCompile` with string literal  | Crash         |
| `assert` | Invariant that SHOULD always hold — violation is a bug       | Trident       |
| `error`  | Expected failure mode — user input, I/O, external system     | Normal        |

### `panic` — effectively banned

Zero-panic policy. The ONLY accepted `panic` in Lerian code is `regexp.MustCompile(...)`
where the argument is a compile-time string literal constant. That specific call is
acceptable because the panic can only fire if the regex literal is malformed at
compile time, which surfaces during development, not in production.

Everything else returns an error. No exceptions. A `panic` that reaches production
crashes the service and loses the request; the trident explicitly exists so that
production never needs `panic` to be heard.

### `assert` — for invariants

An **invariant** is something that the code path's caller/callee contract guarantees
will be true. A violation is a bug, not a user error or external failure. When an
invariant is violated, the right response is:

- Trident fires (visible to operators)
- Error propagates (callers can decide how to respond)
- Process keeps running (no crash)

### `error` — for expected failures

An **expected failure** is a normal, anticipated outcome of calling the function:

- User input that does not validate
- External system that returned 503
- Database connection that refused
- Context that was cancelled

Expected failures use normal error returns. They do NOT need the trident because:

- They are not bugs (no operator action needed for each occurrence)
- They are already handled by domain-level metrics (e.g., HTTP error rate, DB error counter)

### Worked examples

| Scenario                                                       | Choice | Reasoning                                                                                                                                   |
| -------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `ctx.Done()` fires during a DB query                            | error  | Expected — request was cancelled or timeout reached                                                                                         |
| Database returns `connection refused`                           | error  | Expected external failure                                                                                                                    |
| User POSTs `amount = "not a number"`                            | error  | Expected input failure — validate at edge                                                                                                    |
| DB query returns success but `rows` is nil                      | assert | Invariant — the driver contract says nil is impossible on success                                                                            |
| Transaction status read from own DB is `"BANANA"`               | assert | Invariant — we wrote it, we control the enum                                                                                                 |
| Tenant ID missing from request context after JWT middleware     | assert | Invariant — the middleware guarantees it; if missing, middleware has a bug                                                                   |
| Account balance goes negative after hold release                | assert | Invariant — accounting laws                                                                                                                  |
| RabbitMQ broker down during publish                             | error  | Expected external failure                                                                                                                    |
| `regexp.MustCompile("[a-z]+")` at package init                   | panic  | Accepted exception — compile-time constant                                                                                                   |
| `regexp.MustCompile(userProvidedPattern)`                        | error  | NOT an exception — user input; validate and return error                                                                                     |
| Impossible `default:` branch in exhaustive switch over enum      | assert | Invariant via `a.Never(ctx, ...)`                                                                                                            |
| JWT signature invalid                                            | error  | Expected failure — auth boundary rejection                                                                                                   |
| Double-entry debits != credits at posting time                   | assert | Invariant — accounting law                                                                                                                   |

★ Insight ─────────────────────────────────────
The question "panic, assert, or error?" has a simple diagnostic: **who is responsible
when this fires?** If a user is responsible (bad input), it's an error. If an operator
is responsible (bug, unexpected state), it's an assert. If nobody can act (compile-time
wrong regex), it's the one accepted panic. Anything that doesn't fit is an error.
─────────────────────────────────────────────────

---

## 9. Testing Patterns

Proving assertions fire correctly is part of the test suite, not a manual exercise.

### Inject a test metrics factory

```go
import "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry/metrics"

func TestPostTransaction_FiresAssertionOnUnbalanced(t *testing.T) {
    testFactory := metrics.NewTestFactory()
    assert.InitAssertionMetrics(testFactory)

    a := assert.New(ctx, testLogger, "ledger", "post-transaction")
    err := PostTransaction(ctx, a, buildUnbalancedTransaction())

    require.Error(t, err)
    require.True(t, errors.Is(err, assert.ErrAssertionFailed))

    // Verify the counter incremented with the expected labels
    require.Equal(t, int64(1), testFactory.CounterValue("assertion_failed_total",
        map[string]string{
            "component": "ledger",
            "operation": "post-transaction",
            "assertion": "That",
        }))
}
```

### Verify span event via in-memory OTel exporter

```go
import "go.opentelemetry.io/otel/sdk/trace/tracetest"

func TestPostTransaction_EmitsSpanEvent(t *testing.T) {
    exporter := tracetest.NewInMemoryExporter()
    // ... set up test tracer provider with this exporter

    _ = PostTransaction(ctx, a, buildUnbalancedTransaction())

    spans := exporter.GetSpans()
    require.Len(t, spans, 1)

    events := spans[0].Events
    require.Len(t, events, 1)
    require.Equal(t, "assertion.failed", events[0].Name)

    attrs := events[0].Attributes
    requireAttr(t, attrs, "assertion.component", "ledger")
    requireAttr(t, attrs, "assertion.operation", "post-transaction")
    requireAttr(t, attrs, "assertion.type", "That")
}
```

### AssertionError field-equality tests

```go
func TestPostTransaction_ReturnsStructuredAssertionError(t *testing.T) {
    err := PostTransaction(ctx, a, buildUnbalancedTransaction())

    var assertErr *assert.AssertionError
    require.True(t, errors.As(err, &assertErr))
    require.Equal(t, "ledger", assertErr.Component)
    require.Equal(t, "post-transaction", assertErr.Operation)
    require.Equal(t, "That", assertErr.Assertion)
    require.Contains(t, assertErr.Message, "double-entry violation")
}
```

### Production-drift mirror check

For every test that uses an `assert.<Predicate>`, verify the production code under test
ALSO uses the same predicate via an asserter. This is the systematic check for Angle 5:

```go
// For each test hitting a predicate:
func TestPostTransaction_BalancesEqual(t *testing.T) {
    txn := buildTransaction(100, 100)
    require.True(t, assert.DebitsEqualCredits(txn.Debits(), txn.Credits()))
    require.NoError(t, PostTransaction(ctx, a, txn))
}

// The production PostTransaction MUST also call a.That(ctx,
// assert.DebitsEqualCredits(...), ...) — otherwise the invariant is test-only.
```

One manual or automated cross-reference pass per PR catches the drift that Angle 5
sweeps surface across a whole codebase.

---

## 10. Anti-Pattern Catalog

Six anti-patterns with consequences. Each is a one-way door — once in production, the
damage compounds.

### 1. `panic()` for invariants

```go
// BEFORE:
if amount.IsNegative() {
    panic("amount must be positive")
}
```

**Consequence:** Crashes the service on an invariant that the asserter would have
reported non-fatally. Request is lost. Operators find a stack trace in logs but no
metric signal. Zero-panic policy violated.

### 2. Silent error return on invariant violation

```go
// BEFORE:
if debits.Cmp(credits) != 0 {
    return errors.New("unbalanced") // no metric, no trace
}
```

**Consequence:** Debit/credit mismatch is returned as a plain error. Log at the
boundary shows "unbalanced" but no `assertion_failed_total` metric, so dashboards
never alert. A silent, slow-motion ledger drift.

### 3. Reinvented predicates

```go
// BEFORE:
func debitsEqualCredits(d, c decimal.Decimal) bool {
    return d.Cmp(c) == 0
}
```

**Consequence:** DIY diverges from canon. The canonical `assert.DebitsEqualCredits`
may include non-zero-total checks, tolerance handling, or invariant upgrades in
future versions — the DIY version stays frozen. Cross-service behavior inconsistency.

### 4. Missing `InitAssertionMetrics`

```go
// Bootstrap:
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
// assert.InitAssertionMetrics missing
a := assert.New(ctx, logger, "ledger", "post")
_ = a.That(ctx, false, "test")
```

**Consequence:** Log and span event fire. Metric counter does not exist in the
registry, so Prometheus never scrapes it. Dashboards show flat lines even as
assertions fire thousands of times per minute during an incident.

### 5. Assertion only in tests

```go
// Test:
require.True(t, assert.DebitsEqualCredits(d, c))

// Production PostTransaction — no invariant check.
```

**Consequence:** Test suite passes. Production code blindly writes whatever debits and
credits the caller provides. First upstream bug that produces unbalanced input writes
corruption directly to the ledger. Silent drift until the first audit.

### 6. Opaque AssertionError in boundary logs

```go
// BEFORE — Fiber error handler:
ErrorHandler: func(c *fiber.Ctx, err error) error {
    logger.Error("request failed", "error", err.Error())
    return c.Status(500).JSON(...)
}
```

**Consequence:** Error is stringified. `Component`, `Operation`, `Assertion` labels are
embedded in the string, not as log fields. Operators cannot filter/group logs by these
dimensions. Incident triage requires correlating by timestamp to the span event to
recover the structure.

---

## 11. Bootstrap Order

The `assert.InitAssertionMetrics` call has a specific position in service bootstrap:

- AFTER logger initialization (assertions emit via the logger)
- AFTER telemetry initialization (uses the metrics factory)
- ALONGSIDE `runtime.InitPanicMetrics` (both read from the same `tl.MetricsFactory`)
- BEFORE any code path that might fire an assertion (i.e., before any handler / consumer
  / worker starts)

For the complete bootstrap sequence (logger → telemetry → runtime → assert →
infrastructure clients → server), see `ring:using-lib-commons` Section 2.

The two-line addition at the right point:

```go
// After opentelemetry.NewTelemetry(...):
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
assert.InitAssertionMetrics(tl.MetricsFactory)
```

---

## 12. Cross-References

This skill does not duplicate material available elsewhere. Use these pointers:

| For                                                         | See                                                            |
| ----------------------------------------------------------- | -------------------------------------------------------------- |
| Full lib-commons package catalog (22 packages)              | `ring:using-lib-commons` Section 1                             |
| Full bootstrap sequence with all clients                    | `ring:using-lib-commons` Section 2                             |
| Observability overview including panic recovery coverage    | `ring:using-lib-commons` Section 5                             |
| Single-angle assertions sweep (lower-detail version)        | `ring:using-lib-commons` Angle 16                              |
| Panic recovery + `SafeGo` + error reporter integration      | `ring:using-runtime`                                           |
| Running a full codebase standards sweep                     | `ring:dev-refactor`                                            |
| Consuming sweep tasks into a development cycle              | `ring:dev-cycle`                                               |

`ring:using-runtime` is the natural companion to this skill — `runtime` protects
against panics that would otherwise silently kill a goroutine; `assert` protects
against invariant violations that would otherwise silently corrupt state. Together,
they close both halves of the invisible-failure problem in Go services.

---

## 13. Cross-Cutting Patterns

Patterns that apply across all `commons/assert` usage.

### Nil-receiver safety

Every exported `Asserter` method is nil-receiver safe. Calling a method on a nil
`*Asserter` returns `ErrNilAsserter` (or equivalent) rather than panicking. This means
code paths that conditionally construct an asserter (e.g., when the logger is optional
in bootstrap) do not need a separate nil check at every call site.

### Production mode effects

`runtime.SetProductionMode(true)` affects the assertion output:

- Stack traces suppressed in logs and span events
- All other fields preserved
- Metric emission unchanged (production mode does not affect counters)

Development mode includes stack traces to aid debugging. The setting is global
(per-process) and is normally set once at bootstrap.

### Interaction with runtime

Asserter methods return errors. They do NOT panic. Therefore they do NOT trigger
`runtime.SafeGo` or `runtime.RecoverWithPolicy` recovery paths. This is intentional:

- `runtime` handles panics (goroutine-death prevention)
- `assert` handles invariant violations (state-corruption prevention)
- The two mechanisms are orthogonal and both are needed

A goroutine launched via `runtime.SafeGo` that fires an assertion: the assertion
returns an error; the goroutine decides what to do with it (return, log, retry); if the
goroutine then panics separately, `SafeGo` recovers. No overlap.

### Performance

Assertion hot-path cost:

- Success path: predicate evaluation + one `if` comparison — effectively free
- Failure path: one `*AssertionError` heap allocation + log line + span event + metric increment

Failure is expected to be rare (invariants should hold nearly always), so the allocation
on failure is acceptable. The success path has zero allocations — safe to place in
tight loops, request handlers, and message consumers.

---

## 14. Breaking Changes

### v4.x → v5.x (commons/assert)

No API-breaking changes in `commons/assert` across v4.2.0 → v5.x. All method
signatures, predicate signatures, and error types are source-compatible.

The module path bump from `github.com/LerianStudio/lib-commons/v4/...` to
`github.com/LerianStudio/lib-commons/v5/...` applies. See `ring:using-lib-commons`
Section 15 for the full module-bump migration checklist.

### v5.0.1+

Patch releases — no API changes to `commons/assert`. Check the latest v5.x tag for current patch level.

---
