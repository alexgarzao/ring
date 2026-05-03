## Outbox Pattern (commons/outbox)

Event-driven services **MUST** use the outbox pattern via `coutbox` for reliable event publishing.

```go
// Reliable event publishing via database-backed outbox
// Prevents message loss when broker is unavailable
outboxRepo := coutbox.NewPostgresRepository(db, coutbox.Config{
    SchemaName: "public",
    TableName:  "outbox_events",
})

event := coutbox.Event{
    AggregateType: "transfer",
    AggregateID:   transferID,
    EventType:     "transfer.completed",
    Payload:       payload,
}

if err := outboxRepo.Store(ctx, event); err != nil {
    return err
}
// Dispatcher polls outbox table and publishes to broker
```

---

