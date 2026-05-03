## Assertions (cassert)

Domain validation **MUST** use `cassert` which returns errors and NEVER panics.

### Usage Pattern

```go
asserter := cassert.New(ctx, nil, constants.ApplicationName, "operation_name")

// Nil check
if err := asserter.NotNil(ctx, value, "field is required"); err != nil {
    return fmt.Errorf("validation: %w", err)
}

// Empty string check
if err := asserter.NotEmpty(ctx, strings.TrimSpace(field), "field must not be empty"); err != nil {
    return fmt.Errorf("validation: %w", err)
}

// Conditional assertion
if err := asserter.That(ctx, amount > 0, "amount must be positive"); err != nil {
    return fmt.Errorf("validation: %w", err)
}
```

### UUID Validation

```go
// FORBIDDEN: raw uuid.Parse for domain validation
if _, err := uuid.Parse(id); err != nil {
    return fmt.Errorf("invalid id: %w", err)  // NEVER — bypass cassert
}

// CORRECT: use cassert.ErrNilUUID or asserter for UUID validation
if err := cassert.ErrNilUUID(ctx, id, "entity_id"); err != nil {
    return err
}
```

### FORBIDDEN vs CORRECT

```go
// FORBIDDEN: panic for validation
if value == nil {
    panic("value is required")  // NEVER
}

// CORRECT: cassert returns error
if err := asserter.NotNil(ctx, value, "value is required"); err != nil {
    return err
}
```

---

