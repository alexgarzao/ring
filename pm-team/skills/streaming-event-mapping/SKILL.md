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
  surviving), OBSERVATIONAL (best-effort) — plus CUSTOM with mandatory written justification.

trigger: |
  - User requests an event catalog, eventable-point inventory, or "where should we emit events" map
  - PM team prepares a Lerian Go service for client-facing event streaming subscriptions
  - Pre-flight to ring:dev-streaming-instrumentation
  - Task mentions "event mapping", "streaming inventory", "eventable points", "client event subscription"

skip_when: |
  - Service is not a Go project (lib-streaming is Go-only)
  - Service has no business logic to emit events about (pure infrastructure, gateway, sidecar, proxy)
  - Task is purely documentation, configuration, or non-discovery
  - Service is consumer-only with no outbound business event surface

prerequisites: |
  - Go service codebase available for read access
  - At least one entry point present (HTTP route, gRPC method, RabbitMQ consumer, scheduled job, webhook)
  - Tenant identity resolvable from request context

sequence:
  before: [ring:dev-streaming-instrumentation]

related:
  complementary: [ring:dev-streaming-instrumentation, ring:codebase-explorer, ring:pre-dev-feature-map]
---

# Streaming Event Mapping (lib-streaming, PM-team)

Orchestrates 3-pass codebase discovery to produce an event catalog and instrumentation map for lib-streaming. You orchestrate. Agents explore. You NEVER read, write, or edit source code directly.

**Announce at start:** "Using ring:streaming-event-mapping through 7 gates (0-7)."

## Streaming Architecture

lib-streaming is a producer-only, write-only event-emission library for Lerian Go services. Events are emitted via `emitter.Emit(ctx, EmitRequest{DefinitionKey, TenantID, Subject, Payload})` against the `streaming.Emitter` interface (constructed via `streaming.NewBuilder().Catalog(...).Build(ctx)`). Wire format: CloudEvents 1.0 binary mode. Each `RouteDefinition` selects a transport — Kafka, SQS, RabbitMQ, EventBridge, or Custom. Per-tenant SaaS subscription remains the primary delivery model regardless of transport; Kafka topic naming is `lerian.streaming.<resource>.<event>[.vN]` with tenant carried on the `ce-tenantid` CloudEvents header.

**WebFetch canonical docs:** `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/doc.go`
**WebFetch agent constraints:** `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/AGENTS.md`
**WebFetch changelog:** `https://raw.githubusercontent.com/LerianStudio/lib-streaming/main/CHANGELOG.md`

## Scope Fence

A candidate is a **streamable business fact** if and ONLY if ALL of:
1. **Past-tense** — something that already happened (`account.created`, not `account.create`)
2. **Durable** — the underlying state is persisted
3. **Broadcastable** — multiple consumers could legitimately receive it
4. **Tenant-scoped** — the event belongs to a tenant (or marked SystemEvent with explicit justification)

Candidates failing ANY of the four → REJECT with documented reason.

## Delivery Postures

| Posture | Direct | Outbox | DLQ | Use when |
|---------|--------|--------|-----|----------|
| CRITICAL | skip | always | on_routable_failure | Loss is correctness/compliance breach; atomic with DB write |
| IMPORTANT | direct | fallback_on_circuit_open | on_routable_failure | Direct in normal ops; survives broker outage |
| OBSERVATIONAL | direct | never | never | Analytics-grade; loss acceptable |
| CUSTOM | per-event | per-event | per-event | None above fits — requires ≥80 char justification |

## Gate Overview

| Gate | Name | Agent | Always? |
|------|------|-------|---------|
| 0 | Stack Detection | Orchestrator (grep + read) | Yes |
| 1 | Pass 1 — Survey | ring:codebase-explorer (single) | Yes |
| 2 | Pass 2 — Slice + Scope Fence | ring:codebase-explorer (single) | Yes |
| 3 | Pass 3 — Mark | ring:codebase-explorer (parallel, 1/segment) | Yes |
| 4 | Catalog Assembly + Validation | Orchestrator (deterministic) | Yes |
| 5 | Business Rendering | Orchestrator | Yes |
| 6 | PM Team Validation | User (PM team) — NEVER SKIPPABLE | Yes |
| 7 | Handoff Package | Orchestrator | Yes |

Gates execute sequentially. Pass 3 (Gate 3) parallelizes internally per segment.

## Gate 0: Stack Detection

Orchestrator executes directly. Detect in parallel:

```
1. Go version:          grep "^go " go.mod | head -1
2. lib-streaming:       grep "lib-streaming" go.mod
3. HTTP framework:      grep -rn "gofiber/fiber\|labstack/echo\|gin-gonic" internal/ go.mod
4. gRPC server:         grep -rn "grpc.NewServer" internal/
5. RabbitMQ consumers:  grep -rn "lib-commons/v5/commons/rabbitmq" internal/
6. Scheduled jobs:      grep -rn "robfig/cron\|time.NewTicker" internal/
7. Webhook receivers:   grep -rn "webhook\|/hooks/" internal/
8. Worker patterns:     grep -rn "commons.Launcher\|commons.App" internal/
9. Tenant source:       grep -rn "tmcore.GetTenantIDContext\|GetTenantID" internal/
10. DDD layout:         ls internal/services/ internal/domain/ 2>/dev/null
11. Database:           grep -rn "jackc/pgx\|database/sql" go.mod
```

**HARD GATE:** If not Go → STOP. If tenant source undetectable → STOP and ask user.

## Gate 1: Pass 1 — Survey

Dispatch `ring:codebase-explorer` to produce `docs/streaming/_pass1-survey.md` with:
- Service Identity (name, purpose, bounded context)
- Entry Point Inventory (HTTP routes, gRPC methods, RabbitMQ consumers, cron jobs, webhooks, CLIs)
- Aggregate Inventory (name, persistence, lifecycle states)
- Tenant Identity Resolution (idiomatic call, where set, reliability per entry type)
- External Dependencies (databases, APIs, brokers)
- Notes for Pass 2

Include in dispatch: stack detection results, lib-streaming WebFetch URLs, constraint to NOT propose events.

**Verification:** File exists, all 6 sections present, ≥1 entry point, ≥1 aggregate, tenant source identified.

## Gate 2: Pass 2 — Slice + Scope Fence

Dispatch `ring:codebase-explorer` with Pass 1 output to produce `docs/streaming/_pass2-segments.md` with:
- Segmentation Strategy (by domain module, aggregate, or entry-point type)
- Segments (3-8): files glob, aggregates touched, commit boundaries, pre/post-fence candidate counts
- Scope Fence Application table (file:line, candidate, 4-test scoring, verdict)
- Pass 3 Dispatch Plan (segments with accepted candidates + sub-prompt hints)

**Verification:** File exists, ≥1 segment, fence table covers all candidates, ≥1 accepted candidate.

**HARD GATE:** If post-fence count = 0 across all segments → STOP and surface to user.

## Gate 3: Pass 3 — Mark (Parallel)

For EACH segment from Gate 2, dispatch `ring:codebase-explorer` IN PARALLEL. Each outputs `docs/streaming/_pass3-{segment_name}.json`.

Per-segment JSON shape:
```json
{
  "segment": "{segment_name}",
  "events": [{
    "definition_key": "transaction.posted",
    "resource_type": "transaction",
    "event_type": "posted",
    "schema_version": "1.0.0",
    "data_content_type": "application/json",
    "data_schema": "",
    "is_system_event": false,
    "description": "...",
    "instrumentation_sites": [{"file": "...", "line_anchor": "...", "emission_timing": "post-commit", "current_function": "..."}],
    "payload_sketch": {"field_name": "type"},
    "tenant_source_at_site": "tmcore.GetTenantIDContext(ctx)",
    "consumer_idempotency_key_candidate": "event_id",
    "posture": "CRITICAL",
    "posture_rationale": "...",
    "delivery_policy": {"enabled": true, "direct": "skip", "outbox": "always", "dlq": "on_routable_failure"}
  }]
}
```

Include in every dispatch: lib-streaming WebFetch URLs, scope fence rules, posture decision tree, naming convention (`<resource>.<event>` lowercase dotted).

**Verification:** One JSON file per segment, valid JSON, all required fields populated, no null/TBD, CUSTOM posture has ≥80 char rationale.

**HARD GATE:** Missing/malformed file → re-dispatch ONLY failing segments.

## Gate 4: Catalog Assembly + Validation

Orchestrator merges all `_pass3-*.json` events into `docs/streaming/instrumentation-map.json`. Validate:
- `definition_key` unique, matches `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`
- `(resource_type, event_type, schema_version)` triple unique
- Non-system events have `tenant_source_at_site` non-empty
- `description` ≥40 chars, `payload_sketch` ≥1 field
- Delivery policy matches canonical posture mapping for non-CUSTOM
- CUSTOM has `posture_rationale` ≥80 chars
- `delivery_policy.enabled` present and boolean (typically `true`); `direct ∈ {"direct","skip"}`, `outbox ∈ {"never","fallback_on_circuit_open","always"}`, `dlq ∈ {"never","on_routable_failure"}` — these are the lib-streaming mode strings the dev skill will emit verbatim

Validation failures → re-dispatch failing segment's Pass 3 with correction notes. Do NOT manually edit JSON.

## Gate 5: Business Rendering

Orchestrator generates `docs/streaming/event-catalog.md` from validated JSON. Required sections:
- Overview (service summary, catalog stats, posture distribution)
- Scope Fence (excluded types table)
- Event Catalog (grouped by posture: CRITICAL, IMPORTANT, OBSERVATIONAL, CUSTOM)
- Detailed Event Specs (one section per event with payload sketch, instrumentation sites, delivery policy)
- Next Step (PM validation instructions)

## Gate 6: PM Team Validation — NEVER SKIPPABLE

Present checklist to PM team:
- All expected events present
- No unexpected events
- Posture per event correct
- Payload sketches contain right fields
- Catalog keys match desired naming convention
- PII fields correctly annotated
- CUSTOM rationales are sound

**Response options:**
- `APPROVED` → proceed to Gate 7
- `REVISE: <segment>: <change>` → loops back to Pass 3 for that segment
- `REVISE: posture <key>: <new posture>` → single-event posture change
- `REVISE: scope-fence: <change>` → re-runs Pass 2 + Pass 3

**HARD GATE:** Must not proceed to Gate 7 without explicit `APPROVED`.

## Gate 7: Handoff Package

Produce `docs/streaming/handoff-to-skill2.md` summarizing:
- PM validation date
- Inputs ready for Skill #2 (instrumentation-map.json, event-catalog.md)
- Catalog summary (service, event counts by posture)
- Outbox required flag
- Next command: `Skill: ring:dev-streaming-instrumentation`

## State Persistence

Save to `docs/streaming/_state.json`:
```json
{
  "skill": "streaming-event-mapping",
  "service_name": "<from Gate 0>",
  "current_gate": 0,
  "gates": {"0": "PENDING", "1": "PENDING", "2": "PENDING", "3": "PENDING", "4": "PENDING", "5": "PENDING", "6": "PENDING_USER_APPROVAL", "7": "PENDING"},
  "metrics": {"entry_points_inventoried": 0, "segments_identified": 0, "candidates_pre_scope_fence": 0, "events_after_scope_fence": 0, "events_critical": 0, "events_important": 0, "events_observational": 0, "events_custom": 0}
}
```
