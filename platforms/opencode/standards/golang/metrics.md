## Typed Metrics (cmetrics)

Custom metrics **MUST** use `cmetrics` for typed metric definitions.

### Metric Definitions

```go
// Define metrics as package-level variables
var metricOperationTotal = cmetrics.Metric{
    Name:        "svc.operation.total",
    Unit:        "1",
    Description: "Total operations by outcome.",
}

var metricOperationLatency = cmetrics.Metric{
    Name:        "svc.operation.latency",
    Unit:        "ms",
    Description: "Operation latency in milliseconds.",
    Buckets:     []float64{10, 50, 100, 250, 500, 1000, 2500, 5000},
}
```

### Usage via MetricsFactory

```go
factory, err := cmetrics.NewMetricsFactory(meter, logger)

counter, err := factory.Counter(metricOperationTotal)
_ = counter.WithLabels(map[string]string{"outcome": "success"}).AddOne(ctx)

histogram, err := factory.Histogram(metricOperationLatency)
_ = histogram.WithLabels(map[string]string{"system": "db"}).Record(ctx, durationMs)
```

### Naming Convention

`{service-prefix}.{subsystem}.{metric_name}`

---

