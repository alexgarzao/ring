---
name: ring:dev-multi-tenant
slug: dev-multi-tenant
version: 1.1.0
type: skill
description: |
  Multi-tenant development cycle orchestrator following Ring Standards.
  Auto-detects the service stack (PostgreSQL, MongoDB, Redis, RabbitMQ, S3),
  then executes a gate-based implementation using tenantId from JWT
  for database-per-tenant isolation via lib-commons v3 TenantConnectionManager.
  Each gate dispatches ring:backend-engineer-golang with context and section references.
  The agent loads multi-tenant.md via WebFetch and has all code examples.

trigger: |
  - User requests multi-tenant implementation for a Go service
  - User asks to add tenant isolation to an existing service
  - Task mentions "multi-tenant", "tenant isolation", "TenantConnectionManager"

prerequisite: |
  - Go service with existing single-tenant functionality

NOT_skip_when: |
  - "organization_id already exists" → organization_id is NOT multi-tenant. tenantId via JWT is required.
  - "Just need to connect the wiring" → Multi-tenant requires lib-commons v3 TenantConnectionManager.
  - "lib-commons v3 upgrade is too risky" → Multi-tenant REQUIRES v3. No v3 = no multi-tenant.

sequence:
  after: [ring:dev-devops]

related:
  complementary: [ring:dev-cycle, ring:dev-implementation, ring:dev-devops, ring:dev-unit-testing, ring:requesting-code-review, ring:dev-validation]

output_schema:
  format: markdown
  required_sections:
    - name: "Multi-Tenant Cycle Summary"
      pattern: "^## Multi-Tenant Cycle Summary"
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
    - name: total_files_changed
      type: integer

examples:
  - name: "Add multi-tenant to a service"
    invocation: "/ring:dev-multi-tenant"
    expected_flow: |
      1. Gate 0: Auto-detect stack
      2. Gate 1: Analyze codebase (build implementation roadmap)
      3. Gates 2-6: Implementation (agent loads multi-tenant.md, follows roadmap)
      4. Gate 7: Metrics & Backward compatibility
      5. Gate 8: Tests
      6. Gate 9: Code review
      7. Gate 10: User validation
      8. Gate 11: Activation guide
---

# Multi-Tenant Development Cycle

<cannot_skip>

## CRITICAL: This Skill ORCHESTRATES. Agents IMPLEMENT.

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Detect stack, determine gates, pass context to agent, verify outputs, enforce order |
| **ring:backend-engineer-golang** | Load multi-tenant.md via WebFetch, implement following the standards |
| **6 reviewers** | Review at Gate 9 |

**CANNOT change scope:** the skill defines WHAT to implement. The agent implements HOW.

**MANDATORY: TDD for all implementation gates (Gates 2-6).** MUST follow RED-GREEN: write a failing test first, then implement to make it pass. MUST include in every dispatch: "Follow TDD: write failing test (RED), then implement (GREEN)."

</cannot_skip>

---

## Multi-Tenant Architecture

Multi-tenant isolation is 100% based on `tenantId` from JWT → `TenantConnectionManager` → database-per-tenant. Each tenant has its own database. `organization_id` is NOT part of multi-tenant.

**Standards reference:** All code examples and implementation patterns are in [multi-tenant.md](../../docs/standards/golang/multi-tenant.md). MUST load via WebFetch before implementing any gate.

**WebFetch URL:** `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md`

### MANDATORY: Agent Instruction (include in EVERY gate dispatch)

MUST include these instructions in every dispatch to `ring:backend-engineer-golang`:

> **STANDARDS: WebFetch `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md` and follow the sections referenced below. All code examples, patterns, and implementation details are in that document. Use them as-is.**
>
> **TDD: For implementation gates (2-6), follow TDD methodology — write a failing test first (RED), then implement to make it pass (GREEN). MUST have test coverage for every change.**

---

## Pressure Resistance

| User Says | This Is | Response |
|-----------|---------|----------|
| "Skip the lib-commons upgrade" | QUALITY_BYPASS | "CANNOT proceed without lib-commons v3. TenantConnectionManager does not exist in v2." |
| "Just do the happy path, skip backward compat" | SCOPE_REDUCTION | "Backward compatibility is NON-NEGOTIABLE. Single-tenant deployments depend on it." |
| "organization_id is our tenant identifier" | AUTHORITY_OVERRIDE | "STOP. organization_id is NOT multi-tenant. tenantId from JWT is the only mechanism." |
| "Skip code review, we tested it" | QUALITY_BYPASS | "MANDATORY: 6 reviewers. One security mistake = cross-tenant data leak." |
| "We don't need RabbitMQ multi-tenant" | SCOPE_REDUCTION | "MUST execute Gate 6 if RabbitMQ was detected. CANNOT skip detected stack." |

---

## Gate Overview

| Gate | Name | Condition | Agent |
|------|------|-----------|-------|
| 0 | Stack Detection | Always | Orchestrator |
| 1 | Codebase Analysis (multi-tenant focus) | Always | ring:codebase-explorer |
| 2 | lib-commons v3 Upgrade | Skip if already v3 | ring:backend-engineer-golang |
| 3 | Multi-Tenant Configuration | Skip if already configured | ring:backend-engineer-golang |
| 4 | TenantMiddleware | Always (core) | ring:backend-engineer-golang |
| 5 | Repository Adaptation | Per detected DB/storage | ring:backend-engineer-golang |
| 6 | RabbitMQ Multi-Tenant | Skip if no RabbitMQ | ring:backend-engineer-golang |
| 7 | Metrics & Backward Compat | Always | ring:backend-engineer-golang |
| 8 | Tests | Always | ring:backend-engineer-golang |
| 9 | Code Review | Always | 6 parallel reviewers |
| 10 | User Validation | Always | User |
| 11 | Activation Guide | Always | Orchestrator |

MUST execute gates sequentially. CANNOT skip or reorder.

---

## Gate 0: Stack Detection

**Orchestrator executes directly. No agent dispatch.**

```text
DETECT (run in parallel):

1. lib-commons version:  grep "lib-commons" go.mod
2. PostgreSQL:           grep -rn "postgresql\|pgx\|squirrel" internal/ go.mod
3. MongoDB:              grep -rn "mongodb\|mongo" internal/ go.mod
4. Redis:                grep -rn "redis\|valkey" internal/ go.mod
5. RabbitMQ:             grep -rn "rabbitmq\|amqp" internal/ go.mod
6. S3/Object Storage:    grep -rn "s3\|ObjectStorage\|PutObject\|GetObject\|Upload.*storage\|Download.*storage" internal/ pkg/ go.mod
7. Existing multi-tenant:
   - Config:     grep -rn "MULTI_TENANT_ENABLED" internal/
   - Middleware: grep -rn "tenantmanager\|WithTenantDB" internal/
   - Context:    grep -rn "GetMongoForTenant\|GetPostgresForTenant" internal/
   - S3 keys:    grep -rn "GetObjectStorageKeyForTenant" internal/
   - RMQ:        grep -rn "X-Tenant-ID" internal/
```

MUST confirm: user explicitly approves detection results before proceeding.

---

## Gate 1: Codebase Analysis (Multi-Tenant Focus)

**Always executes. This gate builds the implementation roadmap for all subsequent gates.**

**Dispatch `ring:codebase-explorer` with multi-tenant-focused context:**

> TASK: Analyze this codebase exclusively under the multi-tenant perspective.
> DETECTED STACK: {databases and messaging from Gate 0}
>
> CRITICAL: Multi-tenant is ONLY about tenantId from JWT → TenantConnectionManager → database-per-tenant.
> IGNORE organization_id completely — it is NOT multi-tenant. A tenant can have multiple organizations inside its database. organization_id is a domain entity, not a tenant identifier.
>
> FOCUS AREAS (explore ONLY these — ignore everything else):
>
> 1. **Service name, modules, and components**: What is the service called? (Look for `const ApplicationName`.) How many components/modules does it have? Each module needs a constant (e.g., `const ModuleManager = "manager"`). Identify: service name (ApplicationName), module names per component, and whether constants exist or need to be created. Hierarchy: Service → Module → Resource.
> 2. **Bootstrap/initialization**: Where does the service start? Where are database connections created? Where is the middleware chain registered? Identify the exact insertion point for TenantMiddleware.
> 3. **Database connections**: How do repositories get their DB connection today? Static field in struct? Constructor injection? Context? List EVERY repository file with file:line showing where the connection is obtained.
> 4. **Middleware chain**: What middleware exists and in what order? Where would TenantMiddleware fit (after auth, before handlers)?
> 5. **Config struct**: Where is the Config struct? What fields exist? Where is it loaded? Identify exact location for MULTI_TENANT_ENABLED vars.
> 6. **RabbitMQ** (if detected): Where are producers? Where are consumers? How are messages published? Where would X-Tenant-ID header be injected? Are producer and consumer in the SAME process or SEPARATE components? Is there already a config split? Are there dual constructors? Is there a RabbitMQManager pool? Does the service struct have both consumer types?
> 7. **Redis** (if detected): Where are Redis operations? Any Lua scripts? Where would GetKeyFromContext be needed?
> 8. **S3/Object Storage** (if detected): Where are Upload/Download/Delete operations? How are object keys constructed? List every file:line that builds an S3 key. What bucket env var is used?
> 9. **Existing multi-tenant code**: Any tenantmanager imports? TenantMiddleware? GetPostgresForTenant/GetMongoForTenant/GetObjectStorageKeyForTenant calls? MULTI_TENANT_ENABLED config? (NOTE: organization_id is NOT related to multi-tenant — ignore it completely)
>
> OUTPUT FORMAT: Structured report with file:line references for every point above.
> DO NOT write code. Analysis only.

**The explorer produces a gap summary.** For the full checklist of required items, see [multi-tenant.md § Checklist](../../docs/standards/golang/multi-tenant.md).

**This report becomes the CONTEXT for all subsequent gates.**

<block_condition>
HARD GATE: MUST complete the analysis report before proceeding. All subsequent gates use this report to know exactly what to change.
</block_condition>

MUST ensure backward compatibility context: the analysis MUST identify how the service works today in single-tenant mode, so subsequent gates preserve this behavior when `MULTI_TENANT_ENABLED=false`.

---

## Gate 2: lib-commons v3 Upgrade

**SKIP IF:** already v3.

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Upgrade lib-commons from v2 to v3. Update go.mod and all import paths.
> Follow multi-tenant.md section "Required lib-commons Version".
> DO NOT implement multi-tenant code yet — only upgrade the dependency.
> Verify: go build ./... and go test ./... MUST pass.

**Verification:** `grep "lib-commons/v3" go.mod` + `go build ./...` + `go test ./...`

<block_condition>
HARD GATE: MUST pass build and tests before proceeding.
</block_condition>

---

## Gate 3: Multi-Tenant Configuration

**SKIP IF:** config already has `MULTI_TENANT_ENABLED`.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Add multi-tenant environment variables to the Config struct.
> CONTEXT FROM GATE 1: {Config struct location and current fields from analysis report}
> Follow multi-tenant.md sections "Environment Variables", "Configuration", and "Conditional Initialization".
> Add conditional log: "Multi-tenant mode enabled" vs "Running in SINGLE-TENANT MODE".
> DO NOT implement TenantMiddleware yet — only configuration.

**Verification:** `grep "MULTI_TENANT_ENABLED" internal/bootstrap/config.go` + `go build ./...`

---

## Gate 4: TenantMiddleware (Core)

**SKIP IF:** middleware already exists.

**This is the CORE gate. Without TenantMiddleware, there is no tenant isolation.**

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Implement TenantMiddleware using lib-commons/v3 tenant-manager package.
> DETECTED DATABASES: {postgresql: Y/N, mongodb: Y/N} (from Gate 0)
> CONTEXT FROM GATE 1: {Bootstrap location, middleware chain insertion point, service init from analysis report}
>
> CRITICAL — HIERARCHY: Service → Module → Resource.
> See [multi-tenant.md § Generic TenantMiddleware](../../docs/standards/golang/multi-tenant.md) for the full middleware pattern.
> See [multi-tenant.md § Conditional Initialization](../../docs/standards/golang/multi-tenant.md) for the bootstrap pattern.
>
> MUST define constants for service name and module names — never pass raw strings.
> The first parameter to NewPostgresManager/NewMongoManager is the SERVICE (ApplicationName).
> WithModule/WithMongoModule receives the MODULE (component name).
> See multi-tenant.md § "JWT Tenant Extraction" for tenantId claim handling.
>
> Create connection managers ONLY for detected databases.
> Public endpoints (/health, /version, /swagger) MUST bypass tenant middleware.
>
> CRITICAL: tenantId comes from JWT, NOT from URL path parameters.
> When MULTI_TENANT_ENABLED=false, middleware calls c.Next() immediately (single-tenant passthrough).
>
> **IF RabbitMQ DETECTED:** MUST accept an optional ConsumerTrigger parameter.
> See [multi-tenant.md § ConsumerTrigger Interface](../../docs/standards/golang/multi-tenant.md) for the wiring pattern.

**Verification:** `grep "tenantmanager.NewTenantMiddleware" internal/bootstrap/` + `go build ./...`

<block_condition>
HARD GATE: CANNOT proceed without TenantMiddleware.
</block_condition>

---

## Gate 5: Repository Adaptation

**SKIP IF:** repositories already use context-based connections.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Adapt all repository implementations to get database connections from tenant context instead of static connections. Also adapt S3/object storage operations to prefix keys with tenant ID.
> DETECTED STACK: {postgresql: Y/N, mongodb: Y/N, redis: Y/N, s3: Y/N} (from Gate 0)
> CONTEXT FROM GATE 1: {List of ALL repository files and storage operations with file:line from analysis report}
>
> Follow multi-tenant.md sections:
> - "Database Connection in Repositories" (PostgreSQL)
> - "MongoDB Multi-Tenant Repository" (MongoDB)
> - "Redis Key Prefixing" and "Redis Key Prefixing for Lua Scripts" (Redis)
> - "S3/Object Storage Key Prefixing" (S3)
>
> MUST work in both modes: multi-tenant (prefixed keys / context connections) and single-tenant (unchanged keys / default connections).

**Verification:** grep for `GetPostgresForTenant` / `GetMongoForTenant` / `GetKeyFromContext` / `GetObjectStorageKeyForTenant` in `internal/` + `go build ./...`

---

## Gate 6: RabbitMQ Multi-Tenant

**SKIP IF:** no RabbitMQ detected.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Implement RabbitMQ multi-tenant patterns with lazy initialization.
> CONTEXT FROM GATE 1: {Producer and consumer file:line locations from analysis report}
> DETECTED ARCHITECTURE: {Are producer and consumer in the same process or separate components?}
>
> Follow multi-tenant.md sections:
> - "RabbitMQ Multi-Tenant Producer" for dual constructor and X-Tenant-ID header
> - "Multi-Tenant Message Queue Consumers (Lazy Mode)" for lazy initialization
> - "ConsumerTrigger Interface" for the trigger wiring
>
> Gate-specific constraints:
> 1. CONFIG SPLIT (MANDATORY): Branch on `cfg.IsMultiTenant()` for both producer and consumer in bootstrap
> 2. MUST keep the existing single-tenant code path untouched
> 3. MUST NOT connect directly to RabbitMQ at startup in multi-tenant mode
> 4. X-Tenant-ID goes in AMQP headers, NOT in message body

**Verification:** `grep "RabbitMQManager\|NewProducerMultiTenant\|EnsureConsumerStarted\|ConsumerTrigger" internal/` + `go build ./...`

<block_condition>
HARD GATE: MUST NOT connect directly to RabbitMQ at startup in multi-tenant mode.
</block_condition>

---

## Gate 7: Metrics & Backward Compatibility

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Add multi-tenant metrics and validate backward compatibility.
>
> Follow multi-tenant.md sections "Multi-Tenant Metrics" and "Single-Tenant Backward Compatibility Validation (MANDATORY)".
>
> BACKWARD COMPATIBILITY IS NON-NEGOTIABLE:
> - MUST start without any MULTI_TENANT_* env vars
> - MUST start without Tenant Manager running
> - MUST pass all existing tests with MULTI_TENANT_ENABLED=false
> - Health/version endpoints MUST work without tenant context
>
> Write TestMultiTenant_BackwardCompatibility integration test.

**Verification:** `MULTI_TENANT_ENABLED=false go test ./...` MUST pass.

<block_condition>
HARD GATE: Backward compatibility MUST pass.
</block_condition>

---

## Gate 8: Tests

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Write multi-tenant tests.
> DETECTED STACK: {postgresql: Y/N, mongodb: Y/N, redis: Y/N, s3: Y/N, rabbitmq: Y/N} (from Gate 0)
>
> Follow multi-tenant.md section "Testing Multi-Tenant Code" (all subsections).
>
> Required tests: unit tests with mock tenant context, tenant isolation tests (two tenants, data separation), error case tests (missing JWT, tenant not found), plus RabbitMQ, Redis, and S3 tests if detected.

**Verification:** `go test ./... -v -count=1` + `go test ./... -cover`

---

## Gate 9: Code Review

**Dispatch 6 parallel reviewers (same pattern as ring:requesting-code-review).**

MUST include this context in ALL 6 reviewer dispatches:

> **MULTI-TENANT REVIEW CONTEXT:**
> - Multi-tenant isolation is based on `tenantId` from JWT → `TenantConnectionManager` → database-per-tenant.
> - `organization_id` is NOT a tenant identifier. It is a business filter within the tenant's database. A single tenant can have multiple organizations. Do NOT flag organization_id as a multi-tenant issue.
> - Backward compatibility is required: when `MULTI_TENANT_ENABLED=false`, the service MUST work exactly as before (single-tenant mode, no tenant context needed).

| Reviewer | Focus |
|----------|-------|
| ring:code-reviewer | Architecture, lib-commons v3 usage, TenantMiddleware placement |
| ring:business-logic-reviewer | Tenant context propagation via tenantId (NOT organization_id) |
| ring:security-reviewer | Cross-tenant DB isolation, JWT tenantId validation, no data leaks between tenant databases |
| ring:test-reviewer | Coverage, isolation tests between two tenants, backward compat tests |
| ring:nil-safety-reviewer | Nil risks in tenant context extraction from JWT and context getters |
| ring:consequences-reviewer | Impact on single-tenant paths, backward compat when MULTI_TENANT_ENABLED=false |

MUST pass all 6 reviewers. Critical findings → fix and re-review.

---

## Gate 10: User Validation

MUST approve: present checklist for explicit user approval.

```markdown
## Multi-Tenant Implementation Complete

- [ ] lib-commons v3
- [ ] MULTI_TENANT_ENABLED config
- [ ] TenantMiddleware (JWT tenantId → DB routing)
- [ ] Repositories use context-based connections
- [ ] S3 keys prefixed with tenantId (if applicable)
- [ ] RabbitMQ X-Tenant-ID (if applicable)
- [ ] Backward compat (MULTI_TENANT_ENABLED=false works)
- [ ] Tests pass
- [ ] Code review passed
```

---

## Gate 11: Activation Guide

**MUST generate `docs/multi-tenant-guide.md` in the project root.** Direct, concise, no filler text.

The file is built from Gate 0 (stack) and Gate 1 (analysis). See [multi-tenant.md § Checklist](../../docs/standards/golang/multi-tenant.md) for the canonical env var list and requirements.

<!-- Template: values filled from Gate 0/1 results. Canonical source: multi-tenant.md -->

The guide MUST include:
1. **Components table**: Component name, Service const, Module const, Resources, what was adapted
2. **Environment variables**: the 7 MULTI_TENANT_* vars with required/default/description
3. **How to activate**: set envs + start alongside Tenant Manager
4. **How to verify**: check logs, test with JWT tenantId
5. **How to deactivate**: set MULTI_TENANT_ENABLED=false
6. **Common errors**: see [multi-tenant.md § Error Handling](../../docs/standards/golang/multi-tenant.md)

---

## State Persistence

Save to `docs/ring-dev-multi-tenant/current-cycle.json` for resume support:

```json
{
  "cycle": "multi-tenant",
  "stack": {"postgresql": false, "mongodb": true, "redis": true, "rabbitmq": true, "s3": true},
  "gates": {"0": "PASS", "1": "PASS", "2": "IN_PROGRESS", "3": "PENDING"},
  "current_gate": 2
}
```

---

## Anti-Rationalization Table

See [multi-tenant.md](../../docs/standards/golang/multi-tenant.md) for the canonical anti-rationalization tables on tenantId vs organization_id.

**Skill-specific rationalizations:**

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Agent says out of scope" | Skill defines scope, not agent. | **Re-dispatch with gate context** |
| "Skip tests" | Gate 8 proves isolation works. | **MANDATORY** |
| "Skip review" | Security implications. One mistake = data leak. | **MANDATORY** |
