## Frameworks & Libraries

### Required Versions (Minimum)

| Library | Minimum Version | Purpose |
|---------|-----------------|---------|
| `lib-commons` | latest v5.x (resolve via `gh api repos/LerianStudio/lib-commons/releases/latest --jq .tag_name`) | Core infrastructure |
| `fiber/v2` | v2.52.0 | HTTP framework |
| `pgx/v5` | v5.7.0 | PostgreSQL driver |
| `go.opentelemetry.io/otel` | v1.42.0 | Telemetry |
| `testify` | v1.11.0 | Testing |
| `go-sqlmock` | v1.5.0 | Database mocking |
| `testcontainers-go` | v0.40.0 | Integration tests |
| `shopspring/decimal` | v1.4.0 | Monetary precision |
| `sony/gobreaker/v2` | v2.4.0 | Circuit breaker (direct use) |

### HTTP Framework

| Library | Use Case |
|---------|----------|
| **Fiber v2** | **Primary choice** - High-performance APIs |
| gRPC-Go | Service-to-service communication |

### Database

| Library | Use Case |
|---------|----------|
| **pgx/v5** | PostgreSQL (recommended) |
| sqlc | Type-safe SQL queries |
| GORM | ORM (when needed) |
| **go-redis/v9** | Redis client |
| **mongo-go-driver** | MongoDB |

### Testing

| Library | Use Case |
|---------|----------|
| testify | Assertions |
| GoMock | Interface mocking (MANDATORY for all mocks) |
| SQLMock | Database mocking |
| testcontainers-go | Integration tests |

---

