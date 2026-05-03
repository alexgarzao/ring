## Backoff (commons/backoff)

Retry logic **MUST** use `cbackoff` for exponential backoff with jitter.

```go
// Exponential backoff with jitter for retries
delay := cbackoff.Exponential(attempt, baseDelay, maxDelay)
jitteredDelay := cbackoff.FullJitter(delay)
```

---

