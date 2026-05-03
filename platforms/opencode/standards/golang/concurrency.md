## Concurrency Patterns

### Goroutines with Context

```go
func processItems(ctx context.Context, items []Item) error {
    g, ctx := errgroup.WithContext(ctx)

    for _, item := range items {
        item := item // capture variable
        g.Go(func() error {
            select {
            case <-ctx.Done():
                return ctx.Err()
            default:
                return processItem(ctx, item)
            }
        })
    }

    return g.Wait()
}
```

> **When to use `errgroup` vs `cruntime`:**
> - **`errgroup.WithContext`**: Bounded concurrent operations within a single function scope (e.g., parallel processing of a batch). Short-lived, exits when all tasks complete.
> - **`cruntime.SafeGoWithContextAndComponent`**: Long-lived goroutines (HTTP servers, consumers, background polling, cache cleanup). Has panic recovery, crash policies, and observability.
> - The FORBIDDEN rule for raw `go func(){}()` applies to ALL production goroutines outside of errgroup.

### Channel Patterns

```go
// Worker pool
func workerPool(ctx context.Context, jobs <-chan Job, results chan<- Result) {
    for {
        select {
        case <-ctx.Done():
            return
        case job, ok := <-jobs:
            if !ok {
                return
            }
            results <- process(job)
        }
    }
}
```

---

