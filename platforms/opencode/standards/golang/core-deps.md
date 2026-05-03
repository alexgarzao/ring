## Core Dependency: lib-commons (MANDATORY)

All Lerian Studio Go projects **MUST** use the latest v5.x release of `lib-commons/v5` as the foundation library. This ensures consistency across all services. Resolve the actual latest tag using `gh api repos/LerianStudio/lib-commons/releases/latest --jq '.tag_name'` instead of hardcoding specific patch versions.

### Required Import (lib-commons v5)

```go
import (
    libCommons "github.com/LerianStudio/lib-commons/v5/commons"
    clog "github.com/LerianStudio/lib-commons/v5/commons/log"
    czap "github.com/LerianStudio/lib-commons/v5/commons/zap"
    cassert "github.com/LerianStudio/lib-commons/v5/commons/assert"
    cruntime "github.com/LerianStudio/lib-commons/v5/commons/runtime"
    cotel "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry"
    cmetrics "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry/metrics"
    chttp "github.com/LerianStudio/lib-commons/v5/commons/net/http"
    cpostgres "github.com/LerianStudio/lib-commons/v5/commons/postgres"
    cmongo "github.com/LerianStudio/lib-commons/v5/commons/mongo"
    credis "github.com/LerianStudio/lib-commons/v5/commons/redis"
)
```

> **Note:** v5 uses `c` prefix aliases (e.g., `clog`, `czap`, `cotel`) except for the root commons package which uses `libCommons`. This distinguishes lib-commons packages from standard library and other imports.

### What lib-commons v5 Provides

| Package | Alias | Purpose | Where Used |
|---------|-------|---------|------------|
| `commons` | `libCommons` | Config loading (`InitLocalEnvConfig`), UUID validation, safe math | Bootstrap, utilities |
| `commons/log` | `clog` | Logger interface, Level types, Field constructors | **Everywhere** |
| `commons/zap` | `czap` | Logger initialization/configuration | **Bootstrap only** |
| `commons/assert` | `cassert` | Domain validation (returns errors, NEVER panics) | Domain, config validation |
| `commons/runtime` | `cruntime` | Safe goroutine management with panic recovery | Bootstrap, workers, services |
| `commons/opentelemetry` | `cotel` | OpenTelemetry initialization, tracing | Bootstrap, middleware |
| `commons/opentelemetry/metrics` | `cmetrics` | Typed metric definitions (Counter, Histogram) | Telemetry, services |
| `commons/net/http` | `chttp` | HTTP telemetry middleware, pagination, responses | Routes, handlers |
| `commons/postgres` | `cpostgres` | PostgreSQL connection with migrations and replicas | Bootstrap, repositories |
| `commons/mongo` | `cmongo` | MongoDB connection with lazy-connect | Bootstrap, repositories |
| `commons/redis` | `credis` | Redis connection (standalone, sentinel, cluster) | Bootstrap, cache |
| `commons/rabbitmq` | `crabbitmq` | RabbitMQ connection with SSRF protection | Bootstrap, producers/consumers |
| `commons/crypto` | `ccrypto` | AES-GCM encryption, HMAC-SHA256 hashing | Sensitive data storage |
| `commons/safe` | `csafe` | Safe decimal math (no panic on zero division) | Financial calculations |
| `commons/backoff` | `cbackoff` | Exponential backoff with jitter | Retry logic |
| `commons/pointers` | `cpointers` | Pointer helper functions (`String()`, `Bool()`, etc.) | DTOs, optional fields |
| `commons/security` | `csecurity` | Sensitive field detection and obfuscation | Logging, auditing |
| `commons/outbox` | `coutbox` | Outbox pattern for reliable event publishing | Event-driven services |
| `commons/secretsmanager` | `csm` | AWS Secrets Manager for M2M credentials | Plugin multi-tenant |
| `commons/circuitbreaker` | `ccb` | Circuit breaker with health checks | External service calls |
| `commons/constants` | `cconst` | Standard HTTP headers, error codes, pagination defaults | Utilities |
| `commons/dispatch layer` | — | Multi-tenant middleware, DB routing, Redis key prefixing | See multi-tenant.md |

> **⛔ Version Gate:** Verify the project's `go.mod` declares `lib-commons/v5`. If the project uses v2, v3, or v4, it is below the current standard and must be migrated. Check with: `grep 'lib-commons' go.mod`

---

