## Observability

| Component | Primary | Alternatives |
|-----------|---------|--------------|
| Logs | Loki | ELK Stack, Splunk, CloudWatch Logs |
| Traces | Jaeger/Tempo | Zipkin, X-Ray, Honeycomb |
| APM | OpenTelemetry | DataDog APM, New Relic APM |

---

## Logging

### Structured Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "error",
  "logger": "api.handler",
  "message": "Failed to process request",
  "service": "api",
  "version": "1.2.3",
  "environment": "production",
  "trace_id": "abc123def456",
  "span_id": "789xyz",
  "request_id": "req-001",
  "user_id": "usr_456",
  "error": {
    "type": "ConnectionError",
    "message": "connection timeout after 30s",
    "stack": "..."
  },
  "context": {
    "method": "POST",
    "path": "/api/v1/users",
    "status": 500,
    "duration_ms": 30045
  }
}
```

### Log Levels

| Level | Usage | Examples |
|-------|-------|----------|
| **ERROR** | Failures requiring attention | Database connection failed, API error |
| **WARN** | Potential issues | Retry attempt, connection pool low |
| **INFO** | Normal operations | Request completed, user logged in |
| **DEBUG** | Detailed debugging | Query parameters, internal state |
| **TRACE** | Very detailed (rarely used) | Full request/response bodies |

### What to Log

```yaml
# DO log
- Request start/end with duration
- Error details with stack traces
- Authentication events (login, logout, failed attempts)
- Authorization failures
- External service calls (start, end, duration)
- Business events (order placed, payment processed)
- Configuration changes
- Deployment events

# DO not log
- Passwords or API keys
- Credit card numbers (full)
- Personal identifiable information (PII)
- Session tokens
- Internal security mechanisms
- Health check requests (too noisy)
```

### Log Aggregation (Loki)

```yaml
# loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

---

