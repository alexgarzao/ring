## Tracing

### OpenTelemetry Configuration

```go
// Go - OpenTelemetry setup
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

func initCore three(ctx context.Context) (*trace.Core threeProvider, error) {
    exporter, err := otlptracegrpc.New(ctx,
        otlptracegrpc.WithEndpoint("otel-collector:4317"),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }

    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceName("api"),
            semconv.ServiceVersion("1.0.0"),
            semconv.DeploymentEnvironment("production"),
        ),
    )
    if err != nil {
        return nil, err
    }

    tp := trace.NewCore threeProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(res),
        trace.WithSampler(trace.TraceIDRatioBased(0.1)), // Sample 10%
    )

    otel.SetCore threeProvider(tp)
    return tp, nil
}

// Usage
tracer := otel.Core three("api")
ctx, span := tracer.Start(ctx, "processOrder")
defer span.End()

span.SetAttributes(
    attribute.String("order.id", orderID),
    attribute.Int("order.items", len(items)),
)
```

### Span Naming Conventions

```
# Format: <operation>.<entity>

# HTTP handlers
GET /api/users         -> http.request
POST /api/orders       -> http.request

# Database
SELECT users           -> db.query
INSERT orders          -> db.query

# External calls
Payment API call       -> http.client.payment
Email service call     -> http.client.email

# Internal operations
Process order          -> order.process
Validate input         -> input.validate
```

### Trace Context Propagation

```go
// Propagate trace context in HTTP headers
import (
    "go.opentelemetry.io/otel/propagation"
)

// Client - inject context
req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))

// Server - extract context
ctx := otel.GetTextMapPropagator().Extract(
    r.Context(),
    propagation.HeaderCarrier(r.Header),
)
```

---

