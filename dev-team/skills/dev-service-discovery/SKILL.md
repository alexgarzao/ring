---
name: ring:dev-service-discovery
description: |
  Scans the current Go project and identifies the Service → Module → Resource
  hierarchy for dispatch layer registration. Detects service name/type, modules
  (via WithModule or component structure), resources per module (PostgreSQL, MongoDB,
  RabbitMQ), database names, MongoDB indexes, and cross-module shared databases.
  Produces a visual HTML report and MongoDB index creation scripts uploaded to S3.

trigger: |
  - User wants to know what to provision in dispatch layer for a service
  - User asks "what services/modules/resources does this project have?"
  - Before running ring:dev-multi-tenant on a new service
  - User asks about MongoDB indexes in a project

skip_when: |
  - Not a Go project
  - Task does not involve service discovery, dispatch layer, or resource mapping
  - Project has no external dependencies

prerequisites: |
  - Go project with go.mod in the current working directory

related:
  complementary: [ring:dev-multi-tenant, ring:dev-devops]
---

# Service Discovery

Scans Go project to produce dispatch layer registration data. Orchestrator executes all detection phases directly.

## Phase 1: Service Detection

```bash
# Service name
grep "ApplicationName\|ServiceName" internal/bootstrap/config.go 2>/dev/null | head -5
cat .env.example 2>/dev/null | grep -i "APPLICATION_NAME\|SERVICE_NAME" | head -3

# Service type
test -f go.mod && cat go.mod | head -3  # module path hints service purpose
ls internal/adapters/ 2>/dev/null       # adapters reveal type

# Unified service check
ls components/ 2>/dev/null              # multiple components = unified service
```

Output:
```
service_name: "my-service"
is_unified: true | false
components: [{name, path, applicationName}]  # if unified
```

## Phase 2: Module Detection

```bash
# Strategy A: Explicit WithModule calls (preferred)
grep -rn "WithModule(" internal/ components/ 2>/dev/null
# Extract string arg: WithModule("onboarding") → module "onboarding"

# Strategy B: Component-based (if no WithModule found)
ls components/  # each component = one module
# module_name = component's ApplicationName

# Strategy C: Single-component fallback
# module_name = service ApplicationName
```

Merge: Strategy A → B fills gaps → C fallback.

## Phase 3: Resource Detection per Module

For each module, scan `{component_path}/internal/adapters/`:

```bash
# PostgreSQL: subdirectory existence
ls {base_path}postgres/ 2>/dev/null

# MongoDB
ls {base_path}mongodb/ 2>/dev/null || ls {base_path}mongo/ 2>/dev/null

# RabbitMQ
ls {base_path}rabbitmq/ 2>/dev/null
grep -l "producer\|Producer" {base_path}rabbitmq/ 2>/dev/null
grep -l "consumer\|Consumer" {base_path}rabbitmq/ 2>/dev/null

# Redis (informational only — NOT a dispatch layer resource)
ls {base_path}redis/ 2>/dev/null
```

## Phase 3.5: Database Name Detection per Module

```bash
# From bootstrap config
grep -E 'env:"POSTGRES_NAME|env:"DB_.*_NAME|env:"MONGO_NAME|env:"MONGO_.*_NAME' \
  {component_path}/internal/bootstrap/config.go

# From .env.example (actual values)
grep -E "POSTGRES_NAME=|DB_.*_NAME=|MONGO_NAME=|MONGO_.*_NAME=" {component_path}/.env.example

# External datasources
grep -E "DATASOURCE_.*_DATABASE=" {component_path}/.env.example
```

Cross-reference across modules: same database name in 2+ modules = shared (provision once).

## Phase 4: MongoDB Index Detection

```bash
# In-code EnsureIndexes
grep -rn "EnsureIndexes\|CreateIndexes" {component_path}/internal/ 2>/dev/null

# Script-based indexes
ls scripts/mongodb/*.js 2>/dev/null
```

For each module with MongoDB and no index script → generate `scripts/mongodb/{module}.js`:
```javascript
// Index creation for {module} module
db = db.getSiblingDB('{database_name}');
db.{collection}.createIndex({field: 1}, {background: true, name: "idx_{field}"});
```

Upload to S3: `s3://lerian-dispatch-layer/indexes/{service_name}/{module}.js`

## Phase 5: Generate HTML Report

Dispatch `ring:visualize`:

```
Generate HTML report showing:
- Service: {service_name} | Unified: {is_unified}
- For each module:
  - Resources table: type, repositories/collections, has_producer, has_consumer, queues
  - Database names: postgres_db, mongo_db (with env var names)
  - Redis: detected / not detected (note: key prefixing only)
- Shared databases: list with modules that share them
- Dispatch layer registration template (JSON)
- MongoDB index scripts: generated / none needed

Style: clean, data-dense table layout
```

## Output: Dispatch Layer Registration Template

```json
{
  "service": "{service_name}",
  "modules": [
    {
      "name": "{module_name}",
      "resources": [
        {
          "type": "postgresql",
          "database": "{db_name}",
          "env_var": "POSTGRES_NAME"
        },
        {
          "type": "mongodb",
          "database": "{db_name}",
          "env_var": "MONGO_NAME"
        },
        {
          "type": "rabbitmq",
          "has_producer": true,
          "has_consumer": true,
          "queues": ["{queue_name}"]
        }
      ]
    }
  ],
  "shared_databases": []
}
```
