---
name: ring:streaming-event-mapping
description: |
  Discovery and mapping skill for Lerian PM teams to identify "eventable points" in a Go service codebase
  where lib-streaming should emit business events to third-party clients (typically per-tenant SaaS
  subscribers). Produces TWO artifacts: a PM-validated event catalog (Markdown) AND a machine-readable
  instrumentation map (JSON) consumed directly by ring:dev-streaming-instrumentation. Three layered
  passes: Survey (service understanding + entry-point inventory), Slice (segment + commit boundaries +
  scope-fence pre-filter), Mark (parallel deep walk per segment proposing file:line + posture). Enforces
  the lib-streaming scope fence (past-tense, durable, broadcastable, tenant-scoped business facts only)
  and three named delivery postures — CRITICAL (atomic with DB), IMPORTANT (resilient, broker-outage
  surviving), OBSERVATIONAL (best-effort) — plus CUSTOM with mandatory written justification. Loads
  canonical lib-streaming docs via WebFetch from main.

trigger: |
  - User requests an event catalog, eventable-point inventory, or "where should we emit events" map
  - PM team prepares a Lerian Go service for client-facing event streaming subscriptions
  - Pre-flight to ring:dev-streaming-instrumentation
  - Task mentions "event mapping", "streaming inventory", "eventable points", "client event subscription",
    "what events should this service emit", "outbound business events"

skip_when: |
  - Service is not a Go project (lib-streaming is Go-only)
  - Service has no business logic to emit events about (pure infrastructure, gateway, sidecar, proxy)
  - Task is purely documentation, configuration, or non-discovery
  - Service is consumer-only with no outbound business event surface

prerequisites: |
  - Go service codebase available for read access (lib-commons-aware preferred but not required)
  - At least one entry point present: HTTP route, gRPC method, RabbitMQ consumer, scheduled job,
    or webhook receiver
  - Tenant identity resolvable from request context (typically via tmcore.GetTenantIDContext)

NOT_skip_when: |
  - "We already know the events, just write them down" → Knowing is not cataloging. Catalog discipline
    is the forcing function. Three-pass discovery surfaces what stakeholders forgot. Run the skill.
  - "Just walk the endpoints" → Endpoints are starting points, not the answer. Background workers,
    scheduled jobs, RabbitMQ consumers, saga steps, and webhook receivers are equally valid event
    sources. Pass 1 inventories ALL entry points.
  - "Skip Pass 1, go straight to marking" → Without service understanding, Pass 3 over-marks (false
    positives) and mis-classifies postures. Pass 1 and Pass 2 are NOT optional.
  - "We don't need posture per event, default everything to direct" → Posture and existence are
    orthogonal axes the library was designed to capture. Collapsing them throws away information.
    CRITICAL events become best-effort and clients lose data.
  - "Just produce the JSON, the Markdown is overhead" → Markdown is the PM-validation surface. JSON
    without Gate 6 PM approval is an unverified handoff. Both required.
  - "Scope fence is too strict, let some borderline events through" → Scope fence is the rule.
    Borderline candidates → REJECT with documented reason. The fence is what makes the catalog
    maintainable and the client subscriptions stable.

sequence:
  before: [ring:dev-streaming-instrumentation]

related:
  complementary: [ring:dev-streaming-instrumentation, ring:codebase-explorer, ring:pre-dev-feature-map,
                  ring:pre-dev-prd-creation, ring:visualize]

input_schema:
  description: |
    Standalone invocation only. Skill auto-detects stack in Gate 0. No structured handoff fields.
  fields: []

output_schema:
  format: markdown
  required_sections:
    - name: "Streaming Event Mapping Summary"
      pattern: "^## Streaming Event Mapping Summary"
      required: true
    - name: "Stack Detection"
      pattern: "^## Stack Detection"
      required: true
    - name: "Pass Results"
      pattern: "^## Pass Results"
      required: true
    - name: "Catalog Output"
      pattern: "^## Catalog Output"
      required: true
    - name: "Handoff to Skill #2"
      pattern: "^## Handoff to Skill #2"
      required: true
  metrics:
    - name: entry_points_inventoried
      type: integer
    - name: segments_identified
      type: integer
    - name: candidates_pre_scope_fence
      type: integer
    - name: events_after_scope_fence
      type: integer
    - name: events_critical
      type: integer
    - name: events_important
      type: integer
    - name: events_observational
      type: integer
    - name: events_custom
      type: integer

---

# Streaming Event Mapping (lib-streaming, PM-team)

<cannot_skip>

## CRITICAL: This Skill ORCHESTRATES. Agents EXPLORE.

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Detect stack, dispatch explorers in 3 passes, enforce scope fence, validate JSON output, gate PM approval |
| **ring:codebase-explorer** | Read and analyze codebase under focused per-pass prompts; propose events and postures with rationale |
| **PM team (human)** | Validate event catalog at Gate 6 before handoff to ring:dev-streaming-instrumentation |

**CANNOT change scope:** the skill defines WHAT to discover and HOW to classify. Explorers propose; PM validates; skill enforces.

**FORBIDDEN: Orchestrator MUST NOT instrument code or write Go source files.** This is a discovery skill. The output is artifacts in `docs/streaming/` — nothing in `internal/` or `pkg/`. All code instrumentation belongs to ring:dev-streaming-instrumentation.

**MANDATORY: Three-pass structure.** MUST execute Pass 1 → Pass 2 → Pass 3 sequentially. Pass 3 dispatches in parallel (one explorer per segment from Pass 2), but Passes themselves are sequential. Skipping or reordering passes is FORBIDDEN.

</cannot_skip>

---

## Streaming Architecture (lib-streaming, the model)

lib-streaming is a producer-only, write-only event-emission library for Lerian Go services. Bootstrapped once via `streaming.NewProducer(ctx, cfg, opts...)` with a `Catalog` registered at construction. Events are emitted via `producer.Emit(ctx, EmitRequest{DefinitionKey, TenantID, Subject, Payload})`. Wire format: CloudEvents 1.0 binary mode for Kafka. Topics shared across tenants (`lerian.streaming.<resource>.<event>[.vN]`); tenant carried on `ce-tenantid` header and partition key.

**Key forcing function:** the Catalog is registered at bootstrap and is immutable. You CANNOT emit a `DefinitionKey` that wasn't registered. This skill produces the catalog (Skill #2 wires it).

**Three named delivery postures** (axis: `Direct × Outbox × DLQ` per event):

| Posture | Direct | Outbox | DLQ | Use when |
|---------|--------|--------|-----|----------|
| CRITICAL | skip | always | on_routable_failure | Loss is correctness/compliance breach; must be atomic with DB write |
| IMPORTANT | direct | fallback_on_circuit_open | on_routable_failure | Direct in normal ops; survives broker outage; recoverable on hard fail |
| OBSERVATIONAL | direct | never | never | Analytics-grade; loss acceptable; cheap |
| CUSTOM | per-event | per-event | per-event | None of the above fits — REQUIRES written justification ≥80 chars |

**Standards reference:** lib-streaming has no `streaming.md` standards file. The authoritative source is the package `doc.go` in the lib-streaming repo:

**WebFetch URL (canonical lib-streaming docs):**
`https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go`

**WebFetch URL (agent-facing constraints):**
`https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md`

---

## MANDATORY: Scope Fence

A candidate is a **streamable business fact** if and ONLY if ALL of:

1. **Past-tense** — describes something that already happened (`account.created`, not `account.create`).
2. **Durable** — the underlying state is persisted; the event is not transient/ephemeral.
3. **Broadcastable** — multiple consumers (the SaaS client + analytics + audit) could legitimately receive it.
4. **Tenant-scoped** — the event belongs to a tenant (or is a marked SystemEvent with explicit `WithAllowSystemEvents` justification).

**HARD GATE: Candidates failing ANY of the four → REJECT with documented reason.**

### What goes IN

| Type | Example |
|------|---------|
| Aggregate state changes | `account.created`, `account.archived`, `transaction.posted`, `transaction.reversed` |
| Lifecycle transitions | `kyc.approved`, `kyc.rejected`, `subscription.activated` |
| Durable artifact emissions | `statement.generated`, `report.published` |
| Compliance signals | `aml.flagged`, `audit_export.completed` |

### What stays OUT

| What | Why | Where it belongs |
|------|-----|------------------|
| Internal command dispatch ("create transaction now") | Not past-tense; pre-state-change | `lib-commons/v5/commons/rabbitmq` |
| Cache invalidation pings | Not durable; transport detail | Internal pub/sub or none |
| Saga step transitions ("step 3 → step 4") | Internal saga state, not a client-relevant fact | Saga state machine |
| Audit log entries | Different consumer model and retention | Audit pipeline |
| Synchronous request/response | Not broadcastable; 1:1 by design | HTTP / gRPC |
| Health/heartbeat signals | Not tenant-scoped; not a business fact | OTEL / health probe |
| Work-queue items | Command, not fact | `lib-commons/v5/commons/dlq` (Redis) or rabbitmq |
| Internal worker progress events | Not broadcastable; implementation detail | Internal logs / metrics |

**Anti-pattern:** "Let's emit an event for every state change so clients have full visibility." → Result: unmaintainable taxonomy, schema-version churn, client integration burden, no clear contract. The fence is the constraint that makes the catalog stable.

---

## MANDATORY: instrumentation-map.json schema

This is the canonical handoff to ring:dev-streaming-instrumentation. EVERY entry MUST have ALL fields populated. No `null`, no `TBD`, no placeholder strings.

```json
{
  "schema_version": "1.0.0",
  "service_name": "<from Gate 0>",
  "tenant_source": "<idiomatic call, e.g. tmcore.GetTenantIDContext(ctx)>",
  "events": [
    {
      "definition_key": "transaction.posted",
      "resource_type": "transaction",
      "event_type": "posted",
      "schema_version": "1.0.0",
      "data_content_type": "application/json",
      "data_schema": "",
      "is_system_event": false,
      "description": "A transaction has been posted to the ledger and is now visible to the tenant.",
      "instrumentation_sites": [
        {
          "file": "internal/services/transaction/post.go",
          "line_anchor": "after txnRepo.Save(ctx, t) returns nil; before HTTP 201 return",
          "emission_timing": "post-commit",
          "current_function": "(s *Service) Post"
        }
      ],
      "payload_sketch": {
        "transaction_id": "uuid",
        "amount": "decimal",
        "currency": "string",
        "posted_at": "timestamp",
        "from_account_id": "uuid",
        "to_account_id": "uuid"
      },
      "tenant_source_at_site": "tmcore.GetTenantIDContext(ctx)",
      "consumer_idempotency_key_candidate": "event_id",
      "posture": "CRITICAL",
      "posture_rationale": "Money movement; loss = ledger inconsistency; consumer reconciliation requires atomic delivery with DB write.",
      "delivery_policy": {
        "enabled": true,
        "direct": "skip",
        "outbox": "always",
        "dlq": "on_routable_failure"
      }
    }
  ],
  "summary": {
    "entry_points_inventoried": 0,
    "segments_identified": 0,
    "candidates_pre_scope_fence": 0,
    "events_after_scope_fence": 0,
    "events_critical": 0,
    "events_important": 0,
    "events_observational": 0,
    "events_custom": 0
  }
}
```

**Validation rules** (Gate 4 enforces all of these):

- `definition_key` MUST be unique within the events array
- `definition_key` MUST match `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$` (lowercase, single dot, snake_case allowed within each side)
- `(resource_type, event_type, schema_version)` triple MUST be unique
- `tenant_source_at_site` MUST be non-empty UNLESS `is_system_event=true`
- `posture` MUST be one of: `CRITICAL`, `IMPORTANT`, `OBSERVATIONAL`, `CUSTOM`
- `posture == "CUSTOM"` REQUIRES `posture_rationale` length ≥ 80 characters
- `delivery_policy` MUST match the canonical mapping for non-CUSTOM postures (see vocabulary table above)
- `instrumentation_sites` MUST have at least one entry; each entry's `file` MUST exist in the codebase
- Every event MUST have `description` length ≥ 40 characters
- Every event MUST have `payload_sketch` with at least one field

---

## MANDATORY: Agent Instruction (include in EVERY explorer dispatch)

MUST include these instructions verbatim in every dispatch to `ring:codebase-explorer`:

> **STANDARDS:** WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go` for the canonical event model. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md` for invariants. Skill #1 is mapping; you are NOT writing code.
>
> **SCOPE FENCE:** A candidate is streamable IFF (past-tense AND durable AND broadcastable AND tenant-scoped). Reject candidates failing any check, with a one-line documented reason.
>
> **POSTURE:** Three named postures (CRITICAL / IMPORTANT / OBSERVATIONAL) plus CUSTOM. Propose one per event with a one-sentence rationale grounded in business impact (loss tolerance, atomicity needs, consumer-side criticality). CUSTOM requires written justification ≥80 chars.
>
> **OUTPUT:** Strict JSON conforming to the instrumentation-map.json schema embedded in the skill. Every field populated. No TBDs. No code edits — read-only exploration.

---

## Severity Calibration

| Severity | Criteria | Examples |
|----------|----------|----------|
| **CRITICAL** | Output structure broken; PM cannot validate; Skill #2 cannot consume | Missing required JSON field; duplicate `(resource_type, event_type, schema_version)`; unparseable JSON; `instrumentation_sites` empty |
| **HIGH** | Scope-fence violation accepted; posture-policy mismatch; tenant source missing on non-system event | Internal command marked as event; CRITICAL posture with `outbox=never`; `is_system_event=false` AND `tenant_source_at_site=""` |
| **MEDIUM** | Discoverable but not load-bearing | Naming convention drift (CamelCase in `definition_key`); `description` shorter than 40 chars; payload_sketch incomplete |
| **LOW** | Cosmetic | Inconsistent rationale length above 80; redundant fields |

MUST report all severities. CRITICAL: STOP immediately, dispatch agent to fix. HIGH: Fix before Gate 4 passes. MEDIUM: Fix in Gate 6 PM iteration. LOW: Document.

---

## Pressure Resistance

| User Says | This Is | Response |
|-----------|---------|----------|
| "We already have a list of events, skip the discovery" | DISCIPLINE_BYPASS | "Lists drift from code. Three-pass discovery cross-checks the list against actual commit boundaries. MUST run all three passes." |
| "Pass 1 is fluff, just walk the code" | SCOPE_REDUCTION | "Pass 1 inventories entry points (HTTP, workers, cron, consumers, webhooks). Without it, Pass 3 only sees handlers and misses 50% of event sources. NOT optional." |
| "Skip Pass 2, parallelize Pass 3 over all files" | PERFORMANCE_BYPASS | "Pass 2 segments + applies the scope fence. Without segmentation, parallel Pass 3 over-marks (false positives) and the assembler at Gate 4 churns. NOT optional." |
| "We don't need three postures, just direct-emit everything" | OPINION_BYPASS | "Posture is per-event policy lib-streaming was designed to capture. Collapsing it loses CRITICAL events to broker outages. Three-posture vocabulary is mandatory." |
| "Markdown is overhead, just give us the JSON" | VALIDATION_BYPASS | "Markdown is the PM-team validation surface. JSON without Gate 6 PM approval is an unverified handoff. Both produced; both required." |
| "The scope fence is too strict, let some borderline events through" | SCOPE_CREEP | "Borderline = REJECT with documented reason. The fence is the rule. CUSTOM posture handles legitimate edge cases via written justification — that is the escape hatch." |
| "Skip the JSON validation, ship the file" | QUALITY_BYPASS | "Gate 4 validates uniqueness, naming, posture-policy consistency. Unvalidated JSON breaks Skill #2 silently. NOT skippable." |
| "The agent already produced output, no need for PM review" | GOVERNANCE_BYPASS | "The catalog is a contract with the SaaS client. PM owns business semantics; engineer owns technical correctness. Both validate. Gate 6 is mandatory." |
| "Just write the events I tell you to" | METHOD_BYPASS | "User-supplied lists are inputs to Pass 1 (cross-referenced with codebase reality), not substitutes for it. Three-pass discovery surfaces what stakeholders forgot." |
| "We're under time pressure, parallelize everything" | TIME_BYPASS | "Pass 1→2→3 are sequential by design (each consumes the prior). Parallelism is INSIDE Pass 3 only. Total wall time is bounded; cutting passes corrupts output." |
| "Use my naming, not the lowercase-dotted convention" | CONVENTION_BYPASS | "Catalog keys cascade to topic names. Inconsistent naming breaks consumer expectations. Convention is enforced at Gate 4 validation." |
| "We can mark a CRITICAL event as OBSERVATIONAL temporarily" | POSTURE_BYPASS | "Posture mismatch ships as the event's persisted DefaultPolicy. 'Temporarily' becomes 'forever' in production. Per-event posture is correct or it's wrong." |

---

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "I know the events, I'll just write the JSON" | Knowing != cataloged. Three-pass discovery surfaces forgotten event sources (workers, cron, webhooks). | **MUST run all three passes** |
| "Endpoints are sufficient as event sources" | Endpoints are 50% of event sources. Workers/cron/sagas/webhooks emit too. | **Pass 1 inventories ALL entry points** |
| "Posture can default to OBSERVATIONAL for everything" | OBSERVATIONAL = best-effort. CRITICAL events become lossy on broker outage. | **Per-event posture with rationale** |
| "Scope fence is heuristic, exceptions are fine" | Scope fence is the rule. Exceptions = catalog churn = unstable client contracts. | **REJECT borderline candidates** |
| "Markdown is for show; JSON is what matters" | Markdown is PM validation. Without Gate 6, JSON is unverified. | **Both required** |
| "Naming convention is preference, not enforcement" | Naming inconsistency cascades to topic names, breaks consumer expectations. | **Enforce `<resource>.<event>` lowercase dotted** |
| "Skill #2 will fix any JSON issues" | Skill #2 consumes structurally. Bad JSON = silent skill #2 failure. | **Gate 4 validates ALL fields** |
| "PM doesn't need to validate every event" | Catalog is a client contract. PM owns business semantics. | **Gate 6 is mandatory** |
| "Pass 3 should run sequentially to avoid output collisions" | Each Pass 3 explorer writes its own per-segment file. No collisions possible. Sequential = wall-time waste. | **MUST dispatch Pass 3 in parallel** |
| "Empty segment after fence = bug, fix the fence" | Empty segment = healthy fence application. Document and continue. | **Document in Pass 2 explicitly** |
| "Trust the explorer's posture without rationale" | Posture without rationale is unfalsifiable. PM cannot validate. | **MUST include posture_rationale on every event** |

---

## Gate Overview

| Gate | Name | Condition | Agent |
|------|------|-----------|-------|
| 0 | Stack Detection | Always | Orchestrator (grep + read) |
| 1 | Pass 1 — Survey | Always | ring:codebase-explorer (single) |
| 2 | Pass 2 — Slice + Scope Fence | Always | ring:codebase-explorer (single) |
| 3 | Pass 3 — Mark | Always | ring:codebase-explorer (parallel, 1 per segment) |
| 4 | Catalog Assembly + Validation | Always | Orchestrator (deterministic merge + schema validation) |
| 5 | Business Rendering | Always | Orchestrator (Markdown generation from JSON) |
| 6 | PM Team Validation ⛔ NEVER SKIPPABLE | Always | User (PM team) |
| 7 | Handoff Package | Always | Orchestrator |

MUST execute gates sequentially. Pass 3 (Gate 3) parallelizes INTERNALLY across segments. CANNOT skip or reorder gates.

---

## Gate 0: Stack Detection

**Orchestrator executes directly. No agent dispatch.**

Detect everything Pass 1 will need to know without reading code in depth.

```text
DETECT (run in parallel):

1. Go project:           grep "^go " go.mod | head -1
2. lib-commons version:  grep "lib-commons" go.mod
3. lib-streaming present: grep "lib-streaming" go.mod
4. HTTP framework:
   - Fiber:    grep -rn "gofiber/fiber" internal/ go.mod
   - Echo:     grep -rn "labstack/echo" internal/ go.mod
   - Gin:      grep -rn "gin-gonic/gin" internal/ go.mod
   - net/http: grep -rn "net/http" internal/main.go internal/cmd/
5. gRPC server:          grep -rn "grpc.NewServer\|google.golang.org/grpc" internal/ go.mod
6. RabbitMQ consumers:
   - lib-commons:    grep -rn "lib-commons/v5/commons/rabbitmq" internal/
   - amqp091 direct: grep -rn "amqp091-go" internal/
7. Scheduled jobs:       grep -rn "robfig/cron\|ticker.*time.NewTicker\|gocron" internal/
8. Webhook receivers:    grep -rn "webhook\|/hooks/\|inbound.*event" internal/
9. Worker patterns:      grep -rn "commons.Launcher\|commons.App\|launcher.Add" internal/
10. Tenant source:
    - tmcore:    grep -rn "tmcore.GetTenantIDContext\|GetTenantID(ctx" internal/
    - JWT claim: grep -rn "ctx.Locals.*tenant\|c.Get.*X-Tenant" internal/
11. Existing event-emission code:
    - Direct sarama:        grep -rn "Shopify/sarama\|IBM/sarama" go.mod internal/
    - Direct franz-go:      grep -rn "twmb/franz-go" internal/  (NOT routed through lib-streaming)
    - watermill:            grep -rn "ThreeDotsLabs/watermill" go.mod internal/
    - segmentio:            grep -rn "segmentio/kafka-go" go.mod internal/
    - amqp091 publish:      grep -rn "amqp091.*Publish\|channel.Publish" internal/
    - lib-streaming itself: grep -rn "lib-streaming\|streaming.NewProducer\|streaming.Emit" internal/
12. DDD layout / aggregates:
    - Common Lerian patterns: ls internal/services/ internal/domain/ internal/aggregates/ 2>/dev/null
13. Database handles (for future outbox detection):
    - Postgres:  grep -rn "database/sql\|jackc/pgx" internal/ go.mod
    - MongoDB:   grep -rn "go.mongodb.org/mongo-driver" internal/ go.mod
14. Multi-tenancy infra:
    - lib-commons: grep -rn "lib-commons/v5/commons/multitenancy" internal/ go.mod
```

**Output format:**

```text
STACK DETECTION RESULTS:
| Aspect                          | Detected                                 |
|---------------------------------|------------------------------------------|
| Go version                      | 1.25                                     |
| HTTP framework                  | Fiber                                    |
| gRPC                            | NO                                       |
| RabbitMQ consumers              | YES (lib-commons/v5/commons/rabbitmq)    |
| Scheduled jobs                  | NO                                       |
| Webhooks                        | YES (`/hooks/inbound`)                   |
| Worker pattern                  | commons.Launcher                         |
| Tenant source                   | tmcore.GetTenantIDContext                |
| Existing event-emission         | NONE (greenfield)                        |
| DDD layout                      | internal/services/<domain>/              |
| Postgres                        | YES                                      |
| MongoDB                         | NO                                       |
| Multi-tenancy infra             | lib-commons multitenancy                 |
| lib-streaming dep               | NOT present                              |
```

<block_condition>
HARD GATE: If "Go project" is NO → STOP. lib-streaming is Go-only. This skill cannot proceed.

HARD GATE: If "tenant source" is undetectable → STOP and ask user. Cannot map events without tenant scoping.
</block_condition>

---

## Gate 1: Pass 1 — Survey

**Always executes. Single explorer dispatch.**

Builds the service understanding required for Pass 2 segmentation.

**Dispatch `ring:codebase-explorer` with this exact prompt structure:**

> **STANDARDS:** WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go` for the canonical event model. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md` for invariants.
>
> **TASK:** Survey this Go service to build a service-level mental model that downstream passes will use.
>
> **DETECTED STACK** (from Gate 0): {paste detection results}
>
> **OUTPUT FILE:** `docs/streaming/_pass1-survey.md`
>
> **REQUIRED SECTIONS** (use these exact headers):
>
> ## Service Identity
> - Service name (look for `const ApplicationName` or equivalent)
> - One-paragraph plain-English description: what does this service do?
> - Top-level value chain: input → processing → output
> - Bounded context: what business domain does this serve?
>
> ## Entry Point Inventory
> Exhaustive list, grouped by type. For each entry, provide: type, identifier, file:line where registered, brief purpose.
>
> - **HTTP routes**: every route registered on the router (method + path + handler)
> - **gRPC methods**: every service method
> - **RabbitMQ consumers**: every queue subscription
> - **Scheduled jobs**: every cron/ticker entry with cadence
> - **Webhook receivers**: inbound webhook endpoints (often a special case of HTTP)
> - **CLI commands**: any `cobra.Command` or equivalent that triggers business logic
>
> ## Aggregate Inventory
> Identify every aggregate / entity / domain object the service OWNS (mutates and persists). Distinguish from references to aggregates owned by other services.
>
> For each aggregate:
> - Aggregate name (e.g. `Account`, `Transaction`, `Statement`)
> - Persistence backend (Postgres? Mongo? Both?)
> - Repository file:line
> - Lifecycle states the aggregate transitions through (e.g. `Account: created → active → frozen → archived`)
>
> ## Tenant Identity Resolution
> - Idiomatic call (e.g. `tmcore.GetTenantIDContext(ctx)`)
> - Where in the stack it's set (auth middleware? gRPC interceptor? message header?)
> - Whether it's reliably non-empty for ALL entry-point types (HTTP usually yes; cron jobs require special handling)
> - System events: any code paths that operate without a tenant (cluster-wide jobs, system bootstrap, etc.)
>
> ## External Dependencies
> Brief list of:
> - Databases
> - External HTTP APIs called
> - Message brokers used
> - Object storage / file emission targets
>
> Purpose: Pass 2 needs to classify side effects per segment.
>
> ## Existing Event-Emission Code (if any)
> Any direct usage of sarama/amqp091/watermill/segmentio/kafka-go/franz-go OUTSIDE of lib-streaming → flag with file:line. These are migration candidates for Skill #2.
>
> ## Notes for Pass 2
> Anything that would shape segmentation. E.g., "service has 3 clear domain modules: ledger, identity, reporting", or "everything is in one big internal/handlers package".
>
> ---
>
> **CONSTRAINTS:**
> - Read whole files when needed; don't speculate.
> - Quote actual file paths and function names.
> - Word count: 800-1500 words. Reference material; depth welcome.
> - DO NOT propose events. DO NOT walk code in depth. This is the survey pass — segmenters and markers come later.
> - DO NOT write the JSON output. That happens at Gate 4.

**Verification (orchestrator):**

- File `docs/streaming/_pass1-survey.md` exists
- All 7 required sections present (`grep "^## "`)
- "Entry Point Inventory" has at least 1 entry
- "Aggregate Inventory" has at least 1 entry
- "Tenant Identity Resolution" identifies a non-empty source

<block_condition>
HARD GATE: If verification fails → re-dispatch with correction notes. Cannot proceed to Pass 2 without valid Pass 1 output.
</block_condition>

---

## Gate 2: Pass 2 — Slice + Scope Fence

**Always executes. Single explorer dispatch with Pass 1 output as context.**

Cuts the codebase into segments and pre-filters candidate events through the scope fence. The output drives Pass 3's parallel walk.

**Dispatch `ring:codebase-explorer`:**

> **STANDARDS:** WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go`. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md`.
>
> **TASK:** Slice the codebase into segments and pre-filter event candidates through the scope fence.
>
> **PASS 1 OUTPUT:** Read `docs/streaming/_pass1-survey.md` in full. It is your starting context.
>
> **OUTPUT FILE:** `docs/streaming/_pass2-segments.md`
>
> **REQUIRED SECTIONS** (use these exact headers):
>
> ## Segmentation Strategy
> Brief paragraph: how is the codebase organized? Choose ONE primary segmentation:
> - By domain module (`ledger`, `identity`, `reporting`) — preferred when codebase has clean DDD layout
> - By aggregate (`Account`, `Transaction`, `Statement`) — preferred when modules are blurred
> - By entry-point type (`http`, `worker`, `cron`, `consumer`) — fallback for flat layouts
>
> Justify the choice in 2-3 sentences.
>
> ## Segments
>
> For each segment (typically 3-8 segments):
>
> ### <Segment Name>
>
> - **Files**: glob pattern (e.g., `internal/services/ledger/**/*.go`)
> - **Aggregates touched**: from Pass 1's aggregate inventory
> - **Side-effect classification per file** (table):
>
>   | File | Side effects observed |
>   |------|----------------------|
>   | `post.go` | DB write (transactions table); audit log entry |
>   | `reverse.go` | DB write (transactions + balances); RabbitMQ command emit |
>
> - **Commit boundaries**: places where state is durably persisted (e.g., "after `repo.Save()` returns nil"). For each, list:
>   - File:line of the commit boundary
>   - One-line description of what just persisted
> - **Pre-scope-fence candidate count**: number of commit boundaries before fence
> - **Post-scope-fence candidate count**: number after applying the four-test fence
> - **Rejected candidates**: per rejected commit boundary, one-line reason citing which fence test failed
>
> ## Scope Fence Application
>
> Tabulated reasoning for the rejection decisions. Format:
>
> | File:line | Candidate Description | Past-tense? | Durable? | Broadcastable? | Tenant-scoped? | Verdict |
> |-----------|----------------------|-------------|----------|----------------|----------------|---------|
> | `cache.go:42` | `cache.Set(...)` after DB write | Y | N (transient) | N | N/A | REJECT (not durable, not broadcastable) |
> | `post.go:142` | `txnRepo.Save(...)` then HTTP 201 | Y | Y | Y | Y | ACCEPT |
>
> List EVERY candidate from EVERY segment. The fence is the rule.
>
> ## Pass 3 Dispatch Plan
>
> One row per segment that survived with at least one ACCEPTed candidate:
>
> | Segment | Files (glob) | Accepted Candidates | Pass 3 Sub-prompt Hint |
> |---------|-------------|--------------------|-----------------------|
> | ledger | `internal/services/ledger/**/*.go` | 4 | "Focus on transaction lifecycle: posted, reversed, settled" |
>
> ---
>
> **CONSTRAINTS:**
> - Apply the scope fence MECHANICALLY. Each candidate gets a Y/N on each of the four tests. NO exceptions.
> - "Borderline" = REJECT with reason. CUSTOM posture later handles legitimate edge cases at Pass 3.
> - DO NOT propose catalog keys, postures, or payload schemas. Pass 3 does that.
> - Word count: 1000-2000 words.

**Verification (orchestrator):**

- File `docs/streaming/_pass2-segments.md` exists
- "Segments" section has at least 1 segment
- "Scope Fence Application" table has every candidate with all four tests scored
- "Pass 3 Dispatch Plan" has at least 1 segment with accepted candidates

<block_condition>
HARD GATE: If verification fails → re-dispatch with correction notes.

HARD GATE: If post-fence candidate count is 0 across all segments → STOP and report. Either the scope fence is being misapplied, or the service truly has no streamable events. Surface to user before proceeding.
</block_condition>

---

## Gate 3: Pass 3 — Mark (Parallel)

**Always executes. PARALLEL dispatch, one explorer per segment.**

For each segment from Gate 2, dispatch `ring:codebase-explorer` IN PARALLEL with the segment-specific deep-walk prompt. Each explorer outputs a per-segment JSON partial; Gate 4 assembles them.

**Dispatch pattern (orchestrator):**

For EACH segment in Gate 2's "Pass 3 Dispatch Plan":

```text
PARALLEL DISPATCH (single message, multiple Task tool calls):

For segment "ledger":
  → Task(subagent_type="ring:codebase-explorer", prompt={Pass-3-template + segment context})

For segment "identity":
  → Task(subagent_type="ring:codebase-explorer", prompt={Pass-3-template + segment context})

For segment "reporting":
  → Task(subagent_type="ring:codebase-explorer", prompt={Pass-3-template + segment context})
```

**Per-explorer prompt (Pass-3-template):**

> **STANDARDS:** WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go`. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md`.
>
> **TASK:** For each ACCEPTED candidate in segment "{segment_name}", produce a complete EventDefinition + instrumentation site + posture proposal.
>
> **PASS 1 OUTPUT:** `docs/streaming/_pass1-survey.md`
> **PASS 2 OUTPUT:** `docs/streaming/_pass2-segments.md`
> **YOUR SEGMENT:** {segment_name}
> **YOUR ACCEPTED CANDIDATES** (from Pass 2):
> {paste rows for this segment from Pass 2's "Pass 3 Dispatch Plan" + accepted candidates table}
>
> **OUTPUT FILE:** `docs/streaming/_pass3-{segment_name}.json`
>
> **OUTPUT SCHEMA:** EXACTLY this shape — populate every field:
>
> ```json
> {
>   "segment": "{segment_name}",
>   "events": [
>     {
>       "definition_key": "transaction.posted",
>       "resource_type": "transaction",
>       "event_type": "posted",
>       "schema_version": "1.0.0",
>       "data_content_type": "application/json",
>       "data_schema": "",
>       "is_system_event": false,
>       "description": "...",
>       "instrumentation_sites": [
>         {
>           "file": "...",
>           "line_anchor": "...",
>           "emission_timing": "post-commit | pre-respond | end-of-saga-step | post-cron-tick",
>           "current_function": "..."
>         }
>       ],
>       "payload_sketch": { "field_name": "type" },
>       "tenant_source_at_site": "tmcore.GetTenantIDContext(ctx)",
>       "consumer_idempotency_key_candidate": "event_id",
>       "posture": "CRITICAL | IMPORTANT | OBSERVATIONAL | CUSTOM",
>       "posture_rationale": "...",
>       "delivery_policy": {
>         "enabled": true,
>         "direct": "skip | direct",
>         "outbox": "always | fallback_on_circuit_open | never",
>         "dlq": "on_routable_failure | never"
>       }
>     }
>   ]
> }
> ```
>
> **POSTURE DECISION TREE** (apply per event):
>
> 1. Is loss of this event a correctness or compliance breach (financial, regulatory, ledger consistency)?
>    → CRITICAL — direct=skip, outbox=always, dlq=on_routable_failure
> 2. Is this event used by consumers as authoritative state (vs. analytics)?
>    → IMPORTANT — direct=direct, outbox=fallback_on_circuit_open, dlq=on_routable_failure
> 3. Is this event purely observational, analytics-grade, non-load-bearing?
>    → OBSERVATIONAL — direct=direct, outbox=never, dlq=never
> 4. None of the above cleanly?
>    → CUSTOM — write a ≥80-char `posture_rationale` justifying the policy combination
>
> **NAMING CONVENTION:**
> - `definition_key` = `<resource>.<event>` (lowercase, single dot, snake_case allowed within each side)
> - `resource_type` = entity name (e.g. `transaction`, `account`, `statement`)
> - `event_type` = past-tense verb (e.g. `posted`, `created`, `archived`, `approved`, `published`)
> - `schema_version` = semver MAJOR.MINOR.PATCH; default `1.0.0` for new events
>
> **PAYLOAD SKETCH:**
> - List the fields a consumer would need to act on this event meaningfully.
> - Use Go-friendly type tags: `uuid`, `string`, `decimal`, `int`, `bool`, `timestamp`, `enum<value1|value2>`, `array<type>`, `object`.
> - Avoid leaking internal-only fields (database PKs that aren't the aggregate ID, internal flags).
> - PII annotation: if a field is PII, suffix with ` (PII)` — e.g., `email: string (PII)`. The implementation skill will surface this for redaction policy review.
>
> **TENANT SOURCE PER SITE:**
> - HTTP handler: typically `tmcore.GetTenantIDContext(ctx)` from auth middleware
> - RabbitMQ consumer: parse from message header (`x-tenant-id`) or body envelope
> - Cron job: tenant must be derivable per-tenant iteration; if cluster-wide → mark `is_system_event=true`
> - Webhook: tenant from URL param OR resolved from incoming-payload account-id lookup
>
> **CONSTRAINTS:**
> - One event per (resource_type, event_type, schema_version) triple. If the same fact is emitted from multiple sites, list the sites under one event's `instrumentation_sites` array.
> - Read the actual source. Do NOT invent function names, file paths, or line numbers. Use `line_anchor` (a description of the surrounding code) instead of literal line numbers when the code is volatile.
> - DO NOT instrument code. DO NOT write Go files. JSON output ONLY.

**Verification (orchestrator):**

After all parallel dispatches complete:

- One `_pass3-{segment_name}.json` file exists per segment from Gate 2
- Each file is valid JSON
- Each event in each file has all required fields populated (no `null`, no `TBD`)
- Each event's `posture` is one of the four valid values
- Each `posture == "CUSTOM"` has `posture_rationale` length ≥ 80 chars

<block_condition>
HARD GATE: If any per-segment file is missing or malformed → re-dispatch ONLY the failing segment(s).
</block_condition>

---

## Gate 4: Catalog Assembly + Validation

**Always executes. Orchestrator-direct (deterministic merge + schema validation). No agent dispatch.**

Merge all per-segment partials into one canonical `instrumentation-map.json` and validate against the schema embedded earlier in this skill.

**Orchestrator workflow:**

```text
1. Read every docs/streaming/_pass3-{segment_name}.json
2. Concatenate the `events` arrays into a single array
3. Build the top-level wrapper with service_name (from Gate 0) and tenant_source (from Pass 1)
4. Compute `summary` block:
   - entry_points_inventoried (count from Pass 1)
   - segments_identified (count from Pass 2)
   - candidates_pre_scope_fence (sum from Pass 2)
   - events_after_scope_fence (length of merged events array)
   - events_critical, events_important, events_observational, events_custom (count by posture)
5. Validate:
   a. definition_key uniqueness within events array
   b. (resource_type, event_type, schema_version) uniqueness
   c. definition_key matches `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`
   d. Every event with is_system_event=false has tenant_source_at_site != ""
   e. Every event has description with len ≥ 40
   f. Every event has payload_sketch with ≥ 1 field
   g. Posture / delivery_policy consistency for non-CUSTOM postures:
      - CRITICAL → direct=skip, outbox=always, dlq=on_routable_failure
      - IMPORTANT → direct=direct, outbox=fallback_on_circuit_open, dlq=on_routable_failure
      - OBSERVATIONAL → direct=direct, outbox=never, dlq=never
   h. Every CUSTOM has posture_rationale length ≥ 80
6. Write final docs/streaming/instrumentation-map.json
```

**Validation failures → re-dispatch the failing segment's Pass 3 explorer with correction notes. Do NOT manually edit the JSON.**

<block_condition>
HARD GATE: All eight validation checks MUST pass. CANNOT proceed to Gate 5 until Gate 4 produces a clean JSON file.
</block_condition>

---

## Gate 5: Business Rendering

**Always executes. Orchestrator-direct (Markdown generation from validated JSON). No agent dispatch.**

Produce the PM-team-readable catalog Markdown at `docs/streaming/event-catalog.md`.

**Required Markdown structure:**

```markdown
# {Service Name} — Streaming Event Catalog

**Generated:** {date}
**Source:** ring:streaming-event-mapping
**Lib-streaming version target:** v0.2.0+

---

## Overview

{1-paragraph plain-English summary derived from Pass 1's "Service Identity" section}

**Catalog stats:**
- Entry points inventoried: {summary.entry_points_inventoried}
- Segments analyzed: {summary.segments_identified}
- Candidates pre-fence: {summary.candidates_pre_scope_fence}
- Events accepted: {summary.events_after_scope_fence}

**Posture distribution:**
- CRITICAL: {summary.events_critical}
- IMPORTANT: {summary.events_important}
- OBSERVATIONAL: {summary.events_observational}
- CUSTOM: {summary.events_custom}

---

## Scope Fence

This catalog includes ONLY past-tense, durable, broadcastable, tenant-scoped business facts. The following types of signals were CONSIDERED but EXCLUDED:

| Excluded type | Reason | Where it belongs |
|--------------|--------|------------------|
| Internal commands | Not past-tense | lib-commons/v5/commons/rabbitmq |
| Cache invalidations | Not durable | Internal pub/sub |
| Saga step transitions | Not broadcastable | Saga internal state |
| Audit entries | Different consumer model | Audit pipeline |
| Synchronous responses | 1:1 by design | HTTP/gRPC |
| Health signals | Not tenant-scoped | OTEL |

If you expected an event in this catalog and it's not here, check Pass 2's rejection reasons in `docs/streaming/_pass2-segments.md`.

---

## Event Catalog

### CRITICAL Events

These events are atomic with the underlying state change. Loss is a correctness/compliance breach. Delivered via outbox pattern; consumer reconciliation is guaranteed.

| Catalog Key | Description | Aggregate | Payload Fields | Tenant Source | File:Anchor |
|-------------|-------------|-----------|---------------|---------------|-------------|
| {definition_key} | {description} | {resource_type} | {field count + key fields} | {tenant_source_at_site} | {file}:{line_anchor} |

### IMPORTANT Events

These events are direct-delivered in normal ops, with broker-outage fallback via outbox. Recoverable on hard failure via DLQ.

{same table format}

### OBSERVATIONAL Events

These events are best-effort. Loss is acceptable. Direct emission only.

{same table format}

### CUSTOM Events

These events have non-standard delivery requirements. Each row includes the rationale.

| Catalog Key | Description | Custom Policy | Rationale |
|-------------|-------------|---------------|-----------|
| {definition_key} | {description} | direct={direct}, outbox={outbox}, dlq={dlq} | {posture_rationale} |

---

## Detailed Event Specs

For each event, expanded form:

### {definition_key}

**Resource:** {resource_type}
**Event:** {event_type}
**Schema version:** {schema_version}
**Posture:** {posture}
**System event:** {is_system_event}

**Description:** {description}

**Payload sketch:**

```json
{payload_sketch}
```

**Instrumentation sites** ({count}):

1. `{file}` — {line_anchor}
   - Emission timing: {emission_timing}
   - Tenant source: {tenant_source_at_site}
   - Idempotency key candidate: {consumer_idempotency_key_candidate}

**Delivery policy:** direct={direct}, outbox={outbox}, dlq={dlq}

---

## Next Step

PM team validates this catalog. After approval, `docs/streaming/instrumentation-map.json` becomes the input to `ring:dev-streaming-instrumentation` (Skill #2), which wires lib-streaming into the codebase.

To proceed: review the table, confirm postures, flag any missing or misclassified events. The skill loops back to Pass 3 for any contested segment.
```

**Verification (orchestrator):**

- File `docs/streaming/event-catalog.md` exists
- All required sections present
- Every event in `instrumentation-map.json` is rendered in the catalog
- Posture distribution matches summary block

---

## Gate 6: PM Team Validation ⛔ NEVER SKIPPABLE

**Always executes. Cannot be skipped under any circumstance.**

Present the catalog to the PM team. Block until explicit approval.

**Orchestrator presents this checklist to the user (PM):**

```markdown
## Streaming Event Catalog — PM Validation

`docs/streaming/event-catalog.md` is ready for PM review. Before handoff to ring:dev-streaming-instrumentation:

- [ ] All expected events are present (cross-check against business roadmap)
- [ ] No unexpected events are present (scope fence is appropriate)
- [ ] Posture per event is correct (CRITICAL events are truly critical; OBSERVATIONAL events are truly best-effort)
- [ ] Payload sketches contain the right fields for client consumers
- [ ] Catalog keys match the naming convention the team wants externally
- [ ] PII fields are correctly annotated
- [ ] CUSTOM rationales are sound

**Please respond with one of:**

- `APPROVED` — proceed to Gate 7 handoff
- `REVISE: <segment>: <change request>` — loops back to Pass 3 for that segment with feedback
- `REVISE: posture <definition_key>: <new posture>` — single-event posture change
- `REVISE: scope-fence: <change request>` — broader fence rule change; re-runs Pass 2 + Pass 3
```

**Loop-back semantics:**

| Revision request | Loops back to |
|------------------|---------------|
| Per-segment content (add/remove events) | Pass 3 (Gate 3) for that segment only |
| Per-event posture change | Pass 3 with explicit posture override |
| Scope fence change | Pass 2 (Gate 2) + Pass 3 (Gate 3) |
| Catalog key naming convention change | Pass 3 (Gate 3) only — names are produced there |

<block_condition>
HARD GATE: PM approval is mandatory. The orchestrator MUST NOT proceed to Gate 7 without explicit `APPROVED` response. Silent inactivity = block.
</block_condition>

---

## Gate 7: Handoff Package

**Always executes. Orchestrator-direct.**

Produce the final handoff package and surface the next-step invocation.

**Outputs:**

1. `docs/streaming/event-catalog.md` (PM-validated, from Gate 5+6) — primary PM artifact
2. `docs/streaming/instrumentation-map.json` (validated, from Gate 4) — primary engineering artifact
3. `docs/streaming/_pass1-survey.md`, `_pass2-segments.md`, `_pass3-{segment}.json` — kept for audit; safe to delete after Skill #2 completes

**Handoff Markdown** (`docs/streaming/handoff-to-skill2.md`):

```markdown
# Handoff to ring:dev-streaming-instrumentation

The streaming event catalog has been validated by PM team on {date}.

**Inputs ready for Skill #2:**

- `docs/streaming/instrumentation-map.json` — canonical event definitions + delivery policies
- `docs/streaming/event-catalog.md` — human-readable catalog

**Catalog summary:**

- Service: {service_name}
- Events: {events_after_scope_fence} ({events_critical} CRITICAL, {events_important} IMPORTANT, {events_observational} OBSERVATIONAL, {events_custom} CUSTOM)
- Tenant source: {tenant_source}

**Outbox required:** {YES/NO based on whether any event has outbox != "never"}

- If YES: ring:dev-streaming-instrumentation will detect/install lib-commons/v5/commons/outbox.

**Next command:**

```text
Skill: ring:dev-streaming-instrumentation
```

The implementation skill will produce a visual preview at Gate 1.5 of its own cycle. Review and approve before any code changes.
```

---

## Output Format (final orchestrator report)

After all gates pass, the orchestrator emits:

```markdown
## Streaming Event Mapping Summary

- Service: {service_name}
- Total entry points inventoried: {entry_points_inventoried}
- Segments analyzed: {segments_identified}
- Candidates pre-fence: {candidates_pre_scope_fence}
- Events accepted: {events_after_scope_fence}
- PM validation: APPROVED on {date}
- Outbox required for Skill #2: {YES/NO}

## Stack Detection

{paste Gate 0 detection table}

## Pass Results

| Pass | Output | Status |
|------|--------|--------|
| Pass 1 — Survey | `docs/streaming/_pass1-survey.md` | PASS |
| Pass 2 — Slice | `docs/streaming/_pass2-segments.md` | PASS |
| Pass 3 — Mark ({N} segments parallel) | `docs/streaming/_pass3-*.json` | PASS |
| Catalog Assembly | `docs/streaming/instrumentation-map.json` | PASS |
| Business Rendering | `docs/streaming/event-catalog.md` | PASS |
| PM Validation | — | APPROVED |

## Catalog Output

| Posture | Count |
|---------|-------|
| CRITICAL | {events_critical} |
| IMPORTANT | {events_important} |
| OBSERVATIONAL | {events_observational} |
| CUSTOM | {events_custom} |

## Handoff to Skill #2

`docs/streaming/handoff-to-skill2.md` written. Invoke `ring:dev-streaming-instrumentation` to wire lib-streaming.
```

---

## State Persistence

Save to `docs/streaming/_state.json` for resume support:

```json
{
  "skill": "streaming-event-mapping",
  "service_name": "<from Gate 0>",
  "current_gate": 6,
  "gates": {
    "0": "PASS",
    "1": "PASS",
    "2": "PASS",
    "3": "PASS",
    "4": "PASS",
    "5": "PASS",
    "6": "PENDING_USER_APPROVAL",
    "7": "PENDING"
  },
  "metrics": {
    "entry_points_inventoried": 18,
    "segments_identified": 4,
    "candidates_pre_scope_fence": 27,
    "events_after_scope_fence": 14,
    "events_critical": 3,
    "events_important": 8,
    "events_observational": 2,
    "events_custom": 1
  }
}
```
