---
name: ring:dev-systemplane-migration
description: |
  Systemplane migration orchestrator for Lerian Go services using lib-commons (latest v5.x). Migrates services from
  .env/YAML-based configuration of operational knobs (log levels, feature flags, rate limits, timeouts,
  worker intervals) to the v5 systemplane runtime config client — a database-backed, hot-reloadable plane
  using Postgres LISTEN/NOTIFY or MongoDB change streams. v5 API: systemplane.NewPostgres /
  NewMongoDB → Register keys → Start → Get*/OnChange → admin.Mount with custom authorizer.
  Detects v4 residue (Supervisor, BundleFactory, ApplyBehavior, SYSTEMPLANE_* env vars — all DELETED in v5.0.0).

trigger: |
  - User requests systemplane integration for a Go service
  - User asks to add hot-reloadable runtime configuration
  - Task mentions "systemplane", "runtime config", "hot reload", "LISTEN/NOTIFY config", "admin.Mount"
  - User asks to migrate from v4 systemplane to v5

skip_when: |
  - Service is not a Go project
  - Task does not involve runtime configuration
  - Service has zero hot-reloadable knobs (everything is static env-var-at-startup config)
  - Task is documentation-only or non-code
---

# Systemplane Migration (lib-commons v5)

You orchestrate. Agents implement. NEVER use Edit/Write/Bash on Go source files.
All code changes go through `Task(subagent_type="ring:backend-engineer-golang")`.
TDD mandatory for all implementation gates (RED → GREEN → REFACTOR).

## Systemplane Architecture (v5)

Three-step lifecycle:
1. `systemplane.NewPostgres` / `systemplane.NewMongoDB` — construct client (pass open `*sql.DB` or `*mongo.Client`)
2. `client.Register(namespace, key, defaultValue, opts...)` — declare every key BEFORE `Start`
3. `client.Start(ctx)` — begin listening; `Get*` for reads, `OnChange` for reactions

**Standards reference:** WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-commons/main/commons/systemplane/doc.go`

**Canonical import paths:**

| Alias | Import Path | Purpose |
|-------|-------------|---------|
| `systemplane` | `github.com/LerianStudio/lib-commons/v5/commons/systemplane` | Client, constructors, options |
| `admin` | `github.com/LerianStudio/lib-commons/v5/commons/systemplane/admin` | HTTP admin routes |
| `systemplanetest` | `github.com/LerianStudio/lib-commons/v5/commons/systemplane/systemplanetest` | Contract test suite |

**v4 packages are DELETED** — do not use `lib-commons/v4/...`, `Supervisor`, `BundleFactory`, `ApplyBehavior`.

**Scope: operational knobs only** — values that can mutate in-place (log levels, feature flags, rate limits, timeouts, poll intervals).
NOT for settings requiring resource teardown: DSNs, TLS material, listen addresses → keep in env vars + restart.

**Redaction policies for `Register`:**

| Policy | Admin GET returns | Use for |
|--------|-------------------|---------|
| `RedactNone` (default) | Raw value | Log levels, feature flags, non-sensitive |
| `RedactMask` | Type-aware mask | Low-sensitivity values |
| `RedactFull` | null/omitted | Secrets, tokens, API keys |

Any key storing credentials MUST use `RedactFull`.

**Admin mount requires custom authorizer** (`admin.WithAuthorizer`) — default is DENY-ALL.

**Mandatory agent instruction (include in EVERY dispatch):**

> WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-commons/main/commons/systemplane/doc.go`.
> Use only canonical v5 import paths. v4 packages do not exist in v5.
> systemplane is for operational knobs only — not DSNs, TLS, or listen addresses.
> TDD: RED → GREEN → REFACTOR for every gate.

## Gate Overview

| Gate | Name | Condition | Agent |
|------|------|-----------|-------|
| 0 | Stack Detection + Compliance Audit | Always | Orchestrator |
| 1 | Codebase Analysis (config focus) | Always | ring:codebase-explorer |
| 1.5 | Implementation Preview | Always | ring:visualize |
| 2 | lib-commons v5 Upgrade + v4 Removal | Skip only if v5 in go.mod AND zero v4 imports | ring:backend-engineer-golang |
| 3 | Client Construction + Key Registration | Always | ring:backend-engineer-golang |
| 4 | OnChange Subscriptions | Always unless zero hot-reloadable keys (justify) | ring:backend-engineer-golang |
| 5 | Config Bridge | Skip if no Config struct reads need live values | ring:backend-engineer-golang |
| 6 | Admin HTTP Mount + Authorizer | Skip only if service has no admin surface (justify) | ring:backend-engineer-golang |
| 7 | Wiring + Lifecycle + Backward Compat | Always — NEVER skippable | ring:backend-engineer-golang |
| 8 | Tests | Always | ring:backend-engineer-golang |
| 9 | Code Review | Always | 10 parallel reviewers |
| 10 | User Validation | Always | User |
| 11 | Activation Guide | Always | Orchestrator |

Gates execute sequentially. Any existing v4 code = NON-COMPLIANT = gates cannot be skipped.

## Gate 0: Stack Detection

Orchestrator executes directly. Three phases:

**Phase 1: Stack Detection**
```bash
grep "lib-commons" go.mod         # check v4 vs v5
grep -rn "systemplane" internal/  # existing usage
grep -rn "SYSTEMPLANE_" .         # v4 env vars
grep "postgresql\|postgres" go.mod # backend type
grep "mongodb\|mongo" go.mod
# Non-canonical:
grep -rn "fsnotify\|viper.Watch\|Supervisor\|BundleFactory\|ApplyBehavior" internal/
```

**Phase 2: v5 Compliance Audit** (if systemplane code detected)
- No v4 imports or types
- `Register` called before `Start`
- `OnChange` wired for hot-reloadable keys
- `admin.Mount` with `admin.WithAuthorizer`
- Lifecycle: `client.Start(ctx)` registered with `commons.Launcher`

**Phase 3: Non-Canonical Detection**
- Any `fsnotify` / `viper.WatchConfig` / `envconfig.Watch` for runtime config → MUST replace
- Any v4 sub-packages (`domain/`, `ports/`, `registry/`, `service/`, `bootstrap/`) → MUST remove

## Severity Reference

| Severity | Criteria |
|----------|----------|
| CRITICAL | v4 import (build fails); `admin.Mount` without authorizer; secret with `RedactNone` |
| HIGH | No `Register` before `Start`; no `OnChange` for live key; `SYSTEMPLANE_*` env vars in code |
| MEDIUM | Missing `WithLogger`/`WithTelemetry`; no validator on numeric range |
| LOW | Missing `WithDescription`; inconsistent namespace naming |
