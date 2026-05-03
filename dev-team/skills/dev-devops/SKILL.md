---
name: ring:dev-devops
description: |
  Gate 1 of the development cycle. Creates/updates Dockerfile, docker-compose setup,
  and environment variables for local development and deployment readiness.
  Runs at TASK cadence (after all subtasks complete Gate 0 + Gate 3 + Gate 9).

trigger: |
  - Gate 1 of development cycle
  - Implementation complete from Gate 0
  - Need containerization or environment setup

skip_when: |
  - Not inside a development cycle (ring:dev-cycle)
  - Task is documentation-only, configuration-only, or non-code
  - Project already has complete Docker setup unchanged by Gate 0
  - Pure library package with no deployable service

sequence:
  after: [ring:dev-implementation]
  before: [ring:dev-sre]

related:
  complementary: [ring:dev-implementation, ring:dev-unit-testing]
---

# DevOps Setup (Gate 1)

Creates or updates containerization artifacts: Dockerfile, docker-compose.yml, .env.example.

You orchestrate. DevOps agent implements. Max 3 iterations, then escalate.

## Step 1: Validate Input

Required: `unit_id` (TASK id), `language` (go|typescript|python), `service_type` (api|worker|batch|cli), `implementation_files`, `gate0_handoffs`.
Optional: `new_dependencies`, `new_env_vars`, `new_services`, `existing_dockerfile`, `existing_compose`.

## Step 2: Analyze Requirements

```
Check existing files:
- Dockerfile: EXISTS/MISSING
- docker-compose.yml: EXISTS/MISSING
- .env.example: EXISTS/MISSING

Determine actions: CREATE / UPDATE / NONE for each

Services needed (from new_services + language defaults):
- Go api → alpine base, expose port 3000
- TypeScript api → node base, expose port 3000
- worker → no port exposed
```

## Step 3: Dispatch DevOps Agent

```yaml
Task:
  subagent_type: "ring:devops-engineer"
  description: "Create/update DevOps artifacts for {unit_id}"
  prompt: |
    ## DevOps Setup Gate

    unit_id: {unit_id}
    language: {language}
    service_type: {service_type}
    implementation_files: {implementation_files}
    new_dependencies: {new_dependencies}
    new_env_vars: {new_env_vars}
    new_services: {new_services}

    Existing files: Dockerfile={EXISTS/MISSING}, docker-compose={EXISTS/MISSING}, .env.example={EXISTS/MISSING}

    Standards: Load via cached_standards or WebFetch:
    https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/devops.md

    ## Required Artifacts

    ### Dockerfile
    - Multi-stage build (builder → final)
    - Go: FROM golang:{version}-alpine AS builder; final FROM alpine:latest
    - TypeScript: FROM node:{version}-alpine AS builder; final FROM node:{version}-alpine
    - Non-root user in final stage
    - COPY only compiled binary/dist (not source)
    - EXPOSE port (api only)
    - HEALTHCHECK CMD wget/curl /health

    ### docker-compose.yml
    - Service: app + all dependencies (postgres, mongodb, rabbitmq, redis/valkey as needed)
    - Health checks on all dependency services
    - app depends_on all deps with condition: service_healthy
    - Named volumes for data persistence
    - Network isolation (app network)
    - Env vars from .env file

    ### .env.example
    - All env vars with defaults + comments
    - Sections: App, Database, Cache, Queue, Observability
    - No secrets with real values

    ## Standards Coverage Table (MANDATORY output)
    | # | Section | Status | Evidence |
    |---|---------|--------|----------|
    | 1 | Containers (Dockerfile) | ✅/❌ | Dockerfile:{line} |
    | 2 | Docker Compose | ✅/❌ | docker-compose.yml:{line} |
    | 3 | Environment (.env.example) | ✅/❌ | .env.example:{line} |
    | 4 | Health Checks | ✅/❌ | {file:line} |

    ## Verification (run and report results)
    1. docker-compose build → PASS/FAIL
    2. docker-compose up -d && sleep 10 && docker-compose ps → PASS/FAIL
    3. docker-compose logs app | head -5 | jq '.level' → PASS/FAIL (JSON logging)
    4. docker-compose down → PASS/FAIL (cleanup)

    All standards met + all verifications PASS required.
```

## Step 4: Validate Output

```
if all standards ✅ AND all verifications PASS:
  → PASS → proceed to Gate 2 (SRE)

if any ❌ or verification FAIL:
  → iterations++
  → if iterations >= 3: ESCALATE to user
  → Re-dispatch with specific failures listed
```

## Re-Dispatch Template (if fixes needed)

```yaml
Task:
  subagent_type: "ring:devops-engineer"
  description: "Fix DevOps issues for {unit_id}"
  prompt: |
    Fix the following DevOps issues:
    {issues_list}

    Re-run verification commands after fixing. Return updated Standards Coverage Table.
```

## Output Format

```markdown
## DevOps Summary
unit_id | result: PASS/FAIL | iterations

## Files Changed
| File | Action | Summary |
|------|--------|---------|
| Dockerfile | Created/Updated | {key changes} |
| docker-compose.yml | Created/Updated | {key changes} |
| .env.example | Created/Updated | {key changes} |

## Verification Results
| Check | Result |
|-------|--------|
| docker-compose build | PASS/FAIL |
| docker-compose up -d | PASS/FAIL |
| services healthy | PASS/FAIL |
| JSON logs | PASS/FAIL |

## Handoff to Gate 2
gate1_result: PASS | ESCALATED
files_changed: [list]
services_configured: N
```
