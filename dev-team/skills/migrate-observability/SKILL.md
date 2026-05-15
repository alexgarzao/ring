---
name: ring:migrate-observability
description: |
  Migrates a Lerian Go application's direct observability imports from the
  deprecated lib-commons shim packages and deprecated HTTP/gRPC observability
  middleware symbols to lib-observability. Targets exactly the packages and
  symbols marked // Deprecated: in lib-commons — no more, no less.
  Adds lib-observability to go.mod and validates the build.
  Migrates commons/opentelemetry only when the effective lib-commons version
  marks that package deprecated and lib-observability/tracing exposes the same API.
  Does NOT touch non-observability commons/net/http helpers, kafka/streaming,
  or any non-deprecated lib-commons package.
---

# Migrate Deprecated lib-commons Observability Packages to lib-observability

## When to use
- Application imports one or more deprecated lib-commons observability packages
- Team decision to eliminate deprecation warnings from lib-commons shims
- lib-commons deprecation notices appear in IDE or go vet output

## Skip when
- Application already imports lib-observability for all observability concerns
- Application has no imports of the deprecated lib-commons packages listed below
- Application is lib-commons itself
- lib-commons version in go.mod does not yet include the delegation shims (commons/log/doc.go has no Deprecated notice) — upgrade lib-commons first

**Do NOT skip when:**
- "The app only imports log/ from lib-commons" → still migrate; log is deprecated
- "The app uses streaming/kafka" → streaming is NOT deprecated; only deprecated observability packages and HTTP/gRPC observability middleware migrate
- "The app uses commons/opentelemetry for tracing bootstrap" → migrate only if the effective lib-commons package is deprecated and lib-observability/tracing exposes the target API

## Sequence
**Runs before:** (none)
**Runs after:** (none)

## Related
**Complementary:** ring:using-ring, ring:dev-cycle, ring:codereview, ring:lint, ring:using-lib-commons

---

## Overview

This skill replaces imports/usages of the **deprecated** lib-commons observability APIs
with their canonical lib-observability equivalents.

**Targeting strategy:** migrate only APIs that satisfy both gates:
1. The source API is marked `// Deprecated:` in the effective lib-commons version.
2. The target API exists in the effective lib-observability version.

If either gate fails, do not migrate that API. Report the missing gate and leave
the lib-commons usage unchanged. This keeps lib-commons deprecation notices as
the source of truth while preventing migrations to APIs that are not available
in lib-observability yet.

Packages that are NOT deprecated in lib-commons (e.g. non-observability
`commons/net/http` helpers, `commons/streaming`) are explicitly out of scope.

**What changes:** import paths and deprecated symbol qualifiers in `.go` files + `go.mod` dependency.
**What stays the same:** all non-deprecated lib-commons packages, including infrastructure
clients (`commons/postgres`, `commons/streaming`, etc.).

---

## CRITICAL: Role Clarification

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Discover imports, plan replacements, validate, report |
| **Agent** | Apply file edits, run go mod, fix compilation errors |

---

## Import Mapping Reference

The deprecated lib-commons packages and their lib-observability replacements:

| Deprecated lib-commons import | lib-observability replacement | Package name change? |
|---|---|---|
| `lib-commons/v5/commons/log` | `lib-observability/log` | No — qualifier stays `log` |
| `lib-commons/v5/commons/zap` | `lib-observability/zap` | No — qualifier stays `zap` |
| `lib-commons/v5/commons/runtime` | `lib-observability/runtime` | No — qualifier stays `runtime` |
| `lib-commons/v5/commons/assert` | `lib-observability/assert` | No — qualifier stays `assert` |
| `lib-commons/v5/commons/opentelemetry` | `lib-observability/tracing` | Yes if the old import was unaliased: `opentelemetry.X` → `tracing.X`. Preserve explicit aliases. |
| `lib-commons/v5/commons/opentelemetry/metrics` | `lib-observability/metrics` | No — qualifier stays `metrics` |
| `lib-commons/v5/commons/opentelemetry/constants` | `lib-observability/constants` | No — qualifier stays `constants` |
| `lib-commons/v5/commons/opentelemetry/redaction` | `lib-observability/redaction` | No — qualifier stays `redaction` |

> The metrics/constants/redaction/log/zap/runtime/assert replacements share the same package qualifier — import path changes only,
> no call-site renames needed in the file body.
> For root `commons/opentelemetry`, preserve explicit aliases such as
> `libOpentelemetry` or `libCommonsOtel`. If the import is unaliased, rewrite
> the package qualifier from `opentelemetry` to `tracing`.

### Deprecated root commons/opentelemetry package

`commons/opentelemetry` is an API-aware package migration. Run it only when the
effective lib-commons package documentation contains `Deprecated:` and the
effective `lib-observability/tracing` package exposes the matching bootstrap,
span, redaction, and propagation APIs.

| Deprecated symbol family | lib-observability replacement |
|---|---|
| `TelemetryConfig`, `Telemetry`, `NewTelemetry`, `ApplyGlobals`, `Tracer`, `Meter`, `ShutdownTelemetry*` | `tracing` equivalents |
| `RedactionRule`, `Redactor`, `NewDefaultRedactor`, `NewAlwaysMaskRedactor`, `NewRedactor`, `ObfuscateStruct` | `tracing` equivalents |
| `AttrBagSpanProcessor`, `RedactingAttrBagSpanProcessor` | `tracing` equivalents |
| `HandleSpanBusinessErrorEvent`, `HandleSpanEvent`, `HandleSpanError` | `tracing` equivalents |
| `SetSpanAttributesFromValue`, `BuildAttributesFromValue`, `SetSpanAttributeForParam` | `tracing` equivalents |
| `InjectTraceContext`, `ExtractTraceContext`, `InjectHTTPContext`, `ExtractHTTPContext`, `InjectGRPCContext`, `ExtractGRPCContext` | `tracing` equivalents |
| `InjectQueueTraceContext`, `ExtractQueueTraceContext`, `PrepareQueueHeaders`, `InjectTraceHeadersIntoQueue`, `ExtractTraceContextFromQueueHeaders` | `tracing` equivalents |
| `GetTraceIDFromContext`, `GetTraceStateFromContext` | `tracing` equivalents |

Migration rule:
- Preserve explicit aliases. Example:
  `libOpentelemetry "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry"`
  becomes `libOpentelemetry "github.com/LerianStudio/lib-observability/tracing"`
  and call sites remain `libOpentelemetry.X`.
- If the old import was unaliased, replace the import path and rewrite
  `opentelemetry.X` call sites to `tracing.X`.
- Helper-only files may migrate independently. These include calls such as
  `HandleSpanError`, `HandleSpanBusinessErrorEvent`,
  `SetSpanAttributesFromValue`, `InjectHTTPContext`, and queue/header
  propagation helpers. They operate on OpenTelemetry public interfaces and do
  not require the application's bootstrap `Telemetry` type to move.
- Bootstrap files that use `Telemetry`, `TelemetryConfig`, `NewTelemetry`,
  `ApplyGlobals`, `Tracer`, `Meter`, or `ShutdownTelemetry*` must be
  migrated only if the resulting `*tracing.Telemetry` does not cross a
  remaining lib-commons API boundary. Typical blockers:
  `commons/server.NewServerManager(..., *commons/opentelemetry.Telemetry, ...)`
  and `commons/net/http.NewTelemetryMiddleware(*commons/opentelemetry.Telemetry)`
  when that middleware call is not also migrated to `lib-observability/middleware`.
- If bootstrap migration would create a type mismatch, leave that file on
  `commons/opentelemetry`, migrate the helper-only files, and report the
  remaining bootstrap import as intentionally blocked.
- If any referenced symbol is absent from `lib-observability/tracing`, do not
  migrate that file. Report the missing symbol and leave the lib-commons import
  unchanged.

### Deprecated symbols inside commons/net/http

`commons/net/http` is a mixed package. Most helpers stay in lib-commons. Only
symbols marked `// Deprecated:` in lib-commons and present in
`lib-observability/middleware` may migrate.

| Deprecated symbol | lib-observability replacement |
|---|---|
| `RequestInfo` | `middleware.RequestInfo` |
| `ResponseMetricsWrapper` | `middleware.ResponseMetricsWrapper` |
| `NewRequestInfo` | `middleware.NewRequestInfo` |
| `LogMiddlewareOption` | `middleware.LogMiddlewareOption` |
| `WithCustomLogger` | `middleware.WithCustomLogger` |
| `WithObfuscationDisabled` | `middleware.WithObfuscationDisabled` |
| `WithHTTPLogging` | `middleware.WithHTTPLogging` |
| `WithGrpcLogging` | `middleware.WithGrpcLogging` |
| `RequestInfo.CLFString` | `middleware.RequestInfo.CLFString` |
| `RequestInfo.String` | `middleware.RequestInfo.String` |
| `RequestInfo.FinishRequestInfo` | `middleware.RequestInfo.FinishRequestInfo` |
| `DefaultMetricsCollectionInterval` | `middleware.DefaultMetricsCollectionInterval` |
| `TelemetryMiddleware` | `middleware.TelemetryMiddleware` |
| `NewTelemetryMiddleware` | `middleware.NewTelemetryMiddleware` |
| `TelemetryMiddleware.WithTelemetry` | `middleware.TelemetryMiddleware.WithTelemetry` |
| `TelemetryMiddleware.EndTracingSpans` | `middleware.TelemetryMiddleware.EndTracingSpans` |
| `TelemetryMiddleware.WithTelemetryInterceptor` | `middleware.TelemetryMiddleware.WithTelemetryInterceptor` |
| `TelemetryMiddleware.EndTracingSpansInterceptor` | `middleware.TelemetryMiddleware.EndTracingSpansInterceptor` |
| `StopMetricsCollector` | `middleware.StopMetricsCollector` |
| `SetHandlerSpanAttributes` | `middleware.SetHandlerSpanAttributes` |
| `SetTenantSpanAttribute` | `middleware.SetTenantSpanAttribute` |
| `SetExceptionSpanAttributes` | `middleware.SetExceptionSpanAttributes` |
| `SetDisputeSpanAttributes` | `middleware.SetDisputeSpanAttributes` |

Migration rule:
- If a file imports `lib-commons/v5/commons/net/http` and uses only deprecated
  observability middleware symbols from that import, replace the import path with
  `github.com/LerianStudio/lib-observability/middleware` and preserve/adjust the
  alias so call sites compile.
- If a file imports `lib-commons/v5/commons/net/http` and also uses non-observability
  HTTP helpers (`Respond`, pagination, validation, CORS,
  rate-limit/idempotency subpackages, etc.), keep the lib-commons import and add
  a second import for `github.com/LerianStudio/lib-observability/middleware`.
  Rewrite only deprecated observability middleware symbol qualifiers to the middleware alias.
- Do not migrate response helpers, validation helpers, pagination helpers,
  CORS/basic-auth helpers, ownership helpers, or any
  `commons/net/http` subpackage.

### Deprecated symbols inside commons root

The root commons package is also mixed. App configuration, environment, OS, security,
and general helpers stay in lib-commons. Only observability context helpers marked
Deprecated in lib-commons and present in root lib-observability may migrate.

| Deprecated symbol | lib-observability replacement |
|---|---|
| `NewLoggerFromContext` | `observability.NewLoggerFromContext` |
| `ContextWithLogger` | `observability.ContextWithLogger` |
| `ContextWithTracer` | `observability.ContextWithTracer` |
| `ContextWithMetricFactory` | `observability.ContextWithMetricFactory` |
| `ContextWithHeaderID` | `observability.ContextWithHeaderID` |
| `TrackingComponents` | `observability.TrackingComponents` |
| `NewTrackingFromContext` | `observability.NewTrackingFromContext` |
| `ContextWithSpanAttributes` | `observability.ContextWithSpanAttributes` |
| `AttributesFromContext` | `observability.AttributesFromContext` |
| `ReplaceAttributes` | `observability.ReplaceAttributes` |

Migration rule:
- If a file imports root `lib-commons/v5/commons` and uses only deprecated
  observability context helpers from that import, replace the import path with
  `github.com/LerianStudio/lib-observability` and preserve or adjust the alias.
- If a file imports root commons and also uses non-observability helpers
  (`AppConfig`, env helpers, security rules, pointer/string/time helpers, etc.),
  keep the lib-commons import and add a second import for
  `github.com/LerianStudio/lib-observability`. Rewrite only deprecated
  observability context helper qualifiers to the lib-observability alias.

### Do NOT migrate (not deprecated — stays lib-commons)

| Import | Reason |
|---|---|
| `lib-commons/v5/commons/net/http` non-observability helpers | HTTP helpers — NOT deprecated. Only logging and telemetry middleware symbols migrate. |
| `lib-commons/v5/commons/streaming` | Kafka/CloudEvents producer — NOT deprecated; uses lib-observability internally |
| `lib-commons/v5/commons/postgres`, `mongo`, `redis`, `rabbitmq` | Infrastructure clients — NOT deprecated |
| `lib-commons/v5/commons/multitenancy` | Multi-tenant dispatch — NOT deprecated |
| `lib-commons/v5/commons/systemplane` | Runtime config client — NOT deprecated |
| `lib-commons/v5/commons` non-observability helpers | Root package helpers such as AppConfig, environment, OS, security, pointers, string/time utilities — NOT deprecated. Only observability context helpers migrate. |

## Step 1: Validate Input

<verify_before_proceed>
- repo_path exists and contains a go.mod file
- go.mod declares module path (to identify lib-commons import prefix)
- effective lib-commons/lib-observability versions satisfy the per-migration gates below
</verify_before_proceed>

```text
1. Verify repo_path/go.mod exists
2. Extract module name from go.mod
3. Confirm lib-commons is a dependency: grep "lib-commons" go.mod
   if not found → report "No lib-commons dependency found. Nothing to migrate." and exit PASS
4. Quick check — lib-observability already present?
   grep "lib-observability" go.mod
   if found → note for UX messaging; do NOT exit here.
   lib-observability presence alone does not mean migration is complete —
   deprecated lib-commons imports may still exist. Continue to Step 2 discovery.
   If Step 2 finds zero deprecated imports, report "Migration already complete.
   No deprecated lib-commons observability imports found." and exit PASS.
5. HARD GATE — Verify the effective lib-commons/lib-observability APIs:

   Resolve the effective lib-commons module directory (honours replace directives, workspaces, and custom GOMODCACHE):

   LIB_COMMONS_DIR=$(go list -m -f '{{.Dir}}' github.com/LerianStudio/lib-commons/v5)
   LIB_OBSERVABILITY_DIR=$(go list -m -f '{{.Dir}}' github.com/LerianStudio/lib-observability 2>/dev/null || true)
   DOC_PATH="${LIB_COMMONS_DIR}/commons/log/doc.go"
   CONTEXT_PATH="${LIB_COMMONS_DIR}/commons/context.go"
   LOGGING_PATH="${LIB_COMMONS_DIR}/commons/net/http/withLogging_middleware.go"
   TELEMETRY_PATH="${LIB_COMMONS_DIR}/commons/net/http/withTelemetry.go"
   SPAN_HELPERS_PATH="${LIB_COMMONS_DIR}/commons/net/http/context_span.go"
   OBS_ROOT_PATH="${LIB_OBSERVABILITY_DIR}/observability.go"
   OBS_MIDDLEWARE_PATH="${LIB_OBSERVABILITY_DIR}/middleware/logging.go"
   OBS_TELEMETRY_PATH="${LIB_OBSERVABILITY_DIR}/middleware/telemetry.go"
   OBS_SPAN_HELPERS_PATH="${LIB_OBSERVABILITY_DIR}/middleware/context_span.go"
   OTEL_DOC_PATH="${LIB_COMMONS_DIR}/commons/opentelemetry/doc.go"
   OBS_TRACING_PATH="${LIB_OBSERVABILITY_DIR}/tracing/otel.go"

   Guard — if the log doc file cannot be located, package-level log/zap/runtime/assert
   and root context-helper migration are disabled:
     if [ ! -f "$DOC_PATH" ]; then
       echo "NOTE: unable to locate $DOC_PATH for github.com/LerianStudio/lib-commons/v5.
       Skipping shim-dependent package/context migrations."
     fi

   Check if doc.go contains "Deprecated":
     grep -c "Deprecated" "$DOC_PATH"

   If result is 0 → do not migrate commons/log, commons/zap, commons/runtime,
   commons/assert, or root commons context helpers. Continue evaluating
   commons/net/http symbol gates and root commons/opentelemetry gates. Report:
     "NOTE: lib-commons does not include the log delegation shims.
      Skipping shim-dependent package/context migrations because replacing
      commons/log.Logger with lib-observability/log.Logger would cause type
      incompatibility at lib-commons boundaries that still accept or return
      commons/log.Logger (for example mongo.Config.Logger).

      Migrations with independent gates, such as deprecated commons/net/http
      symbols and deprecated commons/opentelemetry, may still proceed."

   Check if HTTP/gRPC logging middleware deprecations are available:
     if [ -f "$LOGGING_PATH" ]; then grep -c "Deprecated" "$LOGGING_PATH"; fi

   Check if the target lib-observability middleware API exists:
     if [ -f "$OBS_MIDDLEWARE_PATH" ]; then grep -E "func WithHTTPLogging|func WithGrpcLogging|type RequestInfo|type LogMiddlewareOption" "$OBS_MIDDLEWARE_PATH"; fi

   Check if HTTP/gRPC telemetry middleware deprecations are available:
     if [ -f "$TELEMETRY_PATH" ]; then grep -c "Deprecated" "$TELEMETRY_PATH"; fi

   Check if the target lib-observability telemetry middleware API exists:
     if [ -f "$OBS_TELEMETRY_PATH" ]; then grep -E "func NewTelemetryMiddleware|func \\(tm \\*TelemetryMiddleware\\) WithTelemetry|func \\(tm \\*TelemetryMiddleware\\) WithTelemetryInterceptor|type TelemetryMiddleware" "$OBS_TELEMETRY_PATH"; fi

   Check if root commons observability context helper deprecations are available:
     if [ -f "$CONTEXT_PATH" ]; then grep -E "Deprecated: use (NewTrackingFromContext|ContextWithLogger|ContextWithTracer|ContextWithMetricFactory|ContextWithHeaderID|ContextWithSpanAttributes|AttributesFromContext|ReplaceAttributes)" "$CONTEXT_PATH"; fi

   Check if the target root lib-observability context helper API exists:
     if [ -f "$OBS_ROOT_PATH" ]; then grep -E "func NewTrackingFromContext|func ContextWithLogger|func ContextWithTracer|func ContextWithMetricFactory|func ContextWithHeaderID|func ContextWithSpanAttributes|func AttributesFromContext|func ReplaceAttributes" "$OBS_ROOT_PATH"; fi

   Check if root commons/opentelemetry package deprecation is available:
     if [ -f "$OTEL_DOC_PATH" ]; then grep -c "Deprecated" "$OTEL_DOC_PATH"; fi

   Check if the target lib-observability tracing API exists:
     if [ -f "$OBS_TRACING_PATH" ]; then grep -E "type TelemetryConfig|type Telemetry|func NewTelemetry|func HandleSpanError|func BuildAttributesFromValue|func InjectTraceContext|func GetTraceIDFromContext" "$OBS_TRACING_PATH"; fi

   Check if HTTP span helper deprecations are available:
     if [ -f "$SPAN_HELPERS_PATH" ]; then grep -c "Deprecated" "$SPAN_HELPERS_PATH"; fi

   Check if the target lib-observability span helper API exists:
     if [ -f "$OBS_SPAN_HELPERS_PATH" ]; then grep -E "func SetHandlerSpanAttributes|func SetTenantSpanAttribute|func SetExceptionSpanAttributes|func SetDisputeSpanAttributes" "$OBS_SPAN_HELPERS_PATH"; fi

   If either logging gate result is 0 or the file is absent → do not run the
   commons/net/http logging symbol-level migration. Continue with other
   migrations and report:
     "NOTE: lib-commons does not yet mark HTTP/gRPC logging middleware as
      deprecated, or lib-observability does not yet expose the middleware API.
      Skipping commons/net/http logging migration until both gates pass."

   If either telemetry gate result is 0 or the file is absent → do not run the
   commons/net/http telemetry symbol-level migration. Continue with other
   migrations and report:
     "NOTE: lib-commons does not yet mark HTTP/gRPC telemetry middleware as
      deprecated, or lib-observability does not yet expose the telemetry API.
      Skipping commons/net/http telemetry migration until both gates pass."

   If either root context helper gate result is 0 or the file is absent → do not
   run the commons root observability context helper migration. Continue with
   other migrations and report the missing gate.

   If either root opentelemetry gate result is 0 or the file is absent → do not
   run the commons/opentelemetry package migration. Continue with other
   migrations and report:
     "NOTE: lib-commons does not yet mark commons/opentelemetry as deprecated,
      or lib-observability does not expose the tracing API. Skipping root
      opentelemetry migration until both gates pass."

   If either HTTP span helper gate result is 0 or the file is absent → do not run
   the commons/net/http span helper migration. Continue with other migrations and
   report the missing gate.

   If all relevant gate pairs are ≥ 1 → matching symbols may be migrated when discovered.
```

---

## Step 2: Discover Deprecated Observability Imports

Scan all `.go` files in the repository for deprecated observability imports and
deprecated `commons/net/http` observability middleware symbol usage.
Also scan root `commons` observability context helper usage.

```text
Search patterns (grep -r across *.go files):

MIGRATE targets (all deprecated in lib-commons):
  lib-commons/v5/commons/log"
  lib-commons/v5/commons/zap"
  lib-commons/v5/commons/runtime"
  lib-commons/v5/commons/assert"
  lib-commons/v5/commons/opentelemetry"
  lib-commons/v5/commons/opentelemetry/metrics"
  lib-commons/v5/commons/opentelemetry/constants"
  lib-commons/v5/commons/opentelemetry/redaction"

SYMBOL-LEVEL MIGRATE targets (only when used from lib-commons/v5/commons/net/http):
  RequestInfo
  ResponseMetricsWrapper
  NewRequestInfo
  LogMiddlewareOption
  WithCustomLogger
  WithObfuscationDisabled
  WithHTTPLogging
  WithGrpcLogging
  DefaultMetricsCollectionInterval
  TelemetryMiddleware
  NewTelemetryMiddleware
  WithTelemetry
  EndTracingSpans
  WithTelemetryInterceptor
  EndTracingSpansInterceptor
  StopMetricsCollector
  SetHandlerSpanAttributes
  SetTenantSpanAttribute
  SetExceptionSpanAttributes
  SetDisputeSpanAttributes

SYMBOL-LEVEL MIGRATE targets (only when used from root lib-commons/v5/commons):
  NewLoggerFromContext
  ContextWithLogger
  ContextWithTracer
  ContextWithMetricFactory
  ContextWithHeaderID
  TrackingComponents
  NewTrackingFromContext
  ContextWithSpanAttributes
  AttributesFromContext
  ReplaceAttributes

DO NOT MIGRATE targets (not deprecated — skip silently):
  lib-commons/v5/commons/net/http"        ← keep unless the file uses deprecated observability middleware symbols from it
  lib-commons/v5/commons/streaming"
  lib-commons/v5/commons/postgres"
  lib-commons/v5/commons/mongo"
  lib-commons/v5/commons/redis"
  lib-commons/v5/commons/rabbitmq"
  lib-commons/v5/commons/multitenancy"
  lib-commons/v5/commons/systemplane"
  lib-commons/v5/commons"                 ← keep unless the file uses deprecated observability context helper symbols from it

For each found import, record:
  - file path
  - line number
  - import alias (if any)
  - full import path
  - for commons/net/http, which deprecated observability middleware symbols are used
  - for commons/opentelemetry, whether the import has an explicit alias
  - for commons/opentelemetry, whether the file is helper-only or bootstrap/type-bearing
  - for bootstrap/type-bearing commons/opentelemetry files, whether the telemetry value crosses a remaining lib-commons API boundary
  - for root commons, which deprecated observability context helper symbols are used
  - whether non-observability commons/net/http symbols are also used
  - whether non-observability root commons symbols are also used
```

**Output discovery report:**
```
## Discovery

### Imports to Migrate
| File | Line | Current Import | Target Import |
|------|------|---------------|---------------|
| cmd/main.go | 5 | lib-commons/v5/commons/log | lib-observability/log |
| cmd/main.go | 6 | lib-commons/v5/commons/net/http.WithHTTPLogging | lib-observability/middleware.WithHTTPLogging |
| ...

### Imports NOT Migrated (not deprecated — kept in lib-commons)
| File | Line | Import | Reason |
|------|------|--------|--------|
| ...

### Summary
- Total files to change: X
- Total imports to replace: Y
- Total imports left as-is: Z
```

---

## Step 3: Present Migration Plan and Confirm

<dispatch_required agent="ring:backend-engineer-golang">
Do not proceed with edits until user approves.
</dispatch_required>

Present the full plan using AskUserQuestion:
```
Options:
  1. Apply all migrations as planned
  2. Dry run — show diffs without writing
  3. Select specific packages only
```

If dry_run=true from input, skip this step and show diffs only.

---

## Step 4: Add lib-observability to go.mod

```bash
# lib-observability may not yet be indexed by the Go sum database.
# Always use GONOSUMDB + GOPRIVATE to avoid sum.golang.org 404 errors.
GONOSUMDB="github.com/LerianStudio/lib-observability" \
GOPRIVATE="github.com/LerianStudio/lib-observability" \
  go get github.com/LerianStudio/lib-observability@v1.0.0-beta.3
# Use the version that matches the lib-commons delegation shims.
# Check the lib-commons release notes or go.mod require block for the minimum
# compatible version. v1.0.0-beta.3 is the baseline for the current shims.
```

Verify it appears in go.mod:
```bash
grep "lib-observability" go.mod
# Expected: github.com/LerianStudio/lib-observability v1.0.0-beta.3
# Note: the entry may be marked "// indirect" at this stage — import paths have
# not been updated yet (that happens in Step 5). The "// indirect" marker is
# removed after Step 5 (import replacements) and Step 6 (go mod tidy).
```

---

## Step 5: Apply Import Replacements

<dispatch_required agent="ring:backend-engineer-golang">
For each file identified in Step 2:
1. Read the file
2. Replace the import path using the mapping table
3. Preserve any import aliases the file was using
4. No package qualifier changes needed for the same-name package replacements
   (log stays log, assert stays assert, metrics stays metrics, etc.)
5. For root commons/opentelemetry, migrate helper-only files first. Preserve
   explicit aliases. If the import was unaliased, rewrite `opentelemetry.`
   call sites to `tracing.`. For bootstrap/type-bearing files, migrate only
   after confirming the `Telemetry` value does not cross a remaining
   lib-commons API boundary; otherwise leave that file unchanged and report it.
6. For commons/net/http middleware symbols, rewrite only deprecated observability call sites
   to the lib-observability/middleware import alias. Preserve the lib-commons HTTP
   import when the file still uses non-observability HTTP helpers.
7. For root commons observability context helpers, rewrite only deprecated
   observability call sites to the lib-observability import alias. Preserve the
   lib-commons root import when the file still uses non-observability commons helpers.
8. Write the updated file
</dispatch_required>

---

## Step 6: Run go mod tidy

```bash
GONOSUMDB="github.com/LerianStudio/lib-observability" \
GOPRIVATE="github.com/LerianStudio/lib-observability" \
  go mod tidy
```

Check that lib-commons is still present if the app uses non-deprecated packages:
```bash
grep "lib-commons" go.mod
# Should still be there unless the app used ONLY deprecated packages
```

---

## Step 7: Validate Build and Tests

```bash
go build ./...
go vet ./...
go test ./...
```

<block_condition>
- `go build ./...`, `go vet ./...`, or `go test ./...` exits non-zero
</block_condition>

If build fails:
1. Read each compilation error
2. Since the package-level replacements share the same qualifier, errors are unlikely — check for:
   - Indirect API differences between shim and lib-observability (rare)
   - Missing symbols that the shim exposed but lib-observability doesn't (report as PARTIAL)
3. Fix compilation errors
4. Re-run until `go build ./...` passes

---

## Step 8: Verify No Remaining Deprecated Imports

```bash
grep -r "lib-commons/v5/commons/log\"" . --include="*.go" | wc -l
grep -r "lib-commons/v5/commons/zap\"" . --include="*.go" | wc -l
grep -r "lib-commons/v5/commons/runtime\"" . --include="*.go" | wc -l
grep -r "lib-commons/v5/commons/assert\"" . --include="*.go" | wc -l
grep -r "lib-commons/v5/commons/opentelemetry/metrics\"" . --include="*.go" | wc -l
grep -r "lib-commons/v5/commons/opentelemetry/constants\"" . --include="*.go" | wc -l
grep -r "lib-commons/v5/commons/opentelemetry/redaction\"" . --include="*.go" | wc -l
```

Each should print `0`.

For root `commons/opentelemetry`, helper-only imports should be gone. Remaining
imports are acceptable only when they are bootstrap/type-bearing files blocked
by a remaining lib-commons API boundary. Report each remaining file and why it
was kept:

```bash
grep -r "lib-commons/v5/commons/opentelemetry\"" . --include="*.go"
```

For `commons/net/http`, do not require the import count to be zero. Instead,
verify no deprecated observability middleware symbols remain qualified by the lib-commons HTTP
alias:

```bash
# Replace libHTTP with the alias discovered in each file, commonly http or libHTTP.
grep -rE 'libHTTP\\.(RequestInfo|ResponseMetricsWrapper|NewRequestInfo|LogMiddlewareOption|WithCustomLogger|WithObfuscationDisabled|WithHTTPLogging|WithGrpcLogging|DefaultMetricsCollectionInterval|TelemetryMiddleware|NewTelemetryMiddleware|WithTelemetry|EndTracingSpans|WithTelemetryInterceptor|EndTracingSpansInterceptor|StopMetricsCollector)' . --include="*.go" | wc -l
grep -rE 'http\\.(RequestInfo|ResponseMetricsWrapper|NewRequestInfo|LogMiddlewareOption|WithCustomLogger|WithObfuscationDisabled|WithHTTPLogging|WithGrpcLogging|DefaultMetricsCollectionInterval|TelemetryMiddleware|NewTelemetryMiddleware|WithTelemetry|EndTracingSpans|WithTelemetryInterceptor|EndTracingSpansInterceptor|StopMetricsCollector)' . --include="*.go" | wc -l
```

Both checks should print `0` for aliases actually used by the target repo.

For root `commons`, do not require the import count to be zero. Instead, verify
no deprecated observability context helper symbols remain qualified by the
lib-commons alias:

```bash
# Replace commons/libCommons with aliases discovered in each file.
grep -rE 'commons\\.(NewLoggerFromContext|ContextWithLogger|ContextWithTracer|ContextWithMetricFactory|ContextWithHeaderID|TrackingComponents|NewTrackingFromContext|ContextWithSpanAttributes|AttributesFromContext|ReplaceAttributes)' . --include="*.go" | wc -l
grep -rE 'libCommons\\.(NewLoggerFromContext|ContextWithLogger|ContextWithTracer|ContextWithMetricFactory|ContextWithHeaderID|TrackingComponents|NewTrackingFromContext|ContextWithSpanAttributes|AttributesFromContext|ReplaceAttributes)' . --include="*.go" | wc -l
```

---

## Step 9: Produce Final Report

```markdown
## Changes Applied

| File | Imports Replaced | Before | After |
|------|-----------------|--------|-------|
| cmd/main.go | 2 | commons/log, commons/runtime | log, runtime |
| ...

## Validation

| Check | Result |
|-------|--------|
| go build ./... | ✅ PASS |
| go vet ./... | ✅ PASS |
| go test ./... | ✅ PASS |
| No remaining deprecated lib-commons observability imports | ✅ PASS |

## Summary

- Files changed: X
- Imports replaced: Y
- Build status: PASS
- Result: PASS
```

---

## Severity Calibration

| Severity | Criteria |
|----------|----------|
| CRITICAL | Build fails after migration and cannot be fixed by import path changes alone |
| HIGH | Symbol exists in lib-commons shim but is missing from lib-observability |
| MEDIUM | Import alias collision requiring manual rename |
| LOW | Unused import warning after migration |

---

## Pressure Resistance

| Pushback | Response |
|---|---|
| "Only one or two deprecated imports, not worth the effort" | Deprecation warnings accumulate. Migrate now to keep the codebase clean. |
| "lib-commons shims still work, why change?" | They are deprecated and will be removed in a future major. Earlier migration = smaller blast radius. |
| "commons/opentelemetry is similar, migrate it too" | Migrate it only when the effective lib-commons package is marked `Deprecated:` and `lib-observability/tracing` exposes the required API. Preserve explicit aliases; rewrite unaliased `opentelemetry.` qualifiers to `tracing.`. |
| "What about commons/net/http telemetry middleware?" | If it is marked deprecated in lib-commons and exists in lib-observability/middleware, it migrates. Otherwise the skill skips it and reports the missing gate. |
| "Streaming imports will break" | commons/streaming is NOT deprecated. The skill explicitly skips it. |
| "The import paths are simple, just replace them regardless of lib-commons version" | CANNOT proceed. Without the delegation shims, commons/log.Logger and lib-observability/log.Logger are distinct named types. Every lib-commons boundary (NewTrackingFromContext, mongo.Config.Logger, etc.) returns the old type. Replacing import paths causes compile errors at all those boundaries. Upgrade lib-commons first. |

---

## Anti-Rationalization Table

| Rationalization | Why Wrong | Action |
|---|---|---|
| "I'll also replace commons/opentelemetry while I'm at it" | Root `commons/opentelemetry` is allowed only through the same double gate: source `Deprecated:` plus target API exists in `lib-observability/tracing`. | Run the gate checks first. If either gate fails, leave it unchanged and report the block. |
| "The tests pass even with mixed imports" | Deprecated imports create future breakage risk | Replace all deprecated observability packages and deprecated HTTP/gRPC middleware symbols that pass both gates |
| "I'll do it later when lib-commons removes the shims" | Migration is harder with more files in flight | Migrate now, reduce future blast radius |
| "go get failed — the module must not be public" | The sum DB may not have indexed it yet | Use GONOSUMDB + GOPRIVATE as shown in Step 4 |
| "The import path is the only thing changing, types are compatible" | Only true AFTER lib-commons is on a version with delegation shims. On older versions, commons/log.Logger and lib-observability/log.Logger are distinct named types — not aliases. Compile errors will occur at every lib-commons boundary. | STOP. Run the Step 1 shim check first. If it fails, upgrade lib-commons before running this skill. |
| "I can fix the type errors after replacing imports" | The type errors are systemic — they appear at every lib-commons API boundary (NewTrackingFromContext, infrastructure Config.Logger fields, etc.). Fixing them ad-hoc defeats the purpose of the skill and risks introducing bugs. | STOP. Upgrade lib-commons to a shim-enabled version first. |
