---
name: ring:dev-multi-tenant
version: 1.0.0
type: skill
description: |
  Multi-tenant development cycle orchestrator following Ring Standards.
  Auto-detects the service stack (PostgreSQL, MongoDB, Redis, RabbitMQ),
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
      4. Gate 7: Backward compatibility
      5. Gate 8: Tests
      6. Gate 9: Code review
      7. Gate 10: User validation
---

# Multi-Tenant Development Cycle

<cannot_skip>

## CRITICAL: This Skill ORCHESTRATES. Agents IMPLEMENT.

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Detect stack, determine gates, pass context to agent, verify outputs, enforce order |
| **ring:backend-engineer-golang** | Load multi-tenant.md via WebFetch, implement following the standards |
| **6 reviewers** | Review at Gate 8 |

**⛔ The skill defines WHAT to implement. The agent loads the standards and implements HOW.**

**⛔ TDD is MANDATORY for all implementation gates (Gates 2-6).** The agent MUST follow RED-GREEN: write a failing test first, then implement to make it pass. Every dispatch to the agent for implementation gates MUST include: "Follow TDD: write failing test (RED), then implement (GREEN)."

</cannot_skip>

---

## How Multi-Tenant Works

Multi-tenant isolation is 100% based on `tenantId` from JWT → `TenantConnectionManager` → database-per-tenant. Each tenant has its own database. `organization_id` is NOT part of multi-tenant.

**Standards reference:** All code examples and implementation patterns are in `multi-tenant.md`. The agent MUST load this via WebFetch before implementing any gate.

**WebFetch URL:** `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md`

### MANDATORY Agent Instruction (include in EVERY gate dispatch)

Every dispatch to `ring:backend-engineer-golang` MUST include these instructions:

> **STANDARDS: WebFetch `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md` and follow the sections referenced below. All code examples, patterns, and implementation details are in that document. Use them as-is.**
>
> **TDD: For implementation gates (2-6), follow TDD methodology — write a failing test first (RED), then implement to make it pass (GREEN). Every change MUST have test coverage.**

This ensures the agent loads the standards first, uses canonical code examples, and follows TDD for all implementation work.

---

## Gate Overview

| Gate | Name | Condition | Agent |
|------|------|-----------|-------|
| 0 | Stack Detection | Always | Orchestrator |
| 1 | Codebase Analysis | Always | ring:backend-engineer-golang |
| 2 | lib-commons v3 Upgrade | Skip if already v3 | ring:backend-engineer-golang |
| 3 | Multi-Tenant Configuration | Skip if already configured | ring:backend-engineer-golang |
| 4 | TenantMiddleware | Always (core) | ring:backend-engineer-golang |
| 5 | Repository Adaptation | Per detected DB | ring:backend-engineer-golang |
| 6 | RabbitMQ Tenant Headers | Skip if no RabbitMQ | ring:backend-engineer-golang |
| 7 | Metrics & Backward Compat | Always | ring:backend-engineer-golang |
| 8 | Tests | Always | ring:backend-engineer-golang |
| 9 | Code Review | Always | 6 parallel reviewers |
| 10 | User Validation | Always | User |

**⛔ Gates are SEQUENTIAL. No skipping. No reordering.**

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
6. Existing multi-tenant:
   - Config:     grep -rn "MULTI_TENANT_ENABLED" internal/
   - Middleware: grep -rn "tenantmanager\|WithTenantDB" internal/
   - Context:    grep -rn "GetMongoForTenant\|GetPostgresForTenant" internal/
   - RMQ:        grep -rn "X-Tenant-ID" internal/
```

**Present results to user. User MUST confirm before proceeding.**

---

## Gate 1: Codebase Analysis

**Always executes. This gate builds the implementation roadmap for all subsequent gates.**

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Analyze the current codebase to understand what needs to change for multi-tenant support.
> DETECTED STACK: {from Gate 0}
>
> STANDARDS: WebFetch `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md` and read ALL sections. This document defines the target state.
>
> ANALYZE and report:
> 1. **Bootstrap/initialization**: How does the service start? Where are DB connections created? Where is middleware registered?
> 2. **Repositories**: List ALL repository files. How do they get their DB connection today (static field, constructor injection, context)?
> 3. **Middleware chain**: What middleware exists? Where would TenantMiddleware be inserted?
> 4. **RabbitMQ** (if detected): How are producers and consumers wired? Where are messages published?
> 5. **Redis** (if detected): Where are Redis operations? Any Lua scripts?
> 6. **Config struct**: What fields exist? Where is the config loaded?
> 7. **Gap analysis**: For each section of multi-tenant.md, what exists today vs what needs to be added?
>
> OUTPUT: A structured report with file paths and line numbers for every change needed across Gates 2-8.
> DO NOT write any code. Analysis only.

**Output format:**

```markdown
## Codebase Analysis for Multi-Tenant

### Bootstrap
- Config: {file:line} — needs MULTI_TENANT_ENABLED vars
- Initialization: {file:line} — TenantMiddleware registration point
- Middleware chain: {file:line} — insertion order

### Repositories ({N} files)
- {file:line} — uses static connection, needs GetPostgresForTenant(ctx) / GetMongoForTenant(ctx)
- {file:line} — ...

### RabbitMQ (if applicable)
- Producer: {file:line} — needs X-Tenant-ID header
- Consumer: {file:line} — needs tenant context injection

### Redis (if applicable)
- {file:line} — needs GetKeyFromContext(ctx, key)

### Gap Summary
| multi-tenant.md Section | Current State | Action Needed |
|------------------------|---------------|---------------|
| Environment Variables | Missing | Add to config |
| TenantMiddleware | Missing | Implement in bootstrap |
| Repository Adaptation | Static connections | Use context getters |
| ... | ... | ... |
```

**⛔ HARD GATE: The analysis report MUST be complete before proceeding. All subsequent gates use this report to know exactly what to change.**

---

## Gate 2: lib-commons v3 Upgrade

**SKIP IF:** already v3.

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Upgrade lib-commons from v2 to v3. Update go.mod and all import paths.
> Follow multi-tenant.md section "Required lib-commons Version".
> DO NOT implement multi-tenant code yet — only upgrade the dependency.
> Verify: go build ./... and go test ./... MUST pass.

**Verification:** `grep "lib-commons/v3" go.mod` + `go build ./...` + `go test ./...`

**⛔ HARD GATE: Build and tests MUST pass.**

---

## Gate 3: Multi-Tenant Configuration

**SKIP IF:** config already has `MULTI_TENANT_ENABLED`.

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Add multi-tenant environment variables to the Config struct.
> Follow multi-tenant.md sections "Environment Variables", "Configuration", and "Conditional Initialization".
> Add conditional log: "Multi-tenant mode enabled" vs "Running in SINGLE-TENANT MODE".
> DO NOT implement TenantMiddleware yet — only configuration.

**Verification:** `grep "MULTI_TENANT_ENABLED" internal/bootstrap/config.go` + `go build ./...`

---

## Gate 4: TenantMiddleware (Core)

**SKIP IF:** middleware already exists.

**This is the CORE gate. Without TenantMiddleware, there is no tenant isolation.**

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Implement TenantMiddleware using lib-commons/v3 tenant-manager package.
> DETECTED DATABASES: {postgresql: Y/N, mongodb: Y/N} (from Gate 0)
>
> Follow multi-tenant.md sections "Generic TenantMiddleware", "JWT Tenant Extraction", and "Conditional Initialization".
> Create connection managers ONLY for detected databases.
> Public endpoints (/health, /version, /swagger) MUST bypass tenant middleware.
>
> CRITICAL: tenantId comes from JWT, NOT from URL path parameters.
> The middleware resolves which DATABASE to connect to.
> When MULTI_TENANT_ENABLED=false, middleware calls c.Next() immediately (single-tenant passthrough).

**Verification:** `grep "tenantmanager.NewTenantMiddleware" internal/bootstrap/` + `go build ./...`

**⛔ HARD GATE: Cannot proceed without TenantMiddleware.**

---

## Gate 5: Repository Adaptation

**SKIP IF:** repositories already use context-based connections.

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Adapt all repository implementations to get database connections from tenant context instead of static connections.
> DETECTED DATABASES: {postgresql: Y/N, mongodb: Y/N, redis: Y/N} (from Gate 0)
>
> Follow multi-tenant.md sections:
> - "Database Connection in Repositories" (PostgreSQL)
> - "MongoDB Multi-Tenant Repository" (MongoDB)
> - "Redis Key Prefixing" and "Redis Key Prefixing for Lua Scripts" (Redis)
>
> Repositories MUST work in both modes: multi-tenant (connection from context) and single-tenant (default connection via passthrough).

**Verification:** grep for `GetPostgresForTenant` / `GetMongoForTenant` / `GetKeyFromContext` in `internal/adapters/` + `go build ./...`

---

## Gate 6: RabbitMQ Multi-Tenant

**SKIP IF:** no RabbitMQ detected.

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Implement RabbitMQ multi-tenant patterns.
>
> Follow multi-tenant.md sections "RabbitMQ Multi-Tenant Producer", "Multi-Tenant Message Queue Consumers (Lazy Mode)", and "ConsumerTrigger Interface".
>
> Key points: X-Tenant-ID AMQP header (NOT in message body), per-tenant channels, lazy consumer initialization, ConsumerTrigger wired to middleware.

**Verification:** `grep "X-Tenant-ID" internal/adapters/` + `go build ./...`

---

## Gate 7: Metrics & Backward Compatibility

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Add multi-tenant metrics and validate backward compatibility.
>
> Follow multi-tenant.md sections "Multi-Tenant Metrics" and "Single-Tenant Backward Compatibility Validation (MANDATORY)".
>
> BACKWARD COMPATIBILITY IS NON-NEGOTIABLE:
> - Service MUST start without any MULTI_TENANT_* env vars
> - Service MUST start without Tenant Manager running
> - All existing tests MUST pass with MULTI_TENANT_ENABLED=false
> - Health/version endpoints MUST work without tenant context
>
> Write TestMultiTenant_BackwardCompatibility integration test.

**Verification:** `MULTI_TENANT_ENABLED=false go test ./...` MUST pass.

**⛔ HARD GATE: Backward compatibility MUST pass.**

---

## Gate 8: Tests

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Write multi-tenant tests.
> DETECTED STACK: {postgresql: Y/N, mongodb: Y/N, redis: Y/N, rabbitmq: Y/N} (from Gate 0)
>
> Follow multi-tenant.md section "Testing Multi-Tenant Code" (all subsections).
>
> Required tests: unit tests with mock tenant context, tenant isolation tests (two tenants, data separation), error case tests (missing JWT, tenant not found), plus RabbitMQ and Redis tests if detected.

**Verification:** `go test ./... -v -count=1` + `go test ./... -cover`

---

## Gate 9: Code Review

**Dispatch 6 parallel reviewers (same pattern as ring:requesting-code-review):**

| Reviewer | Focus |
|----------|-------|
| ring:code-reviewer | Architecture, lib-commons v3 usage |
| ring:business-logic-reviewer | Tenant context propagation |
| ring:security-reviewer | Cross-tenant isolation, JWT validation |
| ring:test-reviewer | Coverage, isolation tests |
| ring:nil-safety-reviewer | Nil risks in context extraction |
| ring:consequences-reviewer | Impact on single-tenant paths |

**All 6 MUST pass. Critical findings → fix and re-review.**

---

## Gate 10: User Validation

**Present checklist. User MUST approve.**

```markdown
## Multi-Tenant Implementation Complete

- [ ] lib-commons v3
- [ ] MULTI_TENANT_ENABLED config
- [ ] TenantMiddleware (JWT tenantId → DB routing)
- [ ] Repositories use context-based connections
- [ ] RabbitMQ X-Tenant-ID (if applicable)
- [ ] Backward compat (MULTI_TENANT_ENABLED=false works)
- [ ] Tests pass
- [ ] Code review passed
```

---

## State Persistence

Save to `docs/ring-dev-multi-tenant/current-cycle.json` for resume support:

```json
{
  "cycle": "multi-tenant",
  "stack": {"postgresql": false, "mongodb": true, "redis": true, "rabbitmq": true},
  "gates": {"0": "PASS", "1": "PASS", "2": "IN_PROGRESS", "3": "PENDING"},
  "current_gate": 2
}
```

---

## Anti-Rationalization Table

See [multi-tenant.md § Anti-Rationalization](https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md) for the canonical anti-rationalization tables on tenantId vs organization_id.

**Skill-specific rationalizations:**

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Agent says out of scope" | Skill defines scope, not agent. | **Re-dispatch with gate context** |
| "Skip tests" | Gate 8 proves isolation works. | **MANDATORY** |
| "Skip review" | Security implications. One mistake = data leak. | **MANDATORY** |
