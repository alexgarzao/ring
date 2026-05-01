---
name: ring:dev-streaming-instrumentation
description: |
  lib-streaming instrumentation orchestrator for Lerian Go services. Consumes the validated
  instrumentation-map.json produced by ring:streaming-event-mapping (Skill #1) and wires lib-streaming
  end-to-end: Catalog construction, Producer bootstrap, Emit instrumentation per eventable point,
  Outbox wiring (conditional on per-event posture), Manifest HTTP mount (conditional on HTTP surface),
  feature-flag-gated lifecycle with NoopEmitter fallback, MockEmitter-backed unit tests, Redpanda
  integration tests via testcontainers, and Toxiproxy chaos tests when outbox is wired. 13 gates
  mirroring systemplane's structure: detect → analyze → visual preview → dependency add → catalog +
  producer → emit → outbox → manifest → lifecycle → tests → 10 reviewers → user validation → activation
  guide. Detects and replaces non-canonical alternatives (sarama, watermill, segmentio/kafka-go, direct
  amqp091.Publish, raw franz-go). Each implementation gate dispatches ring:backend-engineer-golang.
  Loads canonical lib-streaming docs via WebFetch from main.

trigger: |
  - User requests streaming instrumentation for a Go service that has a validated
    docs/streaming/instrumentation-map.json from ring:streaming-event-mapping
  - Task mentions "wire lib-streaming", "instrument streaming events", "implement event emission",
    "add streaming.NewProducer", "Emit business events", "lib-streaming bootstrap"
  - Post-flight to ring:streaming-event-mapping (Skill #1)

skip_when: |
  - Service is not a Go project (lib-streaming is Go-only)
  - No instrumentation-map.json present (run ring:streaming-event-mapping first)
  - Task is documentation-only, configuration-only, or non-code

prerequisites: |
  - Go service codebase available for read+write access
  - docs/streaming/instrumentation-map.json present and validated (Gate 6 PM-approved by Skill #1)
  - lib-commons/v5 in go.mod (lib-streaming requires it)
  - At least one entry point where events will be emitted (HTTP/gRPC/worker/cron/consumer)

NOT_skip_when: |
  - "Service already has direct franz-go usage, leave it" → Direct franz-go bypasses lib-streaming's
    Catalog + DeliveryPolicy + outbox + DLQ + manifest + observability. NON-CANONICAL. Gate 2 removes it.
  - "We don't need the Catalog, just Emit raw events" → CANNOT. lib-streaming refuses Emit calls with
    DefinitionKey not in the registered Catalog. Bootstrap fails fast.
  - "Skip the manifest handler, it's overkill" → Manifest is the self-description endpoint clients use
    to discover the event taxonomy. Required unless service has zero HTTP surface (with justification).
  - "Outbox is overkill, all events can be best-effort" → Posture is per-event. If instrumentation-map
    has any event with outbox != never, outbox infra is REQUIRED. Skill installs lib-commons/outbox if
    missing — non-negotiable.
  - "We can skip the feature flag, just enable it" → STREAMING_ENABLED=false MUST preserve identical
    pre-instrumentation behavior. Backward compat is non-negotiable for rollback safety.
  - "Skip the 10 reviewers, lib-streaming is opinionated enough" → Library opinions don't catch
    instrumentation-site mistakes (pre-commit emission, leaked PII, wrong tenant source). 10 reviewers
    are MANDATORY.
  - "Pre-commit emission is fine for our use case" → Pre-commit emission breaks atomicity. Consumer
    sees the event before the DB row exists. CRITICAL events MUST emit post-commit, transactional via
    outbox.
  - "Honor JSON loosely, the events list is approximate" → JSON is the contract from PM-validated
    Skill #1 output. Drift = client integration breakage. Every field is mandatory and exact.

sequence:
  after: [ring:streaming-event-mapping]

related:
  complementary: [ring:streaming-event-mapping, ring:dev-cycle, ring:dev-implementation, ring:dev-devops,
                  ring:dev-unit-testing, ring:codereview, ring:dev-validation, ring:using-lib-commons,
                  ring:dev-systemplane-migration]

input_schema:
  description: |
    Receives instrumentation-map.json from ring:streaming-event-mapping (Skill #1) as the canonical
    input. If invoked standalone without an existing instrumentation-map.json, skill STOPS at Gate 0
    and instructs user to run ring:streaming-event-mapping first.
  fields:
    - name: instrumentation_map_path
      type: string
      description: "Path to instrumentation-map.json (default: docs/streaming/instrumentation-map.json)"
      required: false
      default: "docs/streaming/instrumentation-map.json"
    - name: lib_streaming_version
      type: string
      description: "Pinned lib-streaming version tag (default: latest stable; resolved at Gate 0 via gh api)"
      required: false
      default: "latest"
    - name: skip_gates
      type: array
      items: string
      description: "Gate identifiers to skip (e.g., '5' if zero events need outbox; '6' if no HTTP surface). Skill validates conditional skips and refuses unjustified skips."
      required: false

output_schema:
  format: markdown
  required_sections:
    - name: "Streaming Instrumentation Summary"
      pattern: "^## Streaming Instrumentation Summary"
      required: true
    - name: "Stack Detection"
      pattern: "^## Stack Detection"
      required: true
    - name: "Gate Results"
      pattern: "^## Gate Results"
      required: true
    - name: "Verification"
      pattern: "^## Verification"
      required: true
  metrics:
    - name: gates_passed
      type: integer
    - name: gates_failed
      type: integer
    - name: events_wired
      type: integer
    - name: emit_sites_inserted
      type: integer
    - name: non_canonical_files_removed
      type: integer
    - name: outbox_wired
      type: boolean
    - name: manifest_mounted
      type: boolean

---

# Streaming Instrumentation (lib-streaming)

<cannot_skip>

## CRITICAL: This Skill ORCHESTRATES. Agents IMPLEMENT.

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Detect stack, validate instrumentation-map.json, determine gates, pass context to agent, verify outputs, enforce order |
| **ring:backend-engineer-golang** | Load lib-streaming docs via WebFetch, implement following the canonical API, write tests with TDD |
| **10 reviewers** | Review at Gate 9 |

**CANNOT change scope:** the skill defines WHAT to implement (per the JSON from Skill #1). The agent implements HOW.

**FORBIDDEN: Orchestrator MUST NOT use Edit, Write, or Bash tools to modify Go source files.**
All code changes MUST go through `Task(subagent_type="ring:backend-engineer-golang")`. The orchestrator only verifies outputs (grep, go build, go test) — MUST NOT write implementation code.

**MANDATORY: TDD for all implementation gates (Gates 2-8).** MUST follow RED → GREEN → REFACTOR: write a failing test first, then implement to make it pass, then refactor for clarity/performance. MUST include in every dispatch: "Follow TDD: write failing test (RED), implement to make it pass (GREEN), then refactor for clarity/performance (REFACTOR)."

**MANDATORY: instrumentation-map.json is the contract.** Every EventDefinition, every Emit site, every DeliveryPolicy, every tenant source MUST come from the JSON exactly. The skill VALIDATES at Gate 0 that the JSON exists and is well-formed; from Gate 3 onward, the agent dispatches MUST treat the JSON as authoritative input. Drift between JSON and implementation = scope violation.

</cannot_skip>

---

## Streaming Architecture (lib-streaming, the model)

lib-streaming is a producer-only event-emission library. Three-step lifecycle:

1. `streaming.NewCatalog([]EventDefinition)` — declare every event up-front (immutable)
2. `streaming.NewProducer(ctx, cfg, opts...)` with `WithCatalog(catalog)` — opens connections, registers with `commons.Launcher`
3. `producer.Emit(ctx, EmitRequest{DefinitionKey, TenantID, Subject, Payload})` from request handlers and workers

Wire format: CloudEvents 1.0 binary mode for Kafka. Topic naming: `lerian.streaming.<resource>.<event>[.vN]`. Topics are SHARED across tenants; tenant carried on `ce-tenantid` header and partition key.

**Standards reference:** lib-streaming has no `streaming.md` standards file. The authoritative source is:

1. The `ring:using-lib-commons` skill for v5 surrounding-package overview
2. The lib-streaming `doc.go` and `AGENTS.md`

**WebFetch URLs (load via every gate dispatch):**

- Package docs: `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go`
- Agent guide: `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md`

**Three named delivery postures** (axis: `Direct × Outbox × DLQ` per event):

| Posture | Direct | Outbox | DLQ | Use when |
|---------|--------|--------|-----|----------|
| CRITICAL | skip | always | on_routable_failure | Loss is correctness/compliance breach; atomic with DB write |
| IMPORTANT | direct | fallback_on_circuit_open | on_routable_failure | Direct in normal ops; survives broker outage; recoverable |
| OBSERVATIONAL | direct | never | never | Analytics-grade; loss acceptable; cheap |
| CUSTOM | per-event | per-event | per-event | None of the above fits — written rationale ≥80 chars from Skill #1 |

### MANDATORY: Canonical Import Paths

Agents MUST use these exact import paths. MUST NOT invent paths or import lib-streaming `internal/` subpackages.

| Alias | Import Path | Purpose |
|-------|-------------|---------|
| `streaming` | `github.com/LerianStudio/lib-streaming` | `Producer`, `Emitter`, `NewProducer`, `NewNoopEmitter`, `NewCatalog`, `EventDefinition`, `EmitRequest`, options |
| `streamingtest` | `github.com/LerianStudio/lib-streaming/streamingtest` | `MockEmitter`, `AssertEventEmitted`, `WaitForEvent` (test-only) |
| `commons` | `github.com/LerianStudio/lib-commons/v5/commons` | `commons.App`, `commons.Launcher` (lifecycle integration) |
| `outbox` | `github.com/LerianStudio/lib-commons/v5/commons/outbox` | `OutboxRepository`, Dispatcher (only when Gate 5 is active) |
| `clog` | `github.com/LerianStudio/lib-commons/v5/commons/log` | `WithLogger` value type |
| `cmetrics` | `github.com/LerianStudio/lib-commons/v5/commons/opentelemetry/metrics` | `WithMetricsFactory` value type |

**⛔ HARD GATE:** Agent MUST NOT import `lib-streaming/internal/*` — those packages are not exported. Use root `streaming` and `streamingtest` only.

### MANDATORY: Three Emitter Implementations

| Implementation | When | Construction |
|----------------|------|--------------|
| `*streaming.Producer` | `STREAMING_ENABLED=true` | `streaming.NewProducer(ctx, cfg, opts...)` |
| `Emitter` (returned as `NoopEmitter` internally) | `STREAMING_ENABLED=false` | `streaming.NewNoopEmitter()` |
| `*streamingtest.MockEmitter` | Tests | `streamingtest.NewMockEmitter()` |

Service code depends on the `streaming.Emitter` INTERFACE, not on `*Producer`. This lets `NoopEmitter` and `MockEmitter` substitute transparently.

### MANDATORY: Agent Instruction (include in EVERY gate dispatch)

MUST include these instructions verbatim in every dispatch to `ring:backend-engineer-golang`:

> **STANDARDS:** WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go` for the canonical event model. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md` for invariants. Follow the lib-streaming public API exactly. The root `streaming` package and `streamingtest` are the ONLY valid surfaces.
>
> **IMPORTS:** Use only the canonical import paths from the skill. Do NOT import `lib-streaming/internal/*`. Do NOT use direct franz-go / sarama / amqp091 / watermill / segmentio / nats — those are non-canonical for outbound business events.
>
> **CONTRACT:** `docs/streaming/instrumentation-map.json` is the canonical input. Every EventDefinition, every Emit site, every DeliveryPolicy field MUST match the JSON exactly. NO drift.
>
> **TDD:** For implementation gates (2-8), follow TDD methodology — write a failing test first (RED), then implement to make it pass (GREEN), then refactor for clarity/performance (REFACTOR). MUST have test coverage for every change.
>
> **TENANT:** Tenant identity comes from `tmcore.GetTenantIDContext(ctx)` (or as specified in the JSON's `tenant_source_at_site`). MUST NOT hardcode. MUST NOT default to empty.

---

## Existence ≠ Compliance HARD GATE

**"The service already has lib-streaming code" is NOT a reason to skip any gate.**

If the existing code does any of these, it is **NON-COMPLIANT**:

- Constructs `streaming.Producer` without `WithCatalog` → catalog-less producer; Emit always fails
- Calls `Emit` with `DefinitionKey` not in the catalog → runtime error per call
- Uses direct `franz-go` / `sarama` / `watermill` outside lib-streaming → non-canonical
- Reads tenant from somewhere other than the JSON-specified source → drift from contract
- Lacks `STREAMING_ENABLED` feature flag → no rollback path
- Lacks `commons.Launcher.Add` lifecycle wiring → leaks goroutines + connections at shutdown
- Mounts `NewStreamingHandler` on a public port without auth → information disclosure
- Has Emit calls in pre-commit positions for CRITICAL events → atomicity violation

**Compliance verification requires EVIDENCE, not assumption.** Gate 0 Phase 2 (lib-streaming compliance audit) is MANDATORY when lib-streaming code is detected.

**If ANY audit check is NON-COMPLIANT → the corresponding gate MUST execute to fix it. CANNOT skip.**

---

## Severity Calibration

| Severity | Criteria | Examples |
|----------|----------|----------|
| **CRITICAL** | Compile-breaking; security; correctness violation | Producer constructed without WithCatalog; CRITICAL event with `outbox=never`; manifest mounted unauthenticated; tenant hardcoded; pre-commit emission |
| **HIGH** | Missing core surface; wrong lifecycle; silent failure | No `commons.Launcher.Add`; no `Close()` in shutdown path; non-canonical event-emission code (sarama/watermill) still present; STREAMING_ENABLED missing |
| **MEDIUM** | Partial compliance; observability gap | Missing `WithLogger`/`WithTracer`/`WithMetricsFactory`; no `runtime.InitPanicMetrics` / `assert.InitAssertionMetrics` call; no MockEmitter-based unit tests |
| **LOW** | Documentation, naming | Activation guide missing consumer-tenant-filter checklist; missing comments in bootstrap |

MUST report all severities. CRITICAL: STOP immediately. HIGH: Fix before gate pass. MEDIUM: Fix in iteration. LOW: Document.

---

## Pressure Resistance

| User Says | This Is | Response |
|-----------|---------|----------|
| "Service has direct franz-go, leave it" | COMPLIANCE_BYPASS | "Direct franz-go bypasses Catalog + DeliveryPolicy + outbox + manifest + standardized observability. NON-CANONICAL. Gate 2 removes it." |
| "Skip Gate 0 audit, we know what's there" | DISCIPLINE_BYPASS | "Gate 0 verifies the JSON contract is well-formed AND audits any existing lib-streaming code. Without it, Gate 3 may collide with stale code. NOT skippable." |
| "JSON from Skill #1 is a draft, we'll deviate" | CONTRACT_BYPASS | "JSON is PM-validated. Drift breaks the client subscription contract. Every field is binding." |
| "Skip the visual preview, just instrument" | GOVERNANCE_BYPASS | "Gate 1.5 is the user's only chance to catch wrong knob selection before code touches files. NEVER skippable." |
| "Outbox is overkill, all events best-effort" | POSTURE_BYPASS | "Posture is per-event. If JSON has any event with outbox != never, outbox is REQUIRED. Skill installs lib-commons/outbox if missing." |
| "Manifest handler is overkill, skip Gate 6" | SCOPE_REDUCTION | "Manifest is self-description for client discovery. SKIP only if service has zero HTTP surface, with justification — and then operators lose discoverability." |
| "Skip the feature flag, we're greenfield" | ROLLBACK_BYPASS | "STREAMING_ENABLED=false MUST preserve identical pre-instrumentation behavior. Without it, rollback requires code revert. NEVER skippable." |
| "NoopEmitter is unnecessary; nil works" | NIL_HAZARD | "Nil emitter PANICS on Emit. NoopEmitter is no-op. The constructor enforces this; you don't get to choose." |
| "Pre-commit emission is fine" | ATOMICITY_BYPASS | "Pre-commit means consumer sees event before DB row. CRITICAL events break consumer reconciliation. MUST emit post-commit; outbox=always for transactional atomicity." |
| "Skip code review, lib-streaming is simple" | QUALITY_BYPASS | "Library simplicity hides instrumentation-site mistakes (wrong tenant, leaked PII, pre-commit emission). MANDATORY 10 reviewers." |
| "Skip TDD, manual testing covered it" | TDD_BYPASS | "MANDATORY: RED → GREEN → REFACTOR for every gate. Manual testing does not count." |
| "Custom posture without rationale, just direct=skip" | RATIONALE_BYPASS | "Skill #1 enforced ≥80-char rationale on CUSTOM. Skill #2 inherits that contract. CANNOT alter or remove." |
| "Skip Gate 11 activation guide, devs read code" | OPERATOR_BYPASS | "Activation guide is for operators, not devs. Without it, ops cannot enable/disable safely. NEVER skippable." |
| "Hardcode tenant for tests" | TEST_BYPASS | "Tests use streamingtest.MockEmitter with explicit tenant per request. Hardcoding hides tenant-source bugs in production. Tests must exercise the real tenant path." |
| "Reuse existing audit-log emission, skip new wiring" | RECYCLING_BYPASS | "Audit logs are NOT business events. Different consumer model, different retention, different schema. Wire lib-streaming separately." |
| "Mount manifest on public port, it's authenticated" | NETWORK_BYPASS | "Authentication necessary, not sufficient. Network-layer separation (path prefix + ACL) is defense-in-depth. Operator doc must call out network policy." |

---

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "JSON is suggestion, code is truth" | JSON is the PM-validated contract. Code that drifts from JSON breaks client subscriptions. | **MUST honor every field exactly** |
| "Catalog can be inferred from Emit calls" | Catalog must be registered BEFORE Start; Emit-time inference is impossible. | **MUST construct Catalog from JSON at bootstrap** |
| "Emit at any point in the function" | Emission_timing in JSON is mandatory: post-commit for CRITICAL/IMPORTANT, etc. | **MUST honor emission_timing per site** |
| "Producer can be a singleton constructed lazily" | Catalog is registered at construction. Lazy construction = late catalog = wrong-key Emits succeed silently. | **MUST construct at bootstrap with full catalog** |
| "Skip WithLogger/WithTracer; defaults are fine" | Defaults are no-op. Production observability requires explicit lib-commons wiring. | **MUST pass WithLogger, WithMetricsFactory, WithTracer** |
| "NoopEmitter is for tests, use nil in production" | nil emitter PANICS on Emit. NoopEmitter is the kill switch. | **MUST use NoopEmitter for STREAMING_ENABLED=false** |
| "Direct franz-go is faster" | Bypassing lib-streaming bypasses every opinion the library enforces. NON-CANONICAL. | **MUST go through lib-streaming Producer** |
| "Outbox migration is out of scope" | If JSON declares outbox events, outbox infra is REQUIRED — including migration if missing. | **Gate 5 installs lib-commons/outbox if absent** |
| "Manifest is decoration, skip it" | Manifest is the discovery surface. Skipping means clients cannot enumerate event taxonomy. | **REQUIRED unless service has zero HTTP** |
| "Skip Close() in shutdown" | Missing Close() leaks franz-go goroutines AND aborts in-flight produces. | **MUST call producer.Close() before DB close** |
| "Skip MockEmitter unit tests" | Without unit-level event-emission tests, refactors silently break event production. | **MUST cover every Emit site with MockEmitter** |
| "Hardcode test tenant" | Tests must exercise real tenant path. Hardcoding hides production bugs. | **MUST extract tenant from test ctx** |
| "Skip backward compat tests" | STREAMING_ENABLED=false path must be identical to pre-instrumentation. Without proof, rollback unsafe. | **MUST write TestStreaming_BackwardCompatibility** |
| "Run reviewers sequentially for cost" | Reviewers are independent. Sequential = wall-time waste; doesn't reduce cost. | **MUST dispatch all 10 in parallel** |

---

## Gate Overview

| Gate | Name | Condition | Agent |
|------|------|-----------|-------|
| 0 | Stack Detection + JSON Validation + Compliance Audit + Non-Canonical Detection | Always | Orchestrator |
| 1 | Codebase Analysis | Always | ring:codebase-explorer |
| 1.5 | Visual Implementation Preview | Always; user must approve | Orchestrator (via ring:visualize) |
| 2 | lib-streaming Dependency + Non-Canonical Removal | Skip only if lib-streaming pinned in go.mod AND zero non-canonical detected | ring:backend-engineer-golang |
| 3 | Catalog Construction + Producer Bootstrap | Always | ring:backend-engineer-golang |
| 4 | Emit Instrumentation per Eventable Point | Always | ring:backend-engineer-golang |
| 5 | Outbox Wiring (install if missing) | Conditional — required if any event has `outbox != "never"` | ring:backend-engineer-golang |
| 6 | Manifest HTTP Mount | Conditional — required unless service has zero HTTP surface (with justification) | ring:backend-engineer-golang |
| 7 | Wiring + Lifecycle + Backward Compat ⛔ NEVER SKIPPABLE | Always | ring:backend-engineer-golang |
| 8 | Tests | Always | ring:backend-engineer-golang |
| 9 | Code Review (10 reviewers) | Always | 10 parallel reviewers |
| 10 | User Validation | Always | User |
| 11 | Activation Guide | Always | Orchestrator |

MUST execute gates sequentially. CANNOT skip or reorder.

### Conditional Gate Justification

A gate marked Conditional may be skipped ONLY when its skip condition is met AND documented. Specifically:

- **Gate 2** SKIP only if Gate 0 returns `lib-streaming pinned in go.mod` AND Gate 0 Phase 3 returns zero non-canonical alternatives.
- **Gate 5** SKIP only if Gate 0 verifies `summary.events_critical == 0` AND every event in JSON has `delivery_policy.outbox == "never"`.
- **Gate 6** SKIP only if Gate 0 returns `HTTP framework: NONE` AND `gRPC: NO` (pure background worker). MUST surface justification in final report.

Any other skip = unjustified = reject.

---

## Gate 0: Stack Detection + JSON Validation + Compliance Audit + Non-Canonical Detection

**Orchestrator executes directly. No agent dispatch.**

**This gate has FOUR phases: JSON contract validation, stack detection, lib-streaming compliance audit (if present), and non-canonical detection.**

### Phase 1: instrumentation-map.json Contract Validation

```text
VALIDATE the JSON before anything else:

1. File exists at docs/streaming/instrumentation-map.json (or path from input_schema)
2. Valid JSON, parseable
3. Top-level fields present: schema_version, service_name, tenant_source, events[], summary
4. events[] non-empty
5. Every event has all required fields:
   definition_key, resource_type, event_type, schema_version, data_content_type,
   is_system_event, description, instrumentation_sites[], payload_sketch, tenant_source_at_site,
   posture, posture_rationale, delivery_policy
6. Every definition_key matches `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`
7. (resource_type, event_type, schema_version) is unique across events
8. posture in {CRITICAL, IMPORTANT, OBSERVATIONAL, CUSTOM}
9. delivery_policy is consistent with posture for non-CUSTOM postures
10. Every event with is_system_event=false has tenant_source_at_site != ""
11. Every CUSTOM event has posture_rationale length >= 80
12. Every event has at least one instrumentation_sites entry
```

<block_condition>
HARD GATE: If JSON is missing → STOP. Output: "Run ring:streaming-event-mapping (Skill #1) first to produce docs/streaming/instrumentation-map.json."

HARD GATE: If JSON validation fails → STOP. Output the failing checks. Do NOT attempt to repair the JSON; loop back to Skill #1.
</block_condition>

### Phase 2: Stack Detection

```text
DETECT (run in parallel):

1. Go project + version:    grep "^go " go.mod | head -1
2. lib-commons v5:          grep "lib-commons/v5" go.mod
3. lib-streaming present:   grep "lib-streaming" go.mod (capture version pin)
4. lib-commons/outbox:      grep "lib-commons/v5/commons/outbox" go.mod internal/
5. HTTP framework:
   - Fiber:    grep -rn "gofiber/fiber" internal/ go.mod
   - Echo:     grep -rn "labstack/echo" internal/ go.mod
   - Gin:      grep -rn "gin-gonic/gin" internal/ go.mod
   - net/http: grep -rn "net/http" internal/cmd/ internal/http/
6. gRPC server:             grep -rn "grpc.NewServer" internal/
7. commons.Launcher:        grep -rn "commons.Launcher\|launcher.Add\|commons.App" internal/
8. Tenant source (cross-check against JSON's tenant_source field):
   grep -rn "tmcore.GetTenantIDContext\|GetTenantID(ctx" internal/
9. Database handles:
   - Postgres:  grep -rn "database/sql\|jackc/pgx" internal/
   - MongoDB:   grep -rn "go.mongodb.org/mongo-driver" internal/
10. lib-commons logger:     grep -rn "lib-commons/v5/commons/log" internal/
11. lib-commons metrics:    grep -rn "lib-commons/v5/commons/opentelemetry/metrics" internal/
12. lib-commons multitenancy: grep -rn "lib-commons/v5/commons/multitenancy" internal/
13. Resolve latest lib-streaming tag if input is "latest":
    gh api repos/LerianStudio/lib-streaming/releases/latest --jq .tag_name
```

**Output format:**

```text
STACK DETECTION RESULTS:
| Aspect                          | Detected                                    |
|---------------------------------|---------------------------------------------|
| Go version                      | 1.25                                        |
| lib-commons v5                  | YES (v5.1.0)                                |
| lib-streaming                   | NOT PRESENT                                 |
| Resolved lib-streaming version  | v0.2.0                                      |
| lib-commons/outbox              | NOT PRESENT                                 |
| HTTP framework                  | Fiber                                       |
| gRPC                            | NO                                          |
| commons.Launcher                | YES                                         |
| Tenant source matches JSON      | YES (tmcore.GetTenantIDContext)             |
| Postgres                        | YES                                         |
| MongoDB                         | NO                                          |
| lib-commons logger              | YES                                         |
| lib-commons metrics             | YES                                         |
| lib-commons multitenancy        | YES                                         |
```

### Phase 3: lib-streaming Compliance Audit (only if lib-streaming detected)

If Phase 2 step 3 returns results, MUST run a compliance audit:

```text
AUDIT (only if existing lib-streaming code detected):

NOTE: All S-checks are POSITIVE (absence of canonical pattern = NON-COMPLIANT).

S1. Producer construction with WithCatalog:
    grep -rn "streaming.NewProducer" internal/
    Verify each construction has WithCatalog option
    (no match OR WithCatalog absent = NON-COMPLIANT → Gate 3 MUST fix)

S2. Catalog construction:
    grep -rn "streaming.NewCatalog\|streaming.EventDefinition" internal/
    Verify catalog has every event from instrumentation-map.json
    (missing events = NON-COMPLIANT → Gate 3 MUST add)

S3. Lifecycle integration:
    grep -rn "launcher.Add.*streaming\|launcher.Add.*producer" internal/
    Verify producer is registered with commons.Launcher
    (no match = NON-COMPLIANT → Gate 7 MUST fix)

S4. Required options present:
    grep -rn "streaming.WithLogger\|streaming.WithMetricsFactory\|streaming.WithTracer" internal/
    All three MUST be present
    (any missing = NON-COMPLIANT → Gate 3 MUST add)

S5. Emit calls match catalog:
    grep -rn "\.Emit(" internal/ | grep -i "streaming\|emitter"
    Every Emit's DefinitionKey MUST exist in the catalog
    (mismatch = NON-COMPLIANT → Gate 3/4 MUST fix)

S6. Manifest mount (if HTTP):
    grep -rn "streaming.NewStreamingHandler\|admin.Mount.*streaming" internal/
    Verify mounted on router behind auth middleware
    (no match AND HTTP present = NON-COMPLIANT → Gate 6 MUST add)

S7. Feature flag:
    grep -rn "STREAMING_ENABLED\|SystemplaneEnabled\|StreamingEnabled" internal/ config/
    (no match = NON-COMPLIANT → Gate 7 MUST add)

S8. NoopEmitter for flag-off:
    grep -rn "streaming.NewNoopEmitter\|NewNoopEmitter" internal/
    (no match = NON-COMPLIANT → Gate 7 MUST add)

S9. Tenant from canonical source:
    For each Emit call, verify TenantID is set from tmcore.GetTenantIDContext or per JSON
    (hardcoded tenant or empty = CRITICAL → Gate 4 MUST fix)

S10. PII redaction (if any payload field is PII-annotated in JSON):
     Verify the producer has WithRedaction set or payload doesn't include PII
     (PII without redaction = CRITICAL → Gate 3 MUST fix)
```

**Output format:**

```text
LIB-STREAMING COMPLIANCE AUDIT:
| Component                       | Status                       | Evidence       | Gate Action          |
|---------------------------------|------------------------------|----------------|----------------------|
| Producer + WithCatalog          | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 3: SKIP / FIX   |
| Catalog matches JSON            | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 3: SKIP / FIX   |
| Lifecycle (launcher.Add)        | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 7: SKIP / FIX   |
| Required options                | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 3: SKIP / FIX   |
| Emit calls match catalog        | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 4: SKIP / FIX   |
| Manifest mount                  | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 6: SKIP / FIX   |
| Feature flag                    | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 7: SKIP / FIX   |
| NoopEmitter                     | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 7: SKIP / FIX   |
| Tenant source                   | COMPLIANT / NON-COMPLIANT    | {grep results} | Gate 4: SKIP / FIX   |
| PII redaction                   | COMPLIANT / NON-COMPLIANT / N/A | {grep results} | Gate 3: SKIP / FIX |
```

**HARD GATE: A gate can only be marked as SKIP when ALL its compliance checks are COMPLIANT with evidence. One NON-COMPLIANT row → gate MUST execute.**

### Phase 4: Non-Canonical Detection (MANDATORY)

Always runs, regardless of lib-streaming presence.

```text
DETECT non-canonical event-emission code:

N1. Direct franz-go (NOT via lib-streaming):
    grep -rn "twmb/franz-go" internal/ | grep -v "lib-streaming"

N2. sarama (Shopify or IBM):
    grep -rn "Shopify/sarama\|IBM/sarama" go.mod internal/

N3. watermill:
    grep -rn "ThreeDotsLabs/watermill" go.mod internal/

N4. segmentio/kafka-go:
    grep -rn "segmentio/kafka-go" go.mod internal/

N5. Direct CloudEvents SDK (outside lib-streaming):
    grep -rn "cloudevents/sdk-go" internal/ | grep -v "lib-streaming"

N6. Direct amqp091.Publish (used as event broadcast — NOT for command queues):
    grep -rn "amqp091.*Publish\|channel.Publish" internal/
    Distinguish business-event broadcast from internal command queue (lib-commons/rabbitmq is fine)

N7. NATS:
    grep -rn "nats-io/nats.go" go.mod internal/

N8. Redis Streams as event bus (XADD):
    grep -rn "XADD\|redis.*Stream" internal/

N9. Custom event-bus env vars:
    grep -rn "KAFKA_BROKERS\|EVENT_BUS_\|MESSAGE_BUS_" .env.example config/ internal/
    (only KAFKA_BROKERS used outside STREAMING_BROKERS context)
```

**If N1-N8 detected:** report as `NON-CANONICAL EVENT-EMISSION DETECTED`. Gate 2 MUST remove these and replace with lib-streaming.

**If N9 detected:** report as `NON-CANONICAL EVENT-BUS ENV VARS DETECTED`. Gate 2 MUST replace with `STREAMING_*` env vars.

<block_condition>
HARD GATE: Non-canonical findings BLOCK progression past Gate 2.
</block_condition>

---

## Gate 1: Codebase Analysis

**Always executes. Builds the implementation roadmap for all subsequent gates.**

**Dispatch `ring:codebase-explorer`:**

> **STANDARDS:** WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go`. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md`.
>
> **TASK:** Analyze this codebase to build the implementation roadmap for streaming instrumentation.
>
> **DETECTED STACK** (from Gate 0): {paste detection results}
>
> **INSTRUMENTATION MAP** (from Skill #1): `docs/streaming/instrumentation-map.json`
>
> **OUTPUT FILE:** `docs/streaming/_analysis.md`
>
> **REQUIRED SECTIONS:**
>
> ## Bootstrap Path
> - Where is the service bootstrap entry point? (main.go, internal/cmd/, etc.)
> - Where does the `*sql.DB` / `*mongo.Client` get constructed? File:line.
> - Where is `commons.Launcher` built and `launcher.Add` called?
> - Identify the EXACT file:line where:
>   1. A new `internal/bootstrap/streaming.go` file should be created
>   2. The `streaming.NewProducer` constructor will be invoked
>   3. The producer will be registered via `launcher.Add("streaming", producer)`
>
> ## HTTP Router (if applicable)
> - Where is the Fiber/Echo/Gin/net/http router constructed?
> - Where is auth middleware registered?
> - Identify the exact insertion point for `NewStreamingHandler` mount — MUST be AFTER auth.
>
> ## Tenant Context Middleware
> - Cross-check the JSON's `tenant_source` field against actual codebase usage.
> - Flag any drift: if JSON says `tmcore.GetTenantIDContext` but codebase uses `c.Get("X-Tenant")` only, this is a discrepancy that needs resolution.
>
> ## Existing Event-Emission Code
> - For every non-canonical alternative detected at Gate 0 Phase 4, list file:line and the pattern in use.
> - Categorize: replaceable (direct event broadcast → lib-streaming) vs. NOT replaceable (internal command queue → keep using lib-commons/rabbitmq).
>
> ## Outbox Infrastructure (if any event has outbox != "never")
> - Is `lib-commons/v5/commons/outbox` already in go.mod?
> - Is there an outbox table migration already? (search for `outbox` in migration files)
> - Is there a Dispatcher pool registered?
> - Output: NEEDS_INSTALL / NEEDS_WIRING / EXISTING_AND_WIRED
>
> ## Per-Event Site Inspection
> For EVERY event in instrumentation-map.json, for EVERY entry in `instrumentation_sites`:
> - Read the file at `instrumentation_sites[i].file`.
> - Locate the position described by `instrumentation_sites[i].line_anchor` (semantic).
> - Confirm the position exists and matches the description.
> - Note any obstacles: missing context (ctx not in scope), missing tenant_id resolution, etc.
> - Output a per-site readiness verdict: READY / BLOCKED (reason).
>
> ## Risks to Surface in Gate 1.5 Preview
> - Files with > 5 Emit sites (high churn risk in review)
> - Sites where ctx is constructed late (may need refactor to thread ctx through)
> - Sites where DB transaction boundary is unclear (CRITICAL events at risk)
>
> ---
>
> **CONSTRAINTS:**
> - Read whole files. Don't speculate.
> - Quote actual file paths and function names.
> - DO NOT write Go code. Analysis only.
> - Word count: 1500-2500 words.

<block_condition>
HARD GATE: Analysis MUST complete before Gate 1.5. Every event in JSON MUST have a per-site readiness verdict.

HARD GATE: If any site is BLOCKED with no resolution path → STOP and surface to user. Cannot proceed without consensus on how to unblock.
</block_condition>

---

## Gate 1.5: Visual Implementation Preview

**Always executes. Generates HTML via `ring:visualize` skill. User MUST approve before any code changes.**

**Orchestrator generates the preview using `ring:visualize` with this content:**

The HTML page MUST include:

### 1. Current State (Before)

- Mermaid diagram: current event-emission flow (or "NONE — greenfield" if no events emitted today)
- Table of non-canonical alternatives with file:line and patterns to be replaced
- Existing lib-streaming code (if any) and compliance audit results

### 2. Target State (After)

- Mermaid diagram: lib-streaming flow — `NewCatalog → NewProducer → launcher.Add → Emit per site → Manifest endpoint + Outbox (if applicable)`
- Three-step lifecycle explicit: Catalog → Producer construction (auto-Start) → Emit + Manifest
- Tenant flow: `Request → Auth middleware sets ctx → tmcore.GetTenantIDContext → EmitRequest.TenantID`

### 3. Change Map (per gate)

Table with columns: Gate, File, What Changes, Impact, Lines (estimate). One row per file.

Example:

| Gate | File | What Changes | Impact | Lines |
|------|------|--------------|--------|-------|
| 2 | `go.mod` | Add `github.com/LerianStudio/lib-streaming v0.2.0` | Build needs Gates 3-7 to compile | +2 |
| 2 | `internal/messaging/legacy_emitter.go` | DELETE — non-canonical sarama publisher | Removes alternative path | -150 |
| 3 | `internal/bootstrap/streaming.go` | NEW — Catalog construction + Producer bootstrap | Adds new bootstrap file | +120 |
| 4 | `internal/services/transaction/post.go` | Insert `producer.Emit(ctx, EmitRequest{...})` post-commit | One Emit site | +10 |
| 5 | `internal/migrations/20260501_outbox.sql` | NEW — outbox table migration (if Gate 5 active) | Adds DB schema | +25 |
| 6 | `internal/http/router.go` | Mount `NewStreamingHandler` on `/streaming` behind auth | One route group | +8 |
| 7 | `internal/bootstrap/app.go` | Conditional construction + launcher.Add + close-order | Wiring | +25 |
| 8 | `internal/services/transaction/post_test.go` | MockEmitter assertions for `transaction.posted` | Test coverage | +40 |

### 4. Per-File Code Diff Panels

For EVERY file in the change map, generate a before/after diff panel:

- **Before:** exact current code from Gate 1 analysis (or NEW FILE marker)
- **After:** exact code that will be written, using only canonical lib-streaming surface
- Syntax highlighting + line numbers (read `default/skills/visualize/templates/code-diff.html` for patterns)

Example for Gate 3 (bootstrap):

```go
// AFTER: internal/bootstrap/streaming.go (NEW FILE)
package bootstrap

import (
    "context"

    "github.com/LerianStudio/lib-streaming"
    clog "github.com/LerianStudio/lib-commons/v5/commons/log"
    cmetrics "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry/metrics"
    "go.opentelemetry.io/otel/trace"
)

func NewStreaming(
    ctx context.Context,
    cfg streaming.Config,
    logger clog.Logger,
    metricsFactory *cmetrics.MetricsFactory,
    tracer trace.Tracer,
) (streaming.Emitter, error) {
    if !cfg.Enabled {
        return streaming.NewNoopEmitter(), nil
    }

    catalog, err := streaming.NewCatalog(
        streaming.EventDefinition{
            Key:          "transaction.posted",
            ResourceType: "transaction",
            EventType:    "posted",
            SchemaVersion: "1.0.0",
            DataContentType: "application/json",
            Description:  "A transaction has been posted to the ledger and is now visible to the tenant.",
            DefaultPolicy: streaming.DeliveryPolicy{
                Enabled: true,
                Direct:  streaming.DirectSkip,
                Outbox:  streaming.OutboxAlways,
                DLQ:     streaming.DLQOnRoutableFailure,
            },
        },
        // ... one per event from instrumentation-map.json
    )
    if err != nil {
        return nil, err
    }

    return streaming.NewProducer(ctx, cfg,
        streaming.WithLogger(logger),
        streaming.WithMetricsFactory(metricsFactory),
        streaming.WithTracer(tracer),
        streaming.WithCatalog(catalog),
    )
}
```

### 5. Backward Compatibility Analysis

**MANDATORY: Show complete conditional initialization, not just skeleton.**

```go
// internal/bootstrap/app.go — wiring
var emitter streaming.Emitter
if cfg.Streaming.Enabled {
    emitter, err = bootstrap.NewStreaming(ctx, cfg.Streaming, logger, metricsFactory, tracer)
    if err != nil {
        return fmt.Errorf("streaming init: %w", err)
    }
    if producer, ok := emitter.(*streaming.Producer); ok {
        if err := launcher.Add("streaming", producer); err != nil {
            return fmt.Errorf("launcher add streaming: %w", err)
        }
    }
    logger.Info(ctx, "Streaming enabled")
} else {
    emitter = streaming.NewNoopEmitter()
    logger.Info(ctx, "Streaming disabled — events will be no-op")
}

// Inject `emitter` into service constructors via the streaming.Emitter interface.
```

When `STREAMING_ENABLED=false`:
- Emitter is NoopEmitter — every Emit returns nil immediately
- Producer is not constructed — no franz-go connections opened
- Manifest is not mounted (or mounted as 404 stub for path stability — designer's choice; default is "not mounted")
- Outbox dispatcher is not registered

### 6. New Dependencies

| Module | Version | Purpose |
|--------|---------|---------|
| `github.com/LerianStudio/lib-streaming` | {resolved version} | Core producer + catalog + manifest |
| `github.com/LerianStudio/lib-commons/v5/commons/outbox` | (already at v5.x) | Conditional — only if Gate 5 active |
| (test) `github.com/testcontainers/testcontainers-go/modules/redpanda` | latest | Integration tests at Gate 8 |
| (test) `github.com/Shopify/toxiproxy/v2` | latest | Chaos tests at Gate 8 (only if Gate 5 active) |

### 7. Catalog Registry (events to be wired)

Render `instrumentation-map.json` events as a table:

| Posture | Definition Key | Resource | Event | Schema | Sites | Tenant | Outbox | DLQ |
|---------|---------------|----------|-------|--------|-------|--------|--------|-----|
| CRITICAL | transaction.posted | transaction | posted | 1.0.0 | 2 | tmcore | always | on_failure |
| IMPORTANT | account.created | account | created | 1.0.0 | 1 | tmcore | fallback | on_failure |
| OBSERVATIONAL | report.exported | report | exported | 1.0.0 | 1 | tmcore | never | never |

### 8. Risk Assessment

| Risk | Mitigation | Verification |
|------|------------|--------------|
| Compile break from non-canonical removal | Gate 2 removes + Gate 3 adds in same cycle; build runs at end of each gate | `go build ./...` passes |
| Pre-commit emission for CRITICAL events | Gate 4 instrumentation respects `emission_timing=post-commit` from JSON | Code review + integration test |
| Tenant hardcoded in Emit | Gate 4 enforces `tenant_source_at_site` from JSON | Code review + nil-safety reviewer |
| Backward compat regression | Gate 7 backward compat test asserts no behavioral change with flag off | `STREAMING_ENABLED=false go test ./...` passes |
| Outbox migration breaks production schema | Gate 5 generates additive migration; rollback via `DROP TABLE IF EXISTS` | Migration up + down tested |
| Manifest publicly accessible | Gate 6 mounts AFTER auth middleware; integration test asserts 401 without auth | Integration test |
| Producer not closed on shutdown | Gate 7 wires Close() in launcher cleanup | Goroutine-leak test |

### 9. Scope Fence Reminder

This skill instruments lib-streaming for the events validated in Skill #1. It does NOT:

- Add new events not in the JSON
- Change posture or delivery policy from the JSON
- Replace lib-commons/rabbitmq for internal command dispatch
- Replace audit logging
- Replace OTEL telemetry

**Output:** Save the HTML report to `docs/streaming/instrumentation-preview.html`. **Open in browser** for the developer to review.

<block_condition>
HARD GATE: Developer MUST explicitly approve the implementation preview before any code changes begin. This prevents wasted effort on misunderstood requirements, incorrect site selection, or scope creep.
</block_condition>

If the developer requests changes to the preview (site relocation, posture override despite Skill #1 contract, scope expansion), STOP and either:

1. Loop back to Skill #1 if the change affects the catalog/posture (PM territory)
2. Adjust the analysis from Gate 1 if the change is technical (file path, mounting point)

DO NOT silently proceed with developer-side changes that contradict the JSON contract.

---

## Gate 2: lib-streaming Dependency + Non-Canonical Removal

**SKIP only if:** Gate 0 returns `lib-streaming pinned in go.mod` AND Gate 0 Phase 4 returns zero non-canonical findings. Otherwise MANDATORY.

**Dispatch `ring:backend-engineer-golang` with context:**

> {Mandatory Agent Instruction block from skill header}
>
> **TASK:** Add lib-streaming as a pinned dependency AND remove all non-canonical event-emission code.
>
> **NON-CANONICAL FINDINGS** (from Gate 0 Phase 4):
> - N1 (direct franz-go): {file:line list}
> - N2 (sarama): {file:line list}
> - N3 (watermill): {file:line list}
> - N4 (segmentio/kafka-go): {file:line list}
> - N5 (direct CloudEvents): {file:line list}
> - N6 (amqp091.Publish for events): {file:line list}
> - N7 (NATS): {file:line list}
> - N8 (Redis Streams as bus): {file:line list}
> - N9 (legacy env vars): {file list}
>
> **PINNED VERSION:** {resolved lib-streaming tag from Gate 0}
>
> **STEPS** (in order):
>
> 1. `go get github.com/LerianStudio/lib-streaming@{pinned-version}`
> 2. `go mod tidy`
> 3. For each non-canonical finding (N1-N8), remove the file IF its sole purpose was the non-canonical pattern, OR remove the specific function/method if the file has other concerns. DO NOT preserve as commented-out code — DELETE.
> 4. For N9, replace `KAFKA_BROKERS` / `EVENT_BUS_*` env vars with `STREAMING_*` equivalents in `.env.example`, `config/`, and code.
> 5. Distinguish: `lib-commons/v5/commons/rabbitmq` is FINE (internal command dispatch). Only replace direct `amqp091.Publish` patterns used for OUTBOUND BUSINESS EVENTS, not for internal queues.
> 6. Do NOT yet wire the lib-streaming Producer — that is Gate 3. This gate ONLY upgrades dependencies and removes non-canonical code so the build is clean.
> 7. If a deletion leaves stub functions that callers reference, replace those call sites with TODO comments referencing Gate 4 (where Emit calls will land). Avoid leaving unbuildable callers.
>
> **VERIFICATION REQUIRED:**
> - `go build ./...` MUST pass after the gate
> - `go test ./...` MUST pass (tests relying on the removed non-canonical code MAY need to be deleted; record which in dispatch output)

**Verification commands (orchestrator runs):**

- `grep "lib-streaming" go.mod` — MUST return a pinned version
- `grep -rn "Shopify/sarama\|IBM/sarama\|ThreeDotsLabs/watermill\|segmentio/kafka-go" go.mod internal/` — MUST return zero results
- `grep -rn "twmb/franz-go" internal/ | grep -v "lib-streaming"` — MUST return zero results
- `grep "KAFKA_BROKERS\|EVENT_BUS_" .env.example config/` — MUST return zero results (replaced with STREAMING_*)
- `go build ./...` — MUST pass
- `go test ./...` — MUST pass

<block_condition>
HARD GATE: Zero non-canonical residue. lib-streaming pinned in go.mod. Build and tests green. CANNOT proceed until all hold.
</block_condition>

---

## Gate 3: Catalog Construction + Producer Bootstrap

**Always executes.** If Gate 0 Phase 3 audit found existing lib-streaming code that's compliant on S1-S4, this gate VERIFIES the catalog matches `instrumentation-map.json` exactly. Drift MUST be fixed.

**Dispatch `ring:backend-engineer-golang` with context:**

> {Mandatory Agent Instruction block}
>
> **TASK:** Construct the streaming Catalog from `docs/streaming/instrumentation-map.json` and the Producer bootstrap. Create new file `internal/bootstrap/streaming.go`.
>
> **JSON CONTRACT:** `docs/streaming/instrumentation-map.json` is the canonical input. Build EventDefinition for EVERY event. NO additions, NO omissions.
>
> **DETECTED CONTEXT** (from Gate 1):
> - Bootstrap path: {file:line}
> - DB handle construction: {file:line}
> - launcher.Add insertion point: {file:line}
> - Logger / metricsFactory / tracer construction: {file:line}
>
> **CANONICAL API:**
>
> ```go
> // Catalog
> func NewCatalog(definitions ...streaming.EventDefinition) (streaming.Catalog, error)
>
> type EventDefinition struct {
>     Key, ResourceType, EventType, SchemaVersion string
>     DataContentType, DataSchema                 string
>     SystemEvent                                 bool
>     Description                                 string
>     DefaultPolicy                               streaming.DeliveryPolicy
> }
>
> // Producer
> func NewProducer(ctx context.Context, cfg streaming.Config, opts ...streaming.EmitterOption) (*streaming.Producer, error)
>
> // Required options
> streaming.WithLogger(clog.Logger)
> streaming.WithMetricsFactory(*cmetrics.MetricsFactory)
> streaming.WithTracer(trace.Tracer)
> streaming.WithCatalog(streaming.Catalog)
>
> // Optional: PII redaction (only if any event's payload_sketch has fields suffixed " (PII)")
> // Note: lib-streaming does NOT have a per-event WithRedaction at v0.2.0 — payload-level
> // redaction is the catalog author's responsibility. If JSON has PII annotations, the agent
> // MUST construct payloads such that PII fields are excluded or hashed BEFORE building
> // EmitRequest.Payload. Add a helper function alongside the bootstrap.
> ```
>
> **CONSTRAINTS:**
>
> 1. MUST use the canonical import paths from the skill's table.
> 2. MUST construct the Catalog with EVERY event from the JSON, in the same order.
> 3. MUST set DefaultPolicy from `delivery_policy` in JSON exactly:
>    - CRITICAL → `{Enabled: true, Direct: DirectSkip, Outbox: OutboxAlways, DLQ: DLQOnRoutableFailure}`
>    - IMPORTANT → `{Enabled: true, Direct: DirectDirect, Outbox: OutboxFallbackOnCircuitOpen, DLQ: DLQOnRoutableFailure}`
>    - OBSERVATIONAL → `{Enabled: true, Direct: DirectDirect, Outbox: OutboxNever, DLQ: DLQNever}`
>    - CUSTOM → use exact policy from JSON
> 4. MUST NOT call Producer.Emit in this gate — Emit insertion is Gate 4.
> 5. MUST NOT register with launcher — wiring is Gate 7.
> 6. Constructor signature: `NewStreaming(ctx, cfg, logger, metricsFactory, tracer) (streaming.Emitter, error)`
> 7. When `cfg.Enabled == false`, return `streaming.NewNoopEmitter()` immediately. Producer construction only when enabled.
> 8. DO NOT set `WithOutboxRepository` here — outbox wiring is Gate 5.
> 9. DO NOT mount manifest here — that is Gate 6.
> 10. Add `runtime.InitPanicMetrics(metricsFactory)` and `assert.InitAssertionMetrics(metricsFactory)` calls at the bootstrap entry point (per `doc.go:30-35`). If they're already there, leave them.
>
> **TDD:**
> - Write `TestNewStreaming_DisabledReturnsNoop` first (RED): assert that `cfg.Enabled=false` returns NoopEmitter
> - Write `TestNewStreaming_EnabledConstructsProducer` (RED): assert that `cfg.Enabled=true` returns *streaming.Producer (use a test broker via testcontainers Redpanda OR streamingtest.MockEmitter for the assertion)
> - Implement to make both pass

**Verification commands:**

- `grep "streaming.NewProducer" internal/bootstrap/streaming.go` — MUST return one constructor call
- `grep -c "streaming.EventDefinition{" internal/bootstrap/streaming.go` — count MUST equal events count from instrumentation-map.json
- `grep "streaming.WithCatalog\|streaming.WithLogger\|streaming.WithMetricsFactory\|streaming.WithTracer" internal/bootstrap/streaming.go` — MUST return all four
- `grep "streaming.NewNoopEmitter" internal/bootstrap/streaming.go` — MUST return at least one call (the disabled path)
- `go build ./...` — MUST pass
- `go test ./bootstrap/... -run TestNewStreaming` — MUST pass

<block_condition>
HARD GATE: All events from JSON MUST be in the catalog. Required options (Logger, MetricsFactory, Tracer, Catalog) MUST be passed. NoopEmitter path MUST exist for disabled flag.
</block_condition>

---

## Gate 4: Emit Instrumentation per Eventable Point

**Always executes. This is the heart of the skill — the only gate that touches business-logic files.**

**Dispatch `ring:backend-engineer-golang` with context:**

> {Mandatory Agent Instruction block}
>
> **TASK:** Insert `producer.Emit(ctx, EmitRequest{...})` calls at every site listed in `docs/streaming/instrumentation-map.json`. ONE site at a time, with TDD.
>
> **JSON CONTRACT:** Every `events[i].instrumentation_sites[j]` is a required Emit insertion. NO additions, NO omissions.
>
> **DETECTED CONTEXT** (from Gate 1): Per-site readiness verdicts. {paste relevant per-site details}
>
> **CANONICAL EMIT PATTERN:**
>
> ```go
> // After durable persistence, before HTTP response
> if err := emitter.Emit(ctx, streaming.EmitRequest{
>     DefinitionKey: "transaction.posted",
>     TenantID:      tmcore.GetTenantIDContext(ctx),
>     Subject:       transactionID.String(),
>     Payload:       payloadBytes, // raw JSON bytes
> }); err != nil {
>     // Strategy depends on posture:
>     // CRITICAL events: log error; do NOT fail the request (outbox will retry)
>     // IMPORTANT events: log warning; do NOT fail the request
>     // OBSERVATIONAL events: log debug; do NOT fail the request
>     logger.Log(ctx, log.LevelWarn, "streaming emit failed",
>         log.String("definition_key", "transaction.posted"),
>         log.Err(err))
> }
> ```
>
> **PER-SITE WORKFLOW** (apply for EVERY site):
>
> 1. Read `events[i].instrumentation_sites[j].file`.
> 2. Locate the position described by `line_anchor` (semantic).
> 3. Verify `emission_timing` matches the JSON:
>    - `post-commit`: AFTER repository Save returns nil, BEFORE function returns / HTTP response. Critical for atomicity.
>    - `pre-respond`: BEFORE HTTP response (typically same as post-commit but explicit about respond timing).
>    - `end-of-saga-step`: at the saga step transition that completes a business outcome.
>    - `post-cron-tick`: at the end of a cron iteration that produced a durable outcome.
> 4. Insert the Emit call:
>    - `DefinitionKey`: from JSON
>    - `TenantID`: from `tenant_source_at_site` in JSON (typically `tmcore.GetTenantIDContext(ctx)`). MUST NOT hardcode. MUST NOT default to empty.
>    - `Subject`: aggregate ID (the entity that just changed) — typically the primary key of the persisted row. Pull from local scope at the site.
>    - `EventID`: leave empty; lib-streaming generates a UUIDv7 in `ApplyDefaults()`.
>    - `Timestamp`: leave zero; lib-streaming sets `time.Now().UTC()`.
>    - `Payload`: build a struct matching `payload_sketch` from JSON, json.Marshal it, pass as json.RawMessage.
> 5. Build the payload struct:
>    - Use field names matching `payload_sketch` keys.
>    - Use Go types matching the type tags (`uuid` → `uuid.UUID`, `decimal` → `decimal.Decimal`, etc.)
>    - PII fields (suffix " (PII)" in JSON): EXCLUDE from payload OR hash. NEVER include raw.
> 6. Failure handling per posture:
>    - CRITICAL: Emit error logs at WARN; outbox eventually retries; the request succeeds (DB row exists)
>    - IMPORTANT: Emit error logs at WARN; circuit-breaker fallback engages
>    - OBSERVATIONAL: Emit error logs at DEBUG; loss is acceptable
>    - In NO case does an Emit failure rollback the DB transaction or return HTTP 5xx
>
> **TDD per site:**
> - Write a unit test using `streamingtest.MockEmitter`:
>   ```go
>   mock := streamingtest.NewMockEmitter()
>   svc := NewTransactionService(repo, mock)
>   svc.Post(ctx, transactionInput)
>   streamingtest.AssertEventEmitted(t, mock, "transaction.posted")
>   streamingtest.AssertTenantID(t, mock, "test-tenant")
>   ```
> - The test fails (RED) before Emit insertion.
> - Insert the Emit call (GREEN).
> - Refactor for clarity (REFACTOR) — extract payload-building helper if shared across sites.
>
> **CONSTRAINTS:**
>
> 1. Service constructors MUST take `streaming.Emitter` (interface), NOT `*streaming.Producer` (concrete).
> 2. Inject the emitter via dependency injection at bootstrap; do NOT use a package-level global.
> 3. Verify ctx is in scope at the emission point. If not, refactor to thread ctx through (this may require Gate 1 to flag it as a BLOCKED site for resolution).
> 4. ONE Emit call per site. Multiple sites for the same event = multiple Emit calls in different files.
> 5. NEVER call Emit inside a database transaction's open scope (would block on broker for CRITICAL outbox path; defeats atomicity for direct-mode events). Emit goes AFTER the transaction commits.
> 6. NEVER use `time.Sleep` or other delays around Emit — the producer manages its own batching.

**Verification commands:**

- For each event in JSON: `grep -rn "DefinitionKey:.*\"{event.definition_key}\"" internal/` — MUST return number of sites matching `len(instrumentation_sites)`
- `grep -rn "TenantID:.*\"\"" internal/` near Emit calls — MUST return zero (no empty tenant)
- `grep -rn "TenantID:.*GetTenantID\|TenantID:.*tmcore" internal/` near Emit calls — MUST return non-zero (canonical tenant source)
- `go build ./...` — MUST pass
- `go test ./... -run TestEmit` — MUST pass (per-site MockEmitter unit tests)
- `go test ./... -race` — MUST pass

<block_condition>
HARD GATE: Every site from JSON MUST have an Emit call. Every Emit MUST resolve TenantID from canonical source. Pre-commit Emits for CRITICAL events are FORBIDDEN.
</block_condition>

### Gate 4 Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Emit before DB commit is fine, the outbox handles atomicity" | Outbox stores the event in the SAME transaction as the DB write — but Emit pre-commit calls outbox without a transaction context. | **MUST emit post-commit; outbox sees the event AFTER the row exists** |
| "Hardcode tenant for clarity" | Hardcoded tenant breaks multi-tenancy. | **MUST resolve from ctx every call** |
| "Skip the test, the Emit is trivial" | MockEmitter test catches DefinitionKey typos, payload misses, tenant misses. | **MUST write MockEmitter test per site** |
| "Include the user's email in payload, consumer needs it" | PII in payload + RedactNone leaks to all consumers. | **EXCLUDE or hash PII fields** |
| "Wrap Emit in retry loop" | lib-streaming has its own retry policy. Manual retries = double-publish. | **DO NOT add manual retry; trust the library** |

---

## Gate 5: Outbox Wiring (Conditional)

**SKIP only if:** Gate 0 Phase 1 confirms `summary.events_critical == 0` AND every event in JSON has `delivery_policy.outbox == "never"`. Otherwise MANDATORY.

**Two scenarios:**

### Scenario A: lib-commons/outbox already in service

If Gate 0 detected `lib-commons/v5/commons/outbox` in go.mod with existing Dispatcher registration, this gate ONLY wires the producer to it.

### Scenario B: lib-commons/outbox missing

If Gate 0 found NO outbox infra, this gate INSTALLS it: dependency, migration, repository instance, dispatcher pool, registration.

**Dispatch `ring:backend-engineer-golang` with context:**

> {Mandatory Agent Instruction block}
>
> **TASK:** Wire the streaming Producer's outbox path. Scenario: {A_existing | B_install}.
>
> **EVENTS REQUIRING OUTBOX** (from JSON): {list events with `delivery_policy.outbox != "never"`}
>
> **DETECTED CONTEXT** (from Gate 1):
> - Outbox infra status: {NEEDS_INSTALL | NEEDS_WIRING | EXISTING_AND_WIRED}
> - DB handle: {*sql.DB or *mongo.Client}
> - Existing migration directory: {path}
>
> **SCENARIO A — wiring existing outbox:**
>
> 1. Construct an `outbox.OutboxRepository` instance backed by the existing infrastructure.
> 2. Pass to producer via `streaming.WithOutboxRepository(repo)` in bootstrap (Gate 3 file).
> 3. Register the streaming relay handler with the existing Dispatcher pool:
>    ```go
>    if err := producer.RegisterOutboxRelay(outboxRegistry); err != nil {
>        return fmt.Errorf("register outbox relay: %w", err)
>    }
>    ```
> 4. Verify the dispatcher poll interval is set sensibly (typically 1-5 seconds).
>
> **SCENARIO B — installing outbox:**
>
> 1. Add dependency: `go get github.com/LerianStudio/lib-commons/v5/commons/outbox` (already at v5).
> 2. Generate migration `internal/migrations/{date}_outbox_streaming.sql`:
>    - Postgres: per `lib-commons/outbox` schema spec
>    - Mongo: collection initialization + indexes
> 3. Construct `outbox.OutboxRepository` (sql or mongo flavor) at bootstrap.
> 4. Construct an `outbox.HandlerRegistry` and a `Dispatcher` pool. Register with `commons.Launcher` so it runs alongside the producer.
> 5. Pass `WithOutboxRepository(repo)` to the producer.
> 6. Call `producer.RegisterOutboxRelay(registry)` AFTER producer construction, BEFORE launcher.Add.
> 7. Update `.env.reference` with any outbox-specific env vars.
>
> **MIGRATION CONSTRAINTS:**
> - MUST be additive (no DROP / ALTER on existing tables).
> - MUST include both up and down migrations.
> - MUST be idempotent (CREATE TABLE IF NOT EXISTS / index variants).
> - MUST be tested via the project's existing migration runner.
>
> **TDD:**
> - Write `TestOutboxFallback_OnCircuitOpen` (RED): assert that when broker is unavailable AND policy is `outbox: fallback_on_circuit_open`, the event is persisted to outbox and Emit returns nil.
> - Use Toxiproxy or a fake circuit-breaker to simulate broker outage.
> - Implement (GREEN).
> - Refactor (REFACTOR).

**Verification commands:**

- `grep "streaming.WithOutboxRepository" internal/bootstrap/streaming.go` — MUST return one match (Scenario A or B)
- `grep "producer.RegisterOutboxRelay" internal/bootstrap/` — MUST return one match
- For Scenario B: migration file exists in `internal/migrations/`
- For Scenario B: `outbox.NewOutboxRepository\|outbox.NewSQLRepository\|outbox.NewMongoRepository` constructed
- `go test ./... -run TestOutbox -race` — MUST pass

<block_condition>
HARD GATE: If any event has `outbox != "never"` AND outbox is not wired → CANNOT proceed. CRITICAL events would silently drop on broker failure.
</block_condition>

---

## Gate 6: Manifest HTTP Mount (Conditional)

**SKIP only if:** Gate 0 returns `HTTP framework: NONE` AND `gRPC: NO` (pure background worker). MUST surface justification in final report. Otherwise MANDATORY.

**Dispatch `ring:backend-engineer-golang` with context:**

> {Mandatory Agent Instruction block}
>
> **TASK:** Mount `streaming.NewStreamingHandler(descriptor, catalog)` on the service's existing HTTP router, AFTER authentication middleware.
>
> **DETECTED CONTEXT** (from Gate 1):
> - HTTP framework: {Fiber | Echo | Gin | net/http}
> - Router construction: {file:line}
> - Auth middleware registration: {file:line}
>
> **CANONICAL API:**
>
> ```go
> // Construct PublisherDescriptor (identifies this producer in the manifest):
> descriptor := streaming.PublisherDescriptor{
>     ServiceName: cfg.ServiceName,
>     Version:     buildVersion,
>     // ... other fields per doc.go
> }
>
> handler, err := streaming.NewStreamingHandler(descriptor, catalog)
> if err != nil {
>     return fmt.Errorf("streaming handler: %w", err)
> }
>
> // Mount on Fiber (using fiberadaptor):
> app.Group("/streaming", authMiddleware).
>     All("*", adaptor.HTTPHandler(handler))
> ```
>
> **CONSTRAINTS:**
>
> 1. MUST mount under a path prefix (`/streaming` or `/admin/streaming`) — NOT on root.
> 2. MUST mount AFTER auth middleware. Authenticated principal is in `c.Locals(...)` for the handler.
> 3. MUST NOT expose on a public-facing port without ACLs/VPN. Operator doc (Gate 11) must call this out.
> 4. The handler is read-only (manifest export). It does NOT mutate state. Authentication is sufficient; no special authorization layer needed beyond service-level auth.
> 5. Manually document the route in the service's existing OpenAPI spec (lib-streaming has no auto-swagger).
>
> **TDD:**
> - Write `TestStreamingManifest_RequiresAuth` (RED): unauthenticated GET /streaming → 401
> - Write `TestStreamingManifest_AuthenticatedReturnsCatalog` (RED): authenticated GET /streaming → 200 with catalog JSON
> - Implement (GREEN).
> - Refactor (REFACTOR).

**Verification commands:**

- `grep "streaming.NewStreamingHandler" internal/` — MUST return one match
- `grep "Group.*streaming\|Mount.*streaming" internal/http/` — MUST be paired with auth middleware
- Integration test: unauthenticated GET → 401; authenticated GET → 200
- `go build ./...` — MUST pass

### Gate 6 Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Manifest is just metadata, no auth needed" | Manifest reveals the event taxonomy, which may inform attackers about internal models. Auth aligns with rest of admin surface. | **MUST mount behind auth** |
| "Skip path prefix, mount on /" | Root mount collides with public API. Path prefix enables network-policy separation. | **MUST use `/streaming` prefix** |

<block_condition>
HARD GATE: Manifest mounted without auth = information disclosure. MUST be paired with existing auth middleware.
</block_condition>

---

## Gate 7: Wiring + Lifecycle + Backward Compat ⛔ NEVER SKIPPABLE

**Always executes. This gate cannot be skipped under any circumstance.**

This is where everything connects: feature flag, conditional construction, launcher.Add, graceful shutdown, and the backward-compat path.

**Dispatch `ring:backend-engineer-golang` with context:**

> {Mandatory Agent Instruction block}
>
> **TASK:** Wire the streaming emitter into the service's bootstrap and shutdown, add the `STREAMING_ENABLED` feature flag, and validate backward compatibility.
>
> **DETECTED CONTEXT** (from Gate 1): {bootstrap path, existing shutdown handler, launcher.Add file:line}
>
> **REQUIRED CHANGES:**
>
> 1. **Feature flag** — add to Config struct:
>    ```go
>    type StreamingConfig struct {
>        Enabled    bool     `env:"STREAMING_ENABLED" default:"false"`
>        Brokers    []string `env:"STREAMING_BROKERS"`
>        ClientID   string   `env:"STREAMING_CLIENT_ID"`
>        // ... other STREAMING_* fields per .env.reference
>    }
>    ```
>
> 2. **Conditional construction in bootstrap:**
>    ```go
>    var emitter streaming.Emitter
>    if cfg.Streaming.Enabled {
>        e, err := bootstrap.NewStreaming(ctx, cfg.Streaming, logger, metricsFactory, tracer)
>        if err != nil {
>            return fmt.Errorf("streaming init: %w", err)
>        }
>        emitter = e
>        if producer, ok := e.(*streaming.Producer); ok {
>            if err := launcher.Add("streaming", producer); err != nil {
>                return fmt.Errorf("launcher add streaming: %w", err)
>            }
>        }
>        logger.Info(ctx, "Streaming enabled")
>    } else {
>        emitter = streaming.NewNoopEmitter()
>        logger.Info(ctx, "Streaming disabled — events will be no-op")
>    }
>    ```
>
> 3. **Inject emitter** into service constructors via the `streaming.Emitter` interface (NOT `*Producer`).
>
> 4. **Lifecycle**:
>    - Producer construction opens connections (per `doc.go:lifecycle`); no separate Start required.
>    - On shutdown, `producer.Close()` is called by the launcher's cleanup — verify launcher.Add ordering: streaming MUST be added BEFORE the DB/HTTP launchers, so streaming closes BEFORE them on shutdown.
>    - Close is idempotent and drains via `STREAMING_CLOSE_TIMEOUT_S`.
>    - MUST handle nil producer in shutdown path (when feature flag is off).
>
> 5. **Conditional manifest mount** (if Gate 6 ran):
>    ```go
>    if producer, ok := emitter.(*streaming.Producer); ok {
>        // mount manifest only when real producer is constructed
>    }
>    ```
>
> 6. **Backward compatibility guarantees** when `STREAMING_ENABLED=false`:
>    - Emitter is NoopEmitter — every Emit returns nil
>    - No franz-go connections opened
>    - No outbox dispatcher registered
>    - Manifest endpoint returns 404 (not mounted)
>    - `go test ./...` passes with zero changes to existing tests
>
> 7. **Write TestStreaming_BackwardCompatibility:**
>    - Start service with `STREAMING_ENABLED=false`
>    - Issue requests; assert no events emitted (use streamingtest.MockEmitter assertion if injected, OR assert via behavior)
>    - Assert manifest endpoint returns 404 (not mounted)
>
> 8. **Write TestStreaming_EnabledRoundtrip:**
>    - Start service with `STREAMING_ENABLED=true`, real or testcontainers Redpanda
>    - Issue a request that triggers Emit
>    - Wait for the event on the broker (use `kfake` or testcontainers Redpanda subscriber)
>    - Assert event has correct DefinitionKey, TenantID, Payload
>    - Assert outbox flow if event has `outbox != never`
>
> **CONSTRAINTS:**
>
> 1. MUST preserve existing startup ordering: streaming construction AFTER lib-commons logger / metrics / tracer init, BEFORE HTTP server.
> 2. MUST NOT block startup on streaming availability unless feature flag is on AND service cannot operate without live emission.
> 3. Close order: producer.Close → DB close. Reversing causes franz-go panics on background goroutines accessing closed DB pools.
>
> **TDD:**
> - Write all four tests first (RED)
> - Implement wiring (GREEN)
> - Refactor (REFACTOR)

**Verification commands:**

- `grep "STREAMING_ENABLED\|StreamingEnabled" internal/ config/` — MUST return results
- `grep "streaming.NewNoopEmitter" internal/bootstrap/` — MUST appear in disabled branch
- `grep "launcher.Add.*streaming\|launcher.Add.*producer" internal/` — MUST appear in enabled branch
- `STREAMING_ENABLED=false go test ./...` — MUST pass
- `STREAMING_ENABLED=true go test ./...` — MUST pass (with broker available or kfake)
- `TestStreaming_BackwardCompatibility` MUST exist and pass
- `TestStreaming_EnabledRoundtrip` MUST exist and pass

<block_condition>
HARD GATE: Backward compat tests MUST pass. Feature-flag-off path MUST be behaviorally identical to pre-instrumentation service. No exceptions.
</block_condition>

---

## Gate 8: Tests

**Always executes.**

**Dispatch `ring:backend-engineer-golang` with context:**

> {Mandatory Agent Instruction block}
>
> **TASK:** Write comprehensive tests for the streaming integration.
>
> **REQUIRED TEST LAYERS:**
>
> 1. **MockEmitter unit tests per Emit site (most coverage):**
>    - For every Emit site, a unit test using `streamingtest.NewMockEmitter()`.
>    - Assert: DefinitionKey, TenantID, Subject, payload structure.
>    - Use `streamingtest.AssertEventEmitted`, `AssertTenantID`, `AssertEventCount` helpers.
>    - Negative tests: when service rejects a request (validation error), NO event is emitted.
>
> 2. **Catalog validation tests:**
>    - Test that `bootstrap.NewStreaming` constructs a Catalog matching `instrumentation-map.json`.
>    - Test that catalog has every event from JSON; no extras.
>
> 3. **OnChange / Emit failure handling tests:**
>    - Test that an Emit error does NOT propagate as an HTTP 5xx (failure modes per posture).
>    - For CRITICAL events: assert log line + outbox writes the event.
>    - For OBSERVATIONAL events: assert log line at DEBUG; nothing else.
>
> 4. **Manifest HTTP tests (if Gate 6 ran):**
>    - Unauthenticated GET → 401
>    - Authenticated GET → 200 with catalog JSON
>    - Catalog JSON matches `instrumentation-map.json` event count
>
> 5. **Backward compat tests (from Gate 7 — re-verified):**
>    - `STREAMING_ENABLED=false` path matches pre-instrumentation baseline
>
> 6. **Integration tests (testcontainers Redpanda):**
>    - Spin up Redpanda v24.2.x via `testcontainers-go/modules/redpanda`
>    - Real Producer.Emit, real Kafka broker, real franz-go consumer in test
>    - Assert: event received with correct CloudEvents headers, correct partition key (tenant_id), correct payload
>    - Pin Redpanda image version per `doc.go` recommendation
>
> 7. **Chaos tests (only if Gate 5 active — outbox wired):**
>    - Use Toxiproxy to simulate broker outage
>    - For an event with `outbox=fallback_on_circuit_open`, assert event lands in outbox table
>    - Restore broker; assert relay drains outbox to broker
>
> 8. **Goroutine leak tests:**
>    - Use `go.uber.org/goleak` (already in deps if lib-streaming testing patterns are followed)
>    - Wrap test main with `goleak.VerifyTestMain`
>
> **CONSTRAINTS:**
>
> 1. Coverage on `internal/bootstrap/streaming.go` and Emit-site files MUST be >= 85%.
> 2. `go test ./... -race` MUST pass — no data races.
> 3. Integration tests MUST be marked with build tag `integration` so unit-test runs are fast.
> 4. Chaos tests with build tag `chaos` — only run when explicitly requested.

**Verification commands:**

- `go test ./... -v -count=1` — MUST pass
- `go test ./... -cover` — coverage on streaming files MUST be >= 85%
- `go test ./... -race` — MUST pass
- `go test -tags integration ./...` — MUST pass (with broker available)
- `go test -tags chaos ./...` — MUST pass (if Gate 5 active)
- `grep "streamingtest.AssertEventEmitted\|streamingtest.NewMockEmitter" internal/` — MUST return one per Emit site

---

## Gate 9: Code Review

**Dispatch 10 parallel reviewers (same pattern as ring:codereview).**

MUST include this context in ALL 10 reviewer dispatches:

> **STREAMING INSTRUMENTATION REVIEW CONTEXT:**
>
> - Service is adopting lib-streaming for outbound business event emission.
> - lib-streaming is producer-only, write-only, Kafka/Redpanda backend, CloudEvents 1.0 binary mode.
> - Three named delivery postures: CRITICAL (atomic via outbox), IMPORTANT (resilient with fallback), OBSERVATIONAL (best-effort). CUSTOM with rationale ≥80 chars.
> - Catalog is registered at bootstrap and immutable. Emit calls with unregistered keys fail fast.
> - Tenant identity flows from `tmcore.GetTenantIDContext(ctx)` (or as specified in `instrumentation-map.json`).
> - Topics are SHARED across tenants — consumer-side tenant filter is OPERATIONAL responsibility (called out in Gate 11 activation guide).
> - Pre-commit Emits for CRITICAL events are FORBIDDEN — break atomicity.
> - Backward compatibility required: `STREAMING_ENABLED=false` MUST behave identically to pre-instrumentation.
> - Manifest mount without auth = information disclosure (CRITICAL).
> - PII fields (suffix " (PII)" in JSON) MUST be excluded or hashed before payload construction.

| Reviewer | Focus |
|----------|-------|
| ring:code-reviewer | Architecture, lifecycle ordering (Catalog → Producer → launcher.Add; Close → DB close), API correctness |
| ring:business-logic-reviewer | Catalog matches instrumentation-map.json exactly; no scope-fence violations; postures honored |
| ring:security-reviewer | Manifest auth, PII redaction in payloads, no credential leakage in logs, tenant isolation |
| ring:test-reviewer | MockEmitter coverage per Emit site; backward compat tests; integration via testcontainers Redpanda; chaos tests (if Gate 5); goroutine leak |
| ring:nil-safety-reviewer | NoopEmitter branch (sp == nil); type assertion safety on emitter.(*Producer); ctx propagation to Emit |
| ring:consequences-reviewer | Impact on `STREAMING_ENABLED=false` path, startup/shutdown ordering, upstream/downstream services unaffected, consumer-side tenant filter operational note |
| ring:dead-code-reviewer | Non-canonical event-emission code removed (sarama, watermill, segmentio, raw franz-go, amqp091.Publish for events) |
| ring:performance-reviewer | Emit hot-path is non-blocking; payload construction not allocating per request unnecessarily; broker batching configured sensibly |
| ring:multi-tenant-reviewer | TenantID from canonical source; partition key drives tenant routing; no cross-tenant leakage; payload doesn't leak cross-tenant data |
| ring:lib-commons-reviewer | Correct usage of lib-commons/v5 logger, metrics, outbox; canonical import paths; runtime.InitPanicMetrics + assert.InitAssertionMetrics called once |

MUST pass all 10 reviewers. Critical findings → fix and re-review.

---

## Gate 10: User Validation

MUST approve: present checklist for explicit user approval.

```markdown
## Streaming Instrumentation Complete

- [ ] lib-streaming pinned in go.mod ({version})
- [ ] Zero non-canonical event-emission code (sarama, watermill, segmentio, raw franz-go, amqp091.Publish for events)
- [ ] Catalog matches instrumentation-map.json exactly ({N} events)
- [ ] Producer constructed with WithCatalog + WithLogger + WithMetricsFactory + WithTracer
- [ ] Every Emit site from JSON has an Emit call ({M} sites)
- [ ] Tenant from canonical source (tmcore.GetTenantIDContext or per JSON)
- [ ] Pre-commit Emits for CRITICAL events: NONE
- [ ] PII fields excluded or hashed
- [ ] Outbox wired for events with outbox != never (or skipped with justification: zero such events)
- [ ] Manifest mounted behind auth (or skipped with justification: no HTTP surface)
- [ ] STREAMING_ENABLED feature flag (default false)
- [ ] NoopEmitter for disabled path
- [ ] launcher.Add for lifecycle; Close before DB close
- [ ] Backward compat test passes with STREAMING_ENABLED=false
- [ ] Enabled roundtrip test passes (testcontainers Redpanda or kfake)
- [ ] MockEmitter unit tests per Emit site
- [ ] Chaos tests pass (if outbox wired)
- [ ] Goroutine leak: clean
- [ ] 10 reviewers passed
```

---

## Gate 11: Activation Guide

**MUST generate `docs/streaming-guide.md` in the project root.** Direct, concise, no filler.

Built from Gate 0 (stack), Gate 1 (analysis), Gate 4 (Emit sites), and the validated `instrumentation-map.json`.

The guide MUST include:

1. **Overview**: what lib-streaming does in this service (one paragraph, scope fence explicit)
2. **Backend**: Kafka / Redpanda — operator must provide brokers, topics auto-created or pre-created policy
3. **Required environment variables**:
   - `STREAMING_ENABLED` (bool, default `false`) — master kill switch
   - `STREAMING_BROKERS` (csv) — bootstrap brokers
   - `STREAMING_CLIENT_ID` (string) — franz-go client.id
   - `STREAMING_CLOUDEVENTS_SOURCE` (string, REQUIRED when enabled) — `ce-source` value
   - `STREAMING_COMPRESSION` (default `lz4`)
   - `STREAMING_REQUIRED_ACKS` (default `all`)
   - Optional: `STREAMING_BATCH_LINGER_MS`, `STREAMING_BATCH_MAX_BYTES`, `STREAMING_MAX_BUFFERED_RECORDS`, `STREAMING_RECORD_RETRIES`, `STREAMING_RECORD_DELIVERY_TIMEOUT_S`, `STREAMING_CB_FAILURE_RATIO`, `STREAMING_CB_MIN_REQUESTS`, `STREAMING_CB_TIMEOUT_S`, `STREAMING_CLOSE_TIMEOUT_S`, `STREAMING_EVENT_POLICIES`
4. **Catalog**: render the events table from instrumentation-map.json with posture and topic name
5. **Topic provisioning**: lib-streaming does NOT auto-create topics. Operator MUST pre-create:
   - For every event: topic `lerian.streaming.<resource>.<event>[.vN]`
   - For DLQ-routable events: topic `<service>.dlq` (per producer; check JSON for unique sources)
6. **How to activate**:
   - Set `STREAMING_ENABLED=true` and `STREAMING_BROKERS=...` and `STREAMING_CLOUDEVENTS_SOURCE=...`
   - Pre-create topics (item 5)
   - Restart the service
7. **How to verify**:
   - Startup logs show `Streaming enabled`
   - GET `/streaming` (authenticated) returns the catalog manifest
   - Trigger a known event-emitting flow; consume from broker (kafkactl, kcat, or rpk) and verify payload
8. **How to deactivate**:
   - Set `STREAMING_ENABLED=false` and restart
   - Service reverts to NoopEmitter; behavior identical to pre-instrumentation
9. **Operational notes**:
   - Topics are SHARED across tenants. Partition key = tenant_id.
   - Default `STREAMING_BATCH_LINGER_MS=5` — sub-second propagation; tune for throughput if needed
   - Outbox (if wired): events for CRITICAL posture flow through outbox table on broker outage; relay drains automatically
   - Default authorizer for manifest is service-level auth — review your auth middleware
10. **⛔ MANDATORY CONSUMER-SIDE TENANT FILTER**:
    > **EVERY consumer of these topics MUST filter events by `ce-tenantid` header before processing.** Topics are shared across tenants. A consumer that processes an event without tenant verification has a CROSS-TENANT DATA LEAK. lib-streaming enforces tenant on the producer side (via partition key), but tenant isolation on the consumer side is the consumer's operational responsibility. This is NOT optional.
11. **Scope fence reminder**: what does NOT go in lib-streaming — internal commands (rabbitmq), audit logs, cache invalidations, saga internal state, sync responses, health signals
12. **Common errors**:
    - `streaming init: catalog: duplicate (resource, event, version)` → instrumentation-map.json has duplicates; fix at Skill #1 level
    - `streaming emit: unknown definition key` → service code has Emit with key not in catalog; check JSON drift
    - `streaming health: degraded` → broker unreachable; outbox is buffering; check broker health
    - `streaming health: down` → broker unreachable AND no outbox configured; events ARE being lost; URGENT
    - `manifest 401` on dashboards → authorization middleware rejecting; fix authorizer
    - Goroutine leak after restart → producer.Close() not called before DB close; fix launcher.Add ordering

---

## State Persistence

Save to `docs/streaming/_instrumentation-state.json` for resume support:

```json
{
  "skill": "dev-streaming-instrumentation",
  "lib_streaming_version": "v0.2.0",
  "service_name": "ledger-api",
  "instrumentation_map_path": "docs/streaming/instrumentation-map.json",
  "events_total": 14,
  "emit_sites_total": 18,
  "outbox_required": true,
  "outbox_install_needed": false,
  "manifest_required": true,
  "non_canonical_files_to_remove": 3,
  "gates": {
    "0": "PASS",
    "1": "PASS",
    "1.5": "PASS",
    "2": "PASS",
    "3": "PASS",
    "4": "IN_PROGRESS",
    "5": "PENDING",
    "6": "PENDING",
    "7": "PENDING",
    "8": "PENDING",
    "9": "PENDING",
    "10": "PENDING",
    "11": "PENDING"
  },
  "current_gate": 4
}
```

---

## Output Format (final orchestrator report)

After all gates pass, emit:

```markdown
## Streaming Instrumentation Summary

- Service: {service_name}
- lib-streaming version: {version}
- Events wired: {events_wired}
- Emit sites inserted: {emit_sites_inserted}
- Non-canonical files removed: {non_canonical_files_removed}
- Outbox wired: {outbox_wired}
- Manifest mounted: {manifest_mounted}

## Stack Detection

{paste Gate 0 detection table}

## Gate Results

| Gate | Name | Status |
|------|------|--------|
| 0 | Stack + JSON + Audit + Non-Canonical | PASS |
| 1 | Codebase Analysis | PASS |
| 1.5 | Visual Preview | APPROVED |
| 2 | Dependency + Removal | PASS |
| 3 | Catalog + Producer | PASS |
| 4 | Emit Instrumentation | PASS |
| 5 | Outbox Wiring | PASS / SKIPPED ({reason}) |
| 6 | Manifest Mount | PASS / SKIPPED ({reason}) |
| 7 | Wiring + Lifecycle | PASS |
| 8 | Tests | PASS |
| 9 | Code Review | PASS (10/10) |
| 10 | User Validation | APPROVED |
| 11 | Activation Guide | docs/streaming-guide.md |

## Verification

- `go build ./...` — PASS
- `go test ./... -race` — PASS
- `go test -tags integration ./...` — PASS
- Coverage on streaming files: {percent}%
- Backward compat: STREAMING_ENABLED=false matches baseline
- Goroutine leak: clean

Service is ready to enable streaming. See `docs/streaming-guide.md`.
```
