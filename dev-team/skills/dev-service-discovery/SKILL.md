---
name: ring:dev-service-discovery
slug: dev-service-discovery
version: 1.0.0
type: skill
description: |
  Scans the current Go project and identifies the Service → Module → Resource
  hierarchy for tenant-manager registration. Detects service name and type,
  modules (via WithModule or component structure), and resources per module
  (PostgreSQL, MongoDB, RabbitMQ). Redis is excluded (managed via key prefixing).
  Produces a visual HTML report for human decision-making.

trigger: |
  - User wants to know what to provision in tenant-manager for a service
  - User asks "what services/modules/resources does this project have?"
  - User needs to register a service in the tenant-manager catalog
  - Before running ring:dev-multi-tenant on a new service

prerequisite: |
  - Go project with go.mod in the current working directory

NOT_skip_when: |
  - "Service is simple, I can see the structure" → Detection must be evidence-based, not assumed.
  - "Already know the modules" → Knowledge ≠ verified. Run the scan.

related:
  complementary: [ring:dev-multi-tenant, ring:dev-devops, ring:exploring-codebase]

output_schema:
  format: html
  required_sections:
    - name: "Service Discovery Report"
      pattern: "^## Service Discovery Report"
      required: true

examples:
  - name: "Scan current project"
    invocation: "/ring:dev-service-discovery"
    expected_flow: |
      1. Detect service identity (ApplicationName, type)
      2. Detect modules (WithModule calls, component structure)
      3. Detect resources per module (PostgreSQL, MongoDB, RabbitMQ)
      4. Generate visual HTML report
      5. Open in browser for review
---

# Service Discovery for Tenant-Manager

Scans the current project and produces a visual report of the **Service → Module → Resource** hierarchy. This report tells you exactly what needs to be registered in the tenant-manager (pool-manager) to provision tenants for this service.

---

## How It Works

The tenant-manager has three entities that must be registered before provisioning tenants:

1. **Service** — the application (e.g., "ledger", "plugin-crm"). Has a type: `product` or `plugin`.
2. **Module** — a logical grouping within the service (e.g., "onboarding", "transaction"). Each module gets its own database pool per tenant.
3. **Resource** — infrastructure a module needs: `postgresql`, `mongodb`, or `rabbitmq`. Each resource gets provisioned per tenant per module.

Redis is **not** a tenant-manager resource — it uses key prefixing via `GetKeyFromContext` and does not need registration.

---

## Phase 1: Service Detection

**Orchestrator executes directly. No agent dispatch.**

```text
DETECT service identity (run in parallel):

1. Service name:
   - Grep tool: pattern "const ApplicationName" in internal/bootstrap/ cmd/ --include="*.go"
   - Extract the string value (e.g., "ledger", "plugin-crm", "onboarding")

2. Service type:
   - Read go.mod first line (module path)
   - If module path contains "plugin-" → serviceType = "plugin"
   - Else → serviceType = "product"

3. Project structure:
   - Glob tool: pattern "components/*/cmd/app/main.go"
   - If multiple matches → unified service with multiple components (like ledger)
   - If no matches → Glob: "cmd/app/main.go" or "cmd/*/main.go" → single-component service

4. Unified service detection (if multiple components found):
   - Glob tool: pattern "components/*/internal/bootstrap/config.go"
   - For each component, grep "const ApplicationName" → collect module names
   - Check if a "parent" component imports and composes the others
     (grep "InitServiceWithOptions\|InitServersWithOptions" in each component's bootstrap)
   - The parent component's ApplicationName = service name
   - Each child component's ApplicationName = module name

Store results:
  service_name = "{detected name}"
  service_type = "product" | "plugin"
  is_unified = true | false
  components = [{name, path, applicationName}]  // if unified
```

---

## Phase 2: Module Detection

```text
DETECT modules (run in parallel):

Strategy A — Explicit WithModule calls (preferred):
   - Grep tool: pattern "WithModule\(" in internal/ components/ --include="*.go"
   - Extract module names from the string argument: WithModule("onboarding") → "onboarding"
   - Deduplicate (same module name used in tmpostgres, tmmongo, tmrabbitmq = one module)

Strategy B — Component-based (if no WithModule found):
   - Each component with its own internal/bootstrap/ and ApplicationName = one module
   - module_name = ApplicationName of that component

Strategy C — Single-component service (no components/ directory):
   - module_name = service ApplicationName
   - This service has exactly 1 module

Merge strategies (A takes precedence, B fills gaps, C is fallback):
  modules = [
    {name: "onboarding", component_path: "components/onboarding/"},
    {name: "transaction", component_path: "components/transaction/"},
  ]
  // or for single-component:
  modules = [
    {name: "my-service", component_path: "./"}
  ]
```

---

## Phase 3: Resource Detection per Module

```text
For EACH detected module, scan its adapter directory:

base_path = module.component_path + "internal/adapters/"
// For single-component: base_path = "internal/adapters/"

DETECT resources (run in parallel per module):

1. PostgreSQL:
   - Glob tool: pattern "{base_path}postgres/*" (directories)
   - If any subdirectory exists → resource "postgresql" detected
   - Count subdirectories = repository count
   - List subdirectory names = repository names (e.g., "organization", "ledger", "account")

2. MongoDB:
   - Glob tool: pattern "{base_path}mongodb/*" OR "{base_path}mongo/*" (directories)
   - If any subdirectory or file exists → resource "mongodb" detected
   - Note: metadata repositories use collection-per-entity pattern

3. RabbitMQ:
   - Glob tool: pattern "{base_path}rabbitmq/*" (files)
   - If any file exists → resource "rabbitmq" detected
   - Grep: "producer\|Producer" in matched files → has producer
   - Grep: "consumer\|Consumer" in matched files → has consumer
   - Grep: "QUEUE\|queue" in the module's bootstrap config → extract queue names

4. Redis (informational only — NOT a tenant-manager resource):
   - Glob tool: pattern "{base_path}redis/*" (files)
   - If exists → note "Redis detected — managed via key prefixing, no tenant-manager registration needed"

Store per module:
  module.resources = [
    {type: "postgresql", repos: ["organization", "ledger", ...], count: 7},
    {type: "mongodb", collections_info: "metadata (collection-per-entity)"},
    {type: "rabbitmq", has_producer: true, has_consumer: true, queues: ["BTO"]},
  ]
  module.redis_detected = true | false  // informational only
```

---

## Phase 4: Generate Visual Report

**MANDATORY: Invoke `Skill("ring:visual-explainer")` to produce the report.**

Read `default/skills/visual-explainer/templates/data-table.html` first to absorb table patterns.

**The HTML report MUST include these sections:**

### 1. Service Overview

Card showing:
- **Service Name:** `{service_name}`
- **Service Type:** `product` | `plugin`
- **Modules:** `{count}`
- **Total Resources:** `{count across all modules}`

### 2. Module Map

One card per module:

```
┌─────────────────────────────────────┐
│ MODULE: onboarding                  │
├─────────────────────────────────────┤
│ PostgreSQL ✅  (7 repositories)     │
│   organization, ledger, account,    │
│   asset, portfolio, segment,        │
│   accounttype                       │
│                                     │
│ MongoDB ✅  (metadata)              │
│                                     │
│ RabbitMQ ❌  (not detected)         │
│                                     │
│ Redis ℹ️  (detected — not a         │
│   tenant-manager resource)          │
└─────────────────────────────────────┘
```

### 3. Service Hierarchy Diagram

Mermaid diagram:

```mermaid
graph TD
    S["Service: ledger (product)"]
    S --> M1["Module: onboarding"]
    S --> M2["Module: transaction"]
    M1 --> R1["PostgreSQL (7 repos)"]
    M1 --> R2["MongoDB"]
    M2 --> R3["PostgreSQL (6 repos)"]
    M2 --> R4["MongoDB"]
    M2 --> R5["RabbitMQ"]
```

### 4. Tenant-Manager Registration Checklist

```markdown
## What to register in tenant-manager:

- [ ] **Service:** `ledger` (type: product, isolation: database)

- [ ] **Module:** `onboarding`
  - [ ] Resource: postgresql (primary)
  - [ ] Resource: mongodb

- [ ] **Module:** `transaction`
  - [ ] Resource: postgresql (primary)
  - [ ] Resource: mongodb
  - [ ] Resource: rabbitmq
```

**Save to:** `docs/service-discovery.html` in the project root.

**Open in browser:**
```text
macOS: open docs/service-discovery.html
Linux: xdg-open docs/service-discovery.html
```

---

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "I already know the modules" | Knowledge ≠ evidence. The scan catches things you miss. | **Run the scan** |
| "This service is simple, just one module" | Simple services may still have multiple resource types. | **Run the scan** |
| "Redis should be included as a resource" | Redis uses key prefixing (`GetKeyFromContext`), not per-tenant provisioning. It is not a tenant-manager resource. | **Exclude Redis from resources** |
| "The report doesn't need to be visual" | Visual reports are for human decision-making. A JSON dump is not actionable. | **Generate HTML via ring:visual-explainer** |
| "WithModule not found, so no modules" | Fall back to component structure or ApplicationName. A service always has at least one module. | **Use Strategy B or C** |

---

## Pressure Resistance

| User Says | This Is | Response |
|-----------|---------|----------|
| "Just tell me the modules, no report" | SCOPE_REDUCTION | "The visual report takes seconds and gives you a complete checklist for tenant-manager registration. Generating it." |
| "Include Redis as a resource" | SCOPE_EXPANSION | "Redis is managed via key prefixing and does not require tenant-manager registration. Excluding it." |
| "Skip the PostgreSQL repo count" | SCOPE_REDUCTION | "Repository count helps you understand the scope of each module. Including it." |
